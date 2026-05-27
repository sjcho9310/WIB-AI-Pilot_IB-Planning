# AI-Pilot 교육용 PoC 환경

Claude Code를 활용한 개발 PoC 교육을 위한 Streamlit + React 워크스페이스입니다.

## 📦 구성

```
test_repository/
├── streamlit-app/     # Python 3.11 + Streamlit 데모
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example
├── react-app/         # React 18 + Vite 데모
│   ├── package.json
│   ├── vite.config.js
│   └── src/
└── .idx/dev.nix       # Firebase Studio 워크스페이스 설정
```

## 🛠 포함된 도구

- **Python**: 3.11, pip, virtualenv
- **Node.js**: 20 + pnpm
- **유틸리티**: git, gh, jq, ripgrep, curl, unzip
- **VS Code 확장**: Claude Code, Python, Pylance, ESLint, Prettier, Tailwind CSS, GitLens 등

## 🚀 실행 방법

### Streamlit
워크스페이스 생성 시 `.venv` 가 자동 생성됩니다. 수동 실행은 다음과 같습니다.

```bash
cd streamlit-app
.venv/bin/streamlit run app.py
```

또는 IDX 프리뷰에서 **streamlit** 항목을 실행하세요.

### React
```bash
cd react-app
pnpm dev
```

또는 IDX 프리뷰에서 **web** 항목을 실행하세요.

## 🔑 API 키 설정 (선택)

```bash
cp streamlit-app/.env.example streamlit-app/.env
# .env 파일에 ANTHROPIC_API_KEY / OPENAI_API_KEY 입력
```

## 🤖 Claude Code 활용

VS Code 사이드바의 Claude Code 패널 또는 터미널에서 `claude` 명령으로 시작합니다.
각 데모 앱의 진입점(`streamlit-app/app.py`, `react-app/src/App.jsx`)을 수정하며 PoC 실습을 진행하세요.
