// 모았텅 허브 서비스워커
//
// ⚠️ 이 워커의 등록 scope는 /moattung/ 이라서, 그대로 두면 하위 앱
//    (/moattung/dahaettung/ 등)으로 들어가는 첫 요청까지 이 워커가 가로챈다.
//    각 앱은 자기 폴더에 자기 서비스워커를 따로 갖고 있으므로, 허브는
//    **자기 폴더에 직접 있는 파일만** 처리하고 하위 폴더 요청은 전부 무시한다.
//
// ⚠️ 캐시 삭제도 마찬가지다. Cache Storage는 origin 전체가 공유하므로
//    "내 것 아닌 캐시 전부 삭제"를 하면 세 앱의 오프라인 캐시를 날려버린다.
//    여기서는 'moattung-hub-' 로 시작하는 옛 캐시만 지운다.

const CACHE = 'moattung-hub-v1';

// 허브 화면이 카드에 띄우는 각 앱 캐릭터 이미지.
// 하위 폴더에 있지만 이 셋만은 예외로 허용한다 (오프라인에서도 카드가 보이게).
// 이미지 파일이라 앱 진입 자체를 가로채는 일은 없다.
const CARD_ICONS = [
  './dasseottung/icon-192.png',
  './dahaettung/icon-192.png',
  './dappaettung/icon-192.png',
];

const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  ...CARD_ICONS,
];

// 허브 폴더 자신의 경로 (예: '/moattung/')
const BASE_PATH = new URL('./', self.location).pathname;
const CARD_ICON_PATHS = CARD_ICONS.map((u) => new URL(u, self.location).pathname);

// 이 요청이 '허브 폴더에 직접 들어있는 파일'인지 판단한다.
// 하위 앱 경로(dahaettung/... )는 '/'가 더 있으므로 false가 된다.
function isHubScoped(url) {
  if (url.origin !== self.location.origin) return false;
  if (CARD_ICON_PATHS.includes(url.pathname)) return true;
  if (!url.pathname.startsWith(BASE_PATH)) return false;
  const rest = url.pathname.slice(BASE_PATH.length);
  return rest === '' || !rest.includes('/');
}

// ── install: 허브 셸을 캐시. 하나가 없어도 전체가 깨지지 않게 개별 캐시.
self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await Promise.all(
      ASSETS.map((url) => cache.add(new Request(url, { cache: 'reload' })).catch(() => {}))
    );
    await self.skipWaiting();
  })());
});

// ── activate: 허브의 옛 캐시만 정리한다 (다른 앱 캐시는 건드리지 않음).
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.filter((k) => k.startsWith('moattung-hub-') && k !== CACHE).map((k) => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

// ── fetch: 허브 폴더의 GET 요청만 처리한다.
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (!isHubScoped(url)) return; // 하위 앱·외부 요청은 각자에게 맡긴다

  // 허브 화면(HTML): 최신을 먼저 받아보고, 실패하면 캐시로 떨어진다.
  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE);
      try {
        const fresh = await fetch(req);
        if (fresh && fresh.ok) cache.put('./index.html', fresh.clone());
        return fresh;
      } catch (e) {
        const cached = (await cache.match('./index.html')) || (await cache.match('./'));
        if (cached) return cached;
        throw e;
      }
    })());
    return;
  }

  // 아이콘 등 정적 자원: 캐시 우선, 없으면 받아서 캐시에 저장.
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(req, { ignoreSearch: true });
    if (cached) return cached;
    const fresh = await fetch(req);
    if (fresh && fresh.ok && fresh.type === 'basic') cache.put(req, fresh.clone());
    return fresh;
  })());
});
