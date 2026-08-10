#!/usr/bin/env bash
set -euo pipefail

if ! command -v anvil >/dev/null 2>&1; then
  echo "anvil is not installed"
  exit 1
fi

anvil --host 127.0.0.1 --port 8545
