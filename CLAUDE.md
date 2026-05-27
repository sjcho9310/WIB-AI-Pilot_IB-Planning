# CLAUDE.md

이 저장소에서 Claude가 따라야 할 작업 지침입니다.

## 환경

- **호스트**: Firebase Studio (Cloud IDE, IDX 기반)
- **Python**: 3.11 (`streamlit-app/.venv`)
- **Node**: 20 + pnpm
- **워크스페이스 루트**: `/home/user/test_repository`

## 개발 진행 원칙

### 1. PoC → 고급화 단계적 접근
- 사용자가 새 기능을 요청하면 **먼저 Streamlit으로 PoC**를 만든다 (`streamlit-app/`).
- 사용자가 "고급 버전", "프로덕션", "예쁘게", "UI 개선" 등을 요청하면 **React로 확장**한다 (`react-app/`).
- PoC 단계에서는 동작 검증이 최우선 — 디자인/추상화에 시간을 쓰지 않는다.

### 2. 스택 선택 기준
- **백엔드 필요 시**: FastAPI (별도 `backend/` 디렉터리에 구성, `uvicorn`으로 실행).
  - 단순 LLM 호출/스크립트 수준이면 Streamlit 내부에서 직접 처리 — 굳이 FastAPI 분리하지 않는다.
  - 외부에서 API 호출이 필요하거나 React와 분리된 백엔드가 필요할 때만 FastAPI 추가.
- **프론트**: 난이도에 따라 Streamlit 또는 React 중 선택.
  - 폼/대시보드/챗 UI → Streamlit
  - 인터랙티브 UI, 커스텀 컴포넌트, 라우팅, 상태관리 필요 → React

### 3. 응답 스타일
- 사용자는 **비개발자/비전공자**일 수 있다.
- 코드를 설명할 때 전문 용어를 풀어쓰고, 무엇을/왜 만들었는지 한두 줄로 먼저 요약한다.
- 명령어를 안내할 때는 복붙 가능한 형태로 제공한다.

### 4. 빌드 & 즉시 확인
개발이 끝나면 **반드시 직접 실행해서 동작 확인**까지 마치고 사용자에게 접속 URL을 안내한다.
Git 푸시/배포는 사용자가 명시적으로 요청하기 전까지 진행하지 않는다.

### 5. Firebase Studio 포트 노출 (필수 검토)
Cloud IDE는 컨테이너 내부에서 실행되므로 `localhost`/`127.0.0.1` 바인딩은 외부에서 접근 불가하다.
**모든 서비스는 `0.0.0.0`에 바인딩**해야 IDX 미리보기/포트 포워딩이 동작한다.

| 서비스 | 실행 명령 (워크스페이스 루트 기준) |
|---|---|
| Streamlit | `streamlit-app/.venv/bin/streamlit run streamlit-app/app.py --server.address=0.0.0.0 --server.port=8080 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false` |
| React (Vite) | `cd react-app && pnpm dev` (vite.config.js에 `host: '0.0.0.0'` 이미 설정됨) |
| FastAPI | `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload` |

- Streamlit의 `enableCORS`/`enableXsrfProtection=false`는 IDX 미리보기 iframe 안에서 동작하기 위함.
- 포트는 충돌하지 않게 분리: Streamlit 8080, FastAPI 8000, React 5173.
- `pkgs` 또는 시스템 의존성이 새로 필요하면 `.idx/dev.nix`의 `packages`에 추가하고 사용자에게 **rebuild가 필요함**을 알린다.
- 서비스 실행은 `run_in_background: true`로 띄우고 로그를 잠시 확인한 뒤 사용자에게 접속 안내.

## 작업 시 체크리스트
- [ ] PoC면 Streamlit, 고도화면 React 선택했는가
- [ ] 백엔드 분리가 정말 필요한가 (아니면 Streamlit 내부 처리)
- [ ] `0.0.0.0` 바인딩 확인했는가
- [ ] 실행 후 동작 확인 + 사용자에게 접속 방법 안내했는가
- [ ] 비개발자도 이해할 설명을 덧붙였는가
