#!/usr/bin/env bash
set -euo pipefail
rm -rf data/chroma
python scripts/build_index.py
