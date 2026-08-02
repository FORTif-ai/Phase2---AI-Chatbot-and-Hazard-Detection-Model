# Free live demo on Vercel

This deploys Fortif.ai as a **$0, always-on** portfolio link — no server to run, real HTTPS,
custom domain optional. It uses a **demo mode** so there's no backend to host:

| Feature | How it works for free |
|---|---|
| Dashboard, memories, search, stats | Client-side sample data + `localStorage` (per-visitor; add/edit/delete work) |
| **Chat (live AI)** | A Vercel **serverless function** calls **Gemini's free tier**, with Eleanor's memories injected as context. Your key stays server-side. |
| **Voice** | The browser's built-in **Web Speech API** (Chrome/Edge) — no Whisper server |
| Hazard detector | A realistic canned sample analysis |

If the Gemini key is missing or the free-tier limit is hit, chat falls back to a friendly canned
reply, so the link never looks broken.

---

## Deploy (5 minutes)

### 1. Get a Google AI Studio key
https://aistudio.google.com/app/apikey → create a key (free tier).

### 2. Import the repo into Vercel
1. Sign in at https://vercel.com with GitHub (free "Hobby" plan).
2. **Add New → Project → Import** this repository.
3. Under **Git Branch**, choose **`vercel-demo`** (or merge it to `main` first and deploy `main`).
4. Leave the build settings as-is — they're read from [vercel.json](vercel.json)
   (builds the dashboard with `VITE_DEMO_MODE=true`, serves `dashboard/dist`, deploys `api/`).

### 3. Add your key as an Environment Variable
In the import screen (or **Project → Settings → Environment Variables**):

| Name | Value | Environments |
|---|---|---|
| `GOOGLE_API_KEY` | your AI Studio key | Production, Preview |

### 4. Deploy
Click **Deploy**. You'll get a URL like `https://fortifai-xxxx.vercel.app` — that's your portfolio link.
Every push to the branch redeploys automatically.

### 5. (Optional) Custom domain
**Project → Settings → Domains** → add e.g. `fortifai.yourdomain.com` and follow the DNS instructions.

---

## Try it
- **Home / Memories:** enter patient id **`patient_123`** to load Eleanor's data.
- **Voice Commands page:** type a question, or click the mic (Chrome/Edge) and ask
  *"Tell me about Eleanor's morning routine"* — the reply comes from live Gemini.
- **Hazard Detector:** shows a sample analysis.

---

## Local testing
- **Full demo incl. the chat function:** install the Vercel CLI and run the dev server, which also
  runs the serverless functions:
  ```bash
  npm i -g vercel
  vercel dev            # set GOOGLE_API_KEY when prompted / in .env
  ```
- **UI only** (chat will use the canned fallback, since functions don't run under Vite):
  ```bash
  cd dashboard
  VITE_DEMO_MODE=true npm run build && npm run preview
  ```

---

## Good to know
- **Voice** needs the Web Speech API — works in Chrome/Edge, not Firefox. Text always works.
- **Gemini free tier** is ~15 req/min; heavy simultaneous use briefly triggers the canned fallback.
- **Data is demo-only and per-browser** — added memories live in that visitor's `localStorage`; they
  don't sync or persist server-side. Don't use real patient data.
- This is separate from the full self-hosted stack in [DEPLOY.md](DEPLOY.md) (Docker + Weaviate +
  Whisper), which you'd use for the real UBIlab pilot rather than a public demo.
