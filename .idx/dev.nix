# AI-Pilot 교육용 개발 환경
# Python 3.11 + Streamlit + React (Vite) + Claude Code
# Firebase Studio (IDX) workspace 설정: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  channel = "stable-24.05";

  packages = [
    # Python 스택
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv

    # Node.js 스택
    pkgs.nodejs_20
    pkgs.nodePackages.pnpm

    # 유틸리티
    pkgs.git
    pkgs.gh
    pkgs.jq
    pkgs.ripgrep
    pkgs.curl
    pkgs.unzip
  ];

  env = {
    PYTHONDONTWRITEBYTECODE = "1";
    PIP_DISABLE_PIP_VERSION_CHECK = "1";
  };

  idx = {
    extensions = [
      # Claude Code
      "anthropic.claude-code"

      # Python
      "ms-python.python"
      "ms-python.vscode-pylance"
      "ms-python.debugpy"

      # JavaScript / React
      "dbaeumer.vscode-eslint"
      "esbenp.prettier-vscode"
      "bradlc.vscode-tailwindcss"
      "dsznajder.es7-react-js-snippets"

      # 공통
      "mikestead.dotenv"
    ];

    workspace = {
      onCreate = {
        # Streamlit 가상환경 + 의존성 설치 (워크스페이스 최초 생성 시)
        install-python = ''
          cd "$WORKSPACE_DIR/streamlit-app" && \
          python -m venv .venv && \
          .venv/bin/pip install --upgrade pip && \
          .venv/bin/pip install -r requirements.txt
        '';
        # React 의존성 설치
        install-node = ''
          cd "$WORKSPACE_DIR/react-app" && pnpm install
        '';
        default.openFiles = [
          "README.md"
          "streamlit-app/app.py"
          "react-app/src/App.jsx"
        ];
      };
      # 매번 시작 시 누락 또는 깨진 경우 복구
      # (Nix 리빌드로 Python 경로가 바뀌면 기존 .venv 심볼릭 링크가 stale 상태가 됨)
      onStart = {
        ensure-venv = ''
          cd "$WORKSPACE_DIR/streamlit-app" || exit 0
          if ! .venv/bin/python -c "import sys" >/dev/null 2>&1; then
            rm -rf .venv && \
            python -m venv .venv && \
            .venv/bin/pip install --upgrade pip && \
            .venv/bin/pip install -r requirements.txt
          fi
        '';
        ensure-node-modules = ''
          if [ ! -d "$WORKSPACE_DIR/react-app/node_modules" ]; then
            cd "$WORKSPACE_DIR/react-app" && pnpm install
          fi
        '';
      };
    };

    # Firebase Studio (IDX) 미리보기 / 포트 포워딩
    # - enable=true 로 켜야 IDX 가 컨테이너 내부 포트를 외부 HTTPS 프록시로 노출
    # - 각 preview 엔트리는 IDX 미리보기 패널 탭으로 표시되며 $PORT 가 자동 할당됨
    # - 모든 서비스는 0.0.0.0 에 바인딩되어야 외부 접근 가능 (localhost 안 됨)
    previews = {
      enable = true;
      previews = {
        # Streamlit PoC 미리보기
        # iframe 내 동작을 위해 CORS / XSRF 비활성화, headless 모드 필수
        streamlit = {
          command = [
            "streamlit-app/.venv/bin/streamlit"
            "run"
            "streamlit-app/app.py"
            "--server.address=0.0.0.0"
            "--server.port=$PORT"
            "--server.headless=true"
            "--server.enableCORS=false"
            "--server.enableXsrfProtection=false"
            "--browser.gatherUsageStats=false"
          ];
          manager = "web";
        };

        # React (Vite) 미리보기
        # vite.config.js 가 process.env.PORT 와 host 0.0.0.0 를 이미 읽도록 설정됨
        react = {
          command = [
            "pnpm"
            "--dir"
            "react-app"
            "dev"
            "--"
            "--host"
            "0.0.0.0"
            "--port"
            "$PORT"
          ];
          manager = "web";
        };

        # FastAPI 백엔드는 추후 backend/ 디렉터리가 생기면 여기 아래 preview 추가:
        # fastapi = {
        #   command = ["streamlit-app/.venv/bin/python" "-m" "uvicorn" "backend.main:app" "--host" "0.0.0.0" "--port" "$PORT" "--reload"];
        #   manager = "web";
        # };
      };
    };
  };
}
