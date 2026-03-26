#!/usr/bin/env bash
# 在 Linux VPS 上安装依赖并前台试运行服务端（需已上传 vpn-proxy-client 目录）
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"
python3 -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -U pip
pip install -r server/requirements.txt
echo "启动: python server/run.py"
exec python server/run.py
