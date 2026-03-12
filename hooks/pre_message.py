#!/usr/bin/env python3
import sys, json
def main():
    message = sys.stdin.read()
    triggers = {
        '多专家讨论': {'signal': 10, 'action': 'force_multi_agent'},
        '这很重要': {'signal': 9, 'action': 'smart_ingest_priority'},
        '记住这个': {'signal': 8, 'action': 'smart_ingest'},
        '别忘记': {'signal': 7, 'action': 'create_reminder'},
    }
    for trigger, cfg in triggers.items():
        if trigger in message:
            print(json.dumps({'triggered': True, 'trigger': trigger, **cfg}))
            return
    print(json.dumps({'triggered': False}))
if __name__ == '__main__': main()
