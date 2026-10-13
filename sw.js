// 서비스 워커: 오프라인에서도 앱이 열리도록 파일을 캐시해 둠.
// 앱 파일을 수정해 배포할 때는 VERSION 을 올려야 이전 캐시가 정리돼요.
const VERSION = "v2";
const CACHE = `jungsan-${VERSION}`;
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  // cache: "reload" — 브라우저 HTTP 캐시에 남은 예전 파일 대신 항상 서버에서 새로 받음
  event.waitUntil(caches.open(CACHE).then((c) =>
    c.addAll(ASSETS.map((u) => new Request(u, { cache: "reload" })))));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  // 같은 사이트 파일 + 이미지 공유용 라이브러리(cdnjs)만 캐시
  const cacheable = url.origin === location.origin || url.hostname === "cdnjs.cloudflare.com";
  if (req.method !== "GET" || !cacheable) return;

  // 페이지: 네트워크 우선 (최신 버전 반영), 실패하면 캐시
  // no-cache — 서버에 변경 여부를 매번 확인 (GitHub Pages의 10분 HTTP 캐시 우회)
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req.url, { cache: "no-cache", credentials: "same-origin" })
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put("./index.html", copy));
          }
          return res;
        })
        .catch(() => caches.match("./index.html"))
    );
    return;
  }

  // 아이콘 등 정적 파일: 캐시 우선
  event.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    }))
  );
});
