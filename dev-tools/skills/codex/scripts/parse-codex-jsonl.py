#!/usr/bin/env python3
"""Parse codex JSONL output from stdin to human-readable format.

Usage:
  codex exec ... --json 2>/dev/null | python3 <skill-dir>/scripts/parse-codex-jsonl.py
  codex exec ... --json 2>err.txt | python3 <skill-dir>/scripts/parse-codex-jsonl.py --session
"""
import sys
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--session', action='store_true',
                    help='Extract SESSION_ID from thread.started events')
args = parser.parse_args()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
        t = obj.get('type', '')
        if args.session and t == 'thread.started':
            tid = obj.get('thread_id', '')
            if tid:
                print(f'SESSION_ID:{tid}')
        elif t == 'item.completed' and 'item' in obj:
            item = obj['item']
            itype = item.get('type', '')
            text = item.get('text', '')
            if itype == 'reasoning' and text:
                print(f'[codex thinking] {text}')
                print()
            elif itype == 'agent_message' and text:
                print(text)
            elif itype == 'command_execution':
                cmd = item.get('command', '')
                if cmd:
                    print(f'[codex ran] {cmd}')
        elif t == 'turn.completed':
            usage = obj.get('usage', {})
            tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
            if tokens:
                print(f'\ntokens used: {tokens}')
    except Exception:
        pass
