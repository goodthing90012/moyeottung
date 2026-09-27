# 🫙 모았텅 (moattung)

> 텅 유니버스 앱을 한곳에 모은 모노레포

기존에 따로 있던 세 개의 PWA 저장소를 커밋 기록을 유지한 채 하나로 합친 것이다.

| 폴더 | 앱 | 설명 | 테마색 |
|---|---|---|---|
| [`dahaettung/`](dahaettung/) | 다했텅 | 매일의 루틴과 프로젝트·일정 기록 | `#22B07D` |
| [`dasseottung/`](dasseottung/) | 다썼텅 | 화장품 소비 & 리필 타이밍 메이트 | `#FF5A5F` |
| [`dappaettung/`](dappaettung/) | 다뺐텅 | 칼로리 텅장 | `#4C9FEB` |
| (루트) | 모았텅 | 세 앱을 골라 들어가는 허브 | 3색 |

## 주소

GitHub Pages(`Settings → Pages → Branch: main / Folder: / (root)`)를 켜면 이렇게 열린다.

```
https://goodthing90012.github.io/moattung/                 ← 모았텅 허브
https://goodthing90012.github.io/moattung/dahaettung/      ← 다했텅
https://goodthing90012.github.io/moattung/dasseottung/     ← 다썼텅
https://goodthing90012.github.io/moattung/dappaettung/     ← 다뺐텅
```

네 개 모두 각각 따로 홈 화면에 추가(설치)할 수 있다. manifest의 `id`/`scope`/`start_url`이
전부 상대경로(`./`)라, 폴더 위치만 맞으면 레포 이름이 바뀌어도 그대로 동작한다.

## 구조

```
moattung/
├── index.html            # 허브 화면
├── manifest.json         # 허브 PWA 매니페스트
├── sw.js                 # 허브 서비스워커 (자기 폴더 파일만 처리)
├── icon-192.png / icon-512.png
├── .nojekyll             # GitHub Pages의 Jekyll 처리 끄기
├── .github/workflows/
│   ├── daily-reminder.yml     # 다했텅 저녁 알림 (한국시간 21시 전후)
│   └── routine-reminder.yml   # 다썼텅 루틴 알림 (한국시간 22시 전후)
├── dahaettung/           # 각 앱은 폴더 하나로 완결돼 있다
├── dasseottung/
└── dappaettung/
```

각 앱 폴더 안에도 `.github/workflows/`가 남아 있지만, GitHub은 **루트의**
`.github/workflows/`만 실행한다. 알림 워크플로를 고칠 때는 루트 쪽을 고쳐야 한다.

## 알림 워크플로에 필요한 Secret

`Settings → Secrets and variables → Actions`에 4개를 등록한다.
**앱마다 VAPID 키가 다르므로 서로 바꿔 넣으면 안 된다.**

| Secret | 앱 | 어디서 얻나 |
|---|---|---|
| `VAPID_PRIVATE_KEY` | 다했텅 | 기존 dahaettung 저장소에 넣어둔 값 |
| `PUSH_SUBSCRIPTION` | 다했텅 | 다했텅 앱 → 설정 탭 → "🔔 저녁 알림"에서 복사 |
| `DASSEOTTUNG_VAPID_PRIVATE_KEY` | 다썼텅 | 기존 dasseottung 저장소에 넣어둔 값 |
| `DASSEOTTUNG_PUSH_SUBSCRIPTION` | 다썼텅 | 다썼텅 앱 → 마이페이지 → 설정 → "🔔 루틴 알림"에서 복사 |

⚠️ **주소가 바뀌었으므로 `PUSH_SUBSCRIPTION` 두 개는 새 주소에서 다시 복사해야 한다.**
푸시 구독은 서비스워커 등록(= 주소)에 묶여 있어서, 옛 주소에서 복사한 코드는 새 주소의
앱에 알림을 보내지 못한다.

## 서비스워커 메모

- 세 앱과 허브는 각자 자기 폴더를 scope로 갖는다. 앱 안에서는 그 앱의 워커가,
  허브 화면에서는 허브 워커가 동작한다.
- **허브 워커는 하위 앱 경로를 절대 가로채지 않는다.** 허브의 scope(`/moattung/`)가
  앱 경로까지 포함하기 때문에, 가로채면 앱 진입이 깨질 수 있다.
  (`sw.js`의 `isHubScoped()` 참고)
- **Cache Storage는 origin 전체가 공유한다.** 세 앱의 워커는 `activate` 때
  "내 것이 아닌 캐시 전부 삭제"를 하므로, 어느 앱이 새 버전으로 바뀌면 다른 앱과
  허브의 오프라인 캐시가 지워진다(앱을 다시 열면 네트워크에서 받아 복구된다).
  합치기 전에도 같은 origin이었으므로 새로 생긴 문제는 아니다.
  허브 워커는 이 짓을 하지 않고 `moattung-hub-` 로 시작하는 자기 캐시만 정리한다.

## 원본 저장소

커밋 기록은 `git subtree`로 그대로 가져왔다. 원본은 읽기 전용으로만 참조했고 수정하지 않았다.

- https://github.com/goodthing90012/dasseottung
- https://github.com/goodthing90012/dahaettung
- https://github.com/goodthing90012/dappaettung
