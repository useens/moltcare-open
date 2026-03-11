/**
 * Error Handler Tests
 */

import { describe, it, expect } from 'vitest';
import { ErrorHandler, ErrorCodes } from '../src/utils/errors.js';
import type { MoltCareError } from '../src/utils/errors.js';

describe('ErrorHandler', () => {
  describe('formatError', () => {
    it('should format string errors', () => {
      const output = ErrorHandler.formatError('Simple error message');
      expect(output).toContain('Simple error message');
      expect(output).toContain('UNKNOWN');
    });

    it('should format Error objects', () => {
      const error = new Error('Test error');
      const output = ErrorHandler.formatError(error);
      expect(output).toContain('Test error');
      expect(output).toContain('ERROR');
    });

    it('should format MoltCareError objects', () => {
      const error: MoltCareError = {
        code: 'TEST_ERROR',
        message: 'Test message',
        suggestion: 'Do this to fix',
      };
      const output = ErrorHandler.formatError(error);
      expect(output).toContain('[TEST_ERROR]');
      expect(output).toContain('Test message');
      expect(output).toContain('Do this to fix');
    });

    it('should include details when provided', () => {
      const error: MoltCareError = {
        code: 'TEST',
        message: 'Test',
        details: ['Detail 1', 'Detail 2'],
      };
      const output = ErrorHandler.formatError(error);
      expect(output).toContain('Detail 1');
      expect(output).toContain('Detail 2');
    });

    it('should include didYouMean suggestions', () => {
      const error: MoltCareError = {
        code: 'TEST',
        message: 'Test',
        didYouMean: ['option1', 'option2'],
      };
      const output = ErrorHandler.formatError(error);
      expect(output).toContain('您是否想查找');
      expect(output).toContain('option1');
      expect(output).toContain('option2');
    });
  });

  describe('findSimilar', () => {
    it('should find similar strings', () => {
      const candidates = ['foundation', 'foundations', 'found', 'something-else'];
      const similar = ErrorHandler.findSimilar('foundation', candidates);
      
      expect(similar.length).toBeGreaterThan(0);
      expect(similar).toContain('foundation');
    });

    it('should return empty for no matches', () => {
      const candidates = ['completely', 'different', 'words'];
      const similar = ErrorHandler.findSimilar('xyz', candidates);
      
      expect(similar).toEqual([]);
    });

    it('should respect limit parameter', () => {
      const candidates = ['a', 'aa', 'aaa', 'aaaa', 'aaaaa'];
      const similar = ErrorHandler.findSimilar('a', candidates, 2);
      
      expect(similar.length).toBeLessThanOrEqual(2);
    });

    it('should be case insensitive', () => {
      const candidates = ['Foundation', 'FOUNDATION'];
      const similar = ErrorHandler.findSimilar('foundation', candidates);
      
      expect(similar.length).toBeGreaterThan(0);
    });

    it('should handle empty input', () => {
      expect(ErrorHandler.findSimilar('', ['test'])).toEqual([]);
      expect(ErrorHandler.findSimilar('test', [])).toEqual([]);
    });
  });

  describe('predefined errors', () => {
    it('should create packNotFound error', () => {
      const error = ErrorHandler.packNotFound('mypack', ['foundation', 'other']);
      
      expect(error.code).toBe(ErrorCodes.PACK_NOT_FOUND);
      expect(error.message).toContain('mypack');
      expect(error.suggestion).toBeTruthy();
      expect(error.didYouMean).toBeDefined();
    });

    it('should create packAlreadyInstalled error', () => {
      const error = ErrorHandler.packAlreadyInstalled('foundation');
      
      expect(error.code).toBe(ErrorCodes.PACK_ALREADY_INSTALLED);
      expect(error.message).toContain('foundation');
      expect(error.suggestion).toContain('--force');
    });

    it('should create invalidPackName error', () => {
      const error = ErrorHandler.invalidPackName('bad/name', 'contains slash');
      
      expect(error.code).toBe(ErrorCodes.INVALID_PACK_NAME);
      expect(error.message).toContain('bad/name');
      expect(error.details).toContain('contains slash');
    });

    it('should create configNotFound error', () => {
      const error = ErrorHandler.configNotFound();
      
      expect(error.code).toBe(ErrorCodes.CONFIG_NOT_FOUND);
      expect(error.suggestion).toContain('init');
    });

    it('should create openClawNotFound error', () => {
      const error = ErrorHandler.openClawNotFound();
      
      expect(error.code).toBe(ErrorCodes.OPENCLAW_NOT_FOUND);
      expect(error.details).toBeDefined();
      expect(error.details!.length).toBeGreaterThan(0);
    });

    it('should create templateRenderFailed error', () => {
      const error = ErrorHandler.templateRenderFailed('template.md', 'parse error');
      
      expect(error.code).toBe(ErrorCodes.TEMPLATE_RENDER_FAILED);
      expect(error.message).toContain('template.md');
      expect(error.details).toContain('parse error');
    });

    it('should create fileWriteFailed error', () => {
      const error = ErrorHandler.fileWriteFailed('output.txt', 'permission denied');
      
      expect(error.code).toBe(ErrorCodes.FILE_WRITE_FAILED);
      expect(error.message).toContain('output.txt');
      expect(error.details).toContain('permission denied');
    });
  });

  describe('ErrorCodes constants', () => {
    it('should have all error codes defined', () => {
      expect(ErrorCodes.PACK_NOT_FOUND).toBe('PACK_NOT_FOUND');
      expect(ErrorCodes.PACK_ALREADY_INSTALLED).toBe('PACK_ALREADY_INSTALLED');
      expect(ErrorCodes.INVALID_PACK_NAME).toBe('INVALID_PACK_NAME');
      expect(ErrorCodes.CONFIG_NOT_FOUND).toBe('CONFIG_NOT_FOUND');
      expect(ErrorCodes.OPENCLAW_NOT_FOUND).toBe('OPENCLAW_NOT_FOUND');
      expect(ErrorCodes.TEMPLATE_RENDER_FAILED).toBe('TEMPLATE_RENDER_FAILED');
      expect(ErrorCodes.FILE_WRITE_FAILED).toBe('FILE_WRITE_FAILED');
    });
  });
});
