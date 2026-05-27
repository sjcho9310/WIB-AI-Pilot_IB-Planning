#!/usr/bin/env bash
# VS Code 터미널 시작 시 자동으로 Streamlit venv 활성화
# (terminal.integrated.profiles 에서 --init-file 로 호출됨)

# 기본 bashrc 먼저 로드
[ -f /etc/bash.bashrc ] && source /etc/bash.bashrc
[ -f "$HOME/.bashrc" ] && source "$HOME/.bashrc"

# 이 스크립트 위치 기준으로 워크스페이스 루트 결정 (PWD 의존 제거)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_ACTIVATE="${WORKSPACE_ROOT}/streamlit-app/.venv/bin/activate"

if [ -f "$VENV_ACTIVATE" ]; then
  # shellcheck disable=SC1090
  source "$VENV_ACTIVATE"
  echo "(.venv) activated: ${WORKSPACE_ROOT}/streamlit-app/.venv"
else
  echo "[init.sh] .venv not found at ${VENV_ACTIVATE}" >&2
  echo "[init.sh] run: cd streamlit-app && python -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
fi
