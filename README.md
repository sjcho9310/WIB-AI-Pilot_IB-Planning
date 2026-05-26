# my_app

iOS / Android Flutter 앱 — 1인 개발 / 최대 1만 MAU 규모를 가정한 스타터.

## 스택

- **Flutter** 3.13.x (Nix `pkgs.flutter` via `.idx/dev.nix`)
- **상태관리**: `flutter_riverpod`
- **라우팅**: `go_router`
- **HTTP**: `dio`
- **모델 코드 생성**: `freezed` + `json_serializable` + `build_runner`
- **백엔드**: Firebase (Auth / Firestore / Core) — 연결은 아래 TODO 참조

## 폴더 구조

```
lib/
  main.dart                 # 앱 진입점 (Firebase init + ProviderScope)
  src/
    app.dart                # MaterialApp.router + 테마
    routing/
      app_router.dart       # go_router 라우트 정의
    core/
      api/dio_client.dart   # Dio provider
      firebase/firebase_bootstrap.dart
    features/
      home/presentation/home_screen.dart
```

## 실행

```bash
flutter pub get
flutter run                 # 연결된 디바이스/에뮬레이터로
flutter analyze             # 정적 분석
flutter test                # 위젯 테스트
```

코드 생성 (freezed/json_serializable 사용 시):

```bash
dart run build_runner build --delete-conflicting-outputs
```

## Firebase Studio (IDX)

`.idx/dev.nix`에 Flutter SDK, JDK17, unzip, Dart/Flutter VS Code 익스텐션, Android/Web 프리뷰가 선언되어 있습니다. 워크스페이스를 재시작하면 자동으로 구성됩니다.

## TODO

### Firebase 프로젝트 연결

현재 `firebase_core/auth/firestore` 패키지는 추가되어 있지만 실제 Firebase 프로젝트와는 연결되지 않은 상태입니다. 다음 단계를 완료해야 정상 동작합니다.

1. **Firebase 프로젝트 생성**
   - https://console.firebase.google.com → "프로젝트 만들기"
   - (Firebase는 GCP 위에서 동작 — 같은 이름의 GCP 프로젝트가 자동 생성됨)

2. **FlutterFire CLI 설치 & 설정**
   ```bash
   npm install -g firebase-tools         # 또는 brew install firebase-cli
   firebase login                        # 브라우저 로그인
   dart pub global activate flutterfire_cli
   flutterfire configure                 # iOS/Android 앱 자동 등록 + 키 파일 생성
   ```
   결과물:
   - `lib/firebase_options.dart`
   - `android/app/google-services.json`
   - `ios/Runner/GoogleService-Info.plist`

   위 세 파일은 `.gitignore`에 포함되어 있어 VCS에 올라가지 않습니다 (시크릿 관리 전략은 별도로 결정).

3. **`firebase_bootstrap.dart` 수정**
   `lib/src/core/firebase/firebase_bootstrap.dart`의 `Firebase.initializeApp()`을 다음으로 변경:
   ```dart
   import 'package:my_app/firebase_options.dart';
   await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
   ```

4. **Firebase 콘솔에서 서비스 활성화**
   - Authentication → 사용할 로그인 방법 (Email/Google/Apple 등) 켜기
   - Firestore Database → 데이터베이스 생성 (테스트 모드로 시작 후 보안 규칙 작성)

### 그 외

- [ ] 앱 아이콘 / 스플래시 (`flutter_launcher_icons`, `flutter_native_splash`)
- [ ] 라우트 추가 (`lib/src/features/` 하위 feature 디렉토리 확장)
- [ ] 푸시 알림 (`firebase_messaging`)
- [ ] Crashlytics / Analytics 연결
- [ ] CI (GitHub Actions: `flutter analyze` + `flutter test`)
- [ ] iOS 코드사이닝 / Android keystore 셋업 (배포 전)
