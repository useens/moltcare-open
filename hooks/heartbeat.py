#!/usr/bin/env python3
import json
from datetime import datetime
def main():
    print(json.dumps({'timestamp': str(datetime.now()), 'status': 'ok'}))
if __name__ == '__main__': main()
