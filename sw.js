/* Malvani Learning AI — offline service worker.
 *
 * The point of this file is that a student on a weak or metered connection
 * can open the app once and keep using every lesson afterwards with no data
 * at all. It precaches the page shell and all lesson/scenario JSON, then
 * serves from cache first and quietly refreshes in the background.
 *
 * Bump CACHE when shipping new content or a new page build, so old caches
 * are replaced rather than shadowing the update.
 */
const CACHE = "malvani-v4";

// Relative URLs resolve against this script's location, which keeps the app
// working both at a GitHub Pages sub-path and at a local server root.
const PRECACHE = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon.svg",
  "./data/lessons/physics/motion.json",
  "./data/lessons/physics/force.json",
  "./data/lessons/physics/gravity.json",
  "./data/lessons/physics/momentum.json",
  "./data/lessons/physics/newton.json",
  "./data/lessons/physics/energy.json",
  "./data/lessons/physics/work.json",
  "./data/lessons/physics/acceleration.json",
  "./data/lessons/physics/velocity.json",
  "./data/lessons/physics/friction.json",
  "./data/lessons/physics/waves.json",
  "./data/lessons/mathematics/fractions.json",
  "./data/lessons/chemistry/atoms.json",
  "./data/lessons/biology/photosynthesis.json",
  "./data/lessons/computer_science/algorithms.json",
  "./data/scenarios/physics/motion_water_carrying_journey.json",
  "./data/scenarios/physics/momentum_cart_comparison.json",
  "./data/scenarios/physics/force_model_comparison.json",
  "./data/places/laterite_plateaus.json",
  "./data/places/sindhudurg_fort.json",
  "./data/places/amboli_ghat.json",
  "./data/places/konkan_rivers.json",
  "./data/places/devgad.json",
  "./data/places/the_coast.json"
];

self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // Add individually: one unexpected 404 must not abort the whole install
    // and leave the student with no offline copy at all.
    await Promise.all(PRECACHE.map(url =>
      cache.add(new Request(url, { cache: "reload" })).catch(() => null)
    ));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(n => n !== CACHE).map(n => caches.delete(n)));
    await self.clients.claim();
  })());
});

self.addEventListener("message", event => {
  if (event.data === "skip-waiting") self.skipWaiting();
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  const sameOrigin = url.origin === self.location.origin;
  const isFont = url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com";
  if (!sameOrigin && !isFont) return;

  // A navigation offline should still open the app, not a browser error page.
  if (request.mode === "navigate") {
    event.respondWith((async () => {
      try {
        return await fetch(request);
      } catch (err) {
        const cache = await caches.open(CACHE);
        return (await cache.match("./index.html")) || (await cache.match("./")) || Response.error();
      }
    })());
    return;
  }

  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(request, { ignoreSearch: true });

    const network = fetch(request).then(response => {
      if (response && (response.ok || response.type === "opaque")) {
        cache.put(request, response.clone()).catch(() => {});
      }
      return response;
    }).catch(() => null);

    // Cache first so the app is instant and works with no connection; the
    // network copy still refreshes the cache for next time.
    if (cached) { event.waitUntil(network); return cached; }

    const fresh = await network;
    return fresh || new Response("Offline and not cached yet.", {
      status: 503, headers: { "Content-Type": "text/plain" }
    });
  })());
});
