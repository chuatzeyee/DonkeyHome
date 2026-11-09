#!/usr/bin/env bash
# Starts the Home Assistant starter wizard (Mac and Linux).
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  python3 wizard/wizard.py "$@"
else
  echo "Python 3 is needed. Mac: install it from https://www.python.org/downloads/  Linux: sudo apt install python3"
  exit 1
fi
