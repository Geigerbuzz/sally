# Hosting Sally for a live demo

Sally is a **static site** (no backend) that calls DeepSeek directly from the browser, so it hosts
anywhere that serves static files. GitHub Pages is the easiest, and works on any device on stage.

## 1 · Put it live on GitHub Pages (one-time, ~1 minute)

1. Go to the repo on GitHub → **Settings → Pages**.
2. Under **Build and deployment → Source**, pick **Deploy from a branch**.
3. Branch: **`claude/reactive-poc`**, folder: **`/ (root)`** → **Save**.
4. Wait ~60 seconds, then refresh. Your site is at:

   **https://geigerbuzz.github.io/sally/**

   (`index.html` is the dashboard. `.nojekyll` is already in the repo so every file is served as-is.)

> Prefer it on the default branch? Merge `claude/reactive-poc` into your default branch first, then
> point Pages at that branch instead. Either works.

## 2 · Demo on someone else's device (the stage laptop)

The DeepSeek key lives only in **that browser's** localStorage — it is never in the repo or sent
anywhere except DeepSeek. Two ways to set it on a fresh device:

- **One-link (fastest):** open
  `https://geigerbuzz.github.io/sally/?key=YOUR_DEEPSEEK_KEY`
  Sally saves the key locally and **immediately strips it from the URL**. The dock gear shows a green dot.
- **Manual:** open the site → click the **gear** in the dock → paste the key → **Test** → **Save**.

Pick the model in the same panel (`deepseek-v4-flash` is fast; `deepseek-v4-pro` is smarter).

## 3 · Good-to-know for the stage

- **No key / no Wi-Fi?** Sally falls back to **offline demo mode** — it still answers with citations,
  the widgets/graph/upload all work; only the live LLM calls are skipped.
- **Browser:** use **Chrome or Edge** for the smooth page-to-page crossfade (View Transitions).
  Safari/Firefox still work, just with a normal page change.
- **HTTPS:** GitHub Pages is HTTPS, which DeepSeek's CORS requires — nothing to configure.
- **Security:** the `?key=` form is convenient but the key is briefly in the address bar / history.
  Use a key you can **rotate after the demo** (DeepSeek dashboard → revoke/replace).
- **Reset between runs:** dock gear → **Reset demo data** clears uploaded docs, chat history, and
  custom widget boards on that device.

## Other hosts (if you ever want them)

Any static host works the same way (drag-and-drop the repo folder): **Netlify**, **Vercel**,
**Cloudflare Pages**. No build step — it's plain HTML/CSS/JS. The only requirement is HTTPS.
