#!/usr/bin/env python3
"""
Local speech-to-text using OpenAI Whisper (Optimized v2.0)
Features: Model caching, Queue management, Async processing
"""

import json
import sys
import warnings
import threading
import queue
import time
from pathlib import Path
from functools import lru_cache

import click

warnings.filterwarnings("ignore")

MODELS = ["tiny", "tiny.en", "base", "base.en", "small", "small.en",
          "medium", "medium.en", "large-v3", "turbo"]

# Global state
_model_cache = {}
_model_lock = threading.Lock()
_transcription_queue = queue.Queue()
_worker_thread = None
_results_cache = {}


def get_cached_model(model_name):
    """Get cached Whisper model (thread-safe)."""
    global _model_cache
    
    with _model_lock:
        if model_name not in _model_cache:
            import whisper
            _model_cache[model_name] = whisper.load_model(model_name)
        return _model_cache[model_name]


def transcribe_audio(audio_file, model_name, language=None, timestamps=False, quiet=False):
    """Transcribe audio file using cached model."""
    try:
        whisper_model = get_cached_model(model_name)
    except Exception as e:
        return {"error": f"Error loading model: {e}"}

    try:
        result = whisper_model.transcribe(
            audio_file, 
            language=language,
            word_timestamps=timestamps, 
            verbose=False
        )
        return result
    except Exception as e:
        return {"error": f"Error transcribing: {e}"}


def process_queue():
    """Background worker to process transcription queue."""
    global _results_cache
    
    while True:
        try:
            task = _transcription_queue.get(timeout=1)
            if task is None:  # Shutdown signal
                break
            
            task_id, audio_file, model, language, timestamps, quiet = task
            
            if not quiet:
                print(f"[Queue] Processing: {Path(audio_file).name}", file=sys.stderr)
            
            result = transcribe_audio(audio_file, model, language, timestamps, quiet)
            _results_cache[task_id] = result
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[Queue] Error: {e}", file=sys.stderr)


def start_worker():
    """Start background worker thread."""
    global _worker_thread
    if _worker_thread is None or not _worker_thread.is_alive():
        _worker_thread = threading.Thread(target=process_queue, daemon=True)
        _worker_thread.start()
        print("[System] Background worker started", file=sys.stderr)


def transcribe_async(audio_file, model, language, timestamps, quiet):
    """Add transcription task to queue and return task ID."""
    import uuid
    task_id = str(uuid.uuid4())[:8]
    
    start_worker()
    _transcription_queue.put((task_id, audio_file, model, language, timestamps, quiet))
    
    return task_id


def wait_for_result(task_id, timeout=60):
    """Wait for async transcription result."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if task_id in _results_cache:
            return _results_cache.pop(task_id)
        time.sleep(0.1)
    return {"error": "Timeout waiting for result"}


@click.command()
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("-m", "--model", default="base", type=click.Choice(MODELS), help="Whisper model size")
@click.option("-l", "--language", default=None, help="Language code (auto-detect if omitted)")
@click.option("-t", "--timestamps", is_flag=True, help="Include word-level timestamps")
@click.option("-j", "--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("-q", "--quiet", is_flag=True, help="Suppress progress messages")
@click.option("--async", "async_mode", is_flag=True, help="Async mode (returns task ID)")
@click.option("--wait", is_flag=True, help="Wait for async result")
@click.option("--task-id", help="Task ID to check result")
@click.option("--benchmark", is_flag=True, help="Show performance metrics")
def main(audio_file, model, language, timestamps, as_json, quiet, async_mode, wait, task_id, benchmark):
    """Transcribe audio using OpenAI Whisper (optimized v2.0)."""
    
    # Preload model on first run
    if not _model_cache and not quiet:
        click.echo("[System] Initializing model cache...", err=True)
    
    start_time = time.time()
    
    # Check result mode
    if task_id:
        if task_id in _results_cache:
            result = _results_cache.pop(task_id)
        else:
            result = {"error": "Task not found or still processing"}
        
        if "error" in result:
            click.echo(result["error"], err=True)
            sys.exit(1)
        
        text = result.get("text", "").strip()
        click.echo(text)
        return
    
    # Async mode
    if async_mode:
        task_id = transcribe_async(audio_file, model, language, timestamps, quiet)
        if wait:
            if not quiet:
                click.echo(f"[Async] Task {task_id} started, waiting...", err=True)
            result = wait_for_result(task_id)
            if "error" in result:
                click.echo(result["error"], err=True)
                sys.exit(1)
        else:
            click.echo(json.dumps({"task_id": task_id, "status": "queued"}))
            return
    else:
        # Sync mode (default)
        if not quiet:
            click.echo(f"[System] Using cached model: {model}", err=True)
        
        result = transcribe_audio(audio_file, model, language, timestamps, quiet)
        
        if "error" in result:
            click.echo(result["error"], err=True)
            sys.exit(1)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    text = result.get("text", "").strip()
    
    if as_json:
        output = {
            "text": text, 
            "language": result.get("language", "unknown"),
            "processing_time": round(processing_time, 2)
        }
        if benchmark:
            output["benchmark"] = {
                "model_cached": model in _model_cache,
                "queue_size": _transcription_queue.qsize(),
                "worker_alive": _worker_thread is not None and _worker_thread.is_alive()
            }
        if timestamps and "segments" in result:
            output["segments"] = [
                {"start": s["start"], "end": s["end"], "text": s["text"],
                 **({"words": s["words"]} if "words" in s else {})}
                for s in result["segments"]
            ]
        click.echo(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        click.echo(text)
        if timestamps and "segments" in result:
            click.echo("\n--- Segments ---", err=True)
            for seg in result["segments"]:
                click.echo(f"  [{seg['start']:.2f}s - {seg['end']:.2f}s]: {seg['text']}", err=True)
        
        if benchmark:
            click.echo(f"\n[Benchmark] Processing time: {processing_time:.2f}s", err=True)
            click.echo(f"[Benchmark] Model cached: {model in _model_cache}", err=True)


if __name__ == "__main__":
    main()
