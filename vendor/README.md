# Vendored assets (offline runtime)

These are bundled into `sally-knowledge-graph.html` at build time so the page
runs **fully offline** at presentation time — no CDN, no runtime fetches.

- `force-graph.min.js` — force-graph v1.51.4 UMD build (vasturiano), MIT.
  Source: npm `force-graph` tarball, `dist/force-graph.min.js`.
- `fonts.css` — `@font-face` rules with base64-embedded **woff2** (latin subset)
  for Bricolage Grotesque (display), Hanken Grotesk (body), IBM Plex Mono (mono).
  Variable-weight families are embedded once with a weight range.

Rebuild the page after changing either file: `./build.sh`
