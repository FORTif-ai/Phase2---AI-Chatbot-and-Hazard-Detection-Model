# Deploying Fortif.ai (portfolio demo)

This deploys the **interactive core** of Fortif.ai as a single, self-contained stack behind
automatic HTTPS, so you can link a live URL from your portfolio.

**What runs in the hosted demo**
- React dashboard (modern UI)
- RAG memory chatbot + memory dashboard (Weaviate + Google Gemini)
- Voice & text command interface (Whisper transcription)
- Weaviate vector database (persistent)

**What is intentionally *not* in the hosted demo**
- **Hazard detection** — it's a server-side batch tool (scans image directories, sends Twilio SMS)
  and its UI/back-end modes don't currently match, so it isn't a compelling public feature. Keep
  running it locally per the main `README.md`. Enabling it on the host is a follow-up (needs OpenCV
  in the Node image + a small fix so the Node endpoint accepts the UI's mode).
- **`main.py`** — the microphone/keyboard CLI assistant runs on a local device, not a server.

> ⚠️ **Use demo data only.** Seed the sample "Eleanor" (`patient_123`) memories — do **not** put real
> patient information on a public demo. Real patient data would bring health-privacy obligations
> (PHIPA/PIPEDA: consent, encryption, Canadian data residency) that a portfolio demo shouldn't carry.

---

## Architecture

```
Internet ──HTTPS──▶  Caddy (web)  ──/──────────────▶ static React SPA
                       │           ──/api/process-* ─▶ node:3001 ──▶ voice:8081 (Whisper + Gemini)
                       │           ──/api/*  ────────▶ rag:8000  ──▶ weaviate:8080 (volume)
                     :80/:443                                         └▶ Google Gemini (external)
```
Only the `web` (Caddy) container is exposed publicly; everything else talks over the internal Docker network.

---

## Prerequisites

- **A Linux VM** with a public IP. Because Whisper (PyTorch) runs in-process, size for RAM:
  - Recommended: **4 GB RAM / 2 vCPU / ~20 GB disk** (e.g. Hetzner CX22 ≈ €4/mo — best value,
    or DigitalOcean/Linode 4 GB ≈ $24/mo).
  - 1–2 GB boxes will OOM when Whisper loads.
- **A domain name** (or subdomain) you can point at the VM — required for HTTPS, which the microphone
  feature needs (`getUserMedia` only works over HTTPS).
- **Docker Engine + Compose plugin** on the VM.
- A **Google AI Studio API key** (https://aistudio.google.com/app/apikey).

---

## Step-by-step

### 1. Point DNS at the server
Create an **A record** for `demo.yourdomain.com` → your VM's public IP. Wait for it to resolve.

### 2. Install Docker on the VM
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # then log out/in
```

### 3. Get the code (this branch)
```bash
git clone https://github.com/FORTif-ai/Phase2---AI-Chatbot-and-Hazard-Detection-Model.git
cd Phase2---AI-Chatbot-and-Hazard-Detection-Model
git checkout deploy-setup
```

### 4. Configure secrets
```bash
cp deploy/.env.example .env
nano .env
```
Set `GOOGLE_API_KEY`, `GEMINI_API_KEY` (same key is fine), a strong `API_KEY`, and your
`SITE_ADDRESS` / `SITE_URL` (your domain). The `.env` file is gitignored.

### 5. Build and start
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
First build pulls PyTorch + the Whisper model, so it takes several minutes. Caddy fetches a
Let's Encrypt certificate automatically once DNS resolves and ports 80/443 are open.

Check everything is healthy:
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f rag        # look for "RAG Server Ready"
curl -s https://demo.yourdomain.com/api/health               # {"status":"healthy",...}
```

### 6. Seed demo memories
The dashboard needs data for `patient_123`. Two easy options:

- **Via the UI:** open the site → **Memories → New Memory**, add a few for patient `patient_123`.
- **Via the API** (through the running RAG service):
  ```bash
  curl -X POST https://demo.yourdomain.com/api/ingest \
    -H "Content-Type: application/json" \
    -H "X-API-Key: <your API_KEY from .env>" \
    -d '{"patient_id":"patient_123","raw_text":"Eleanor loves gardening in the afternoon and tending to her roses.","source":"family_interview","topic":"hobbies","emotion":"positive","is_sensitive":false}'
  ```
  (`rag/add_sample_memories.py` isn't used here — it hardcodes a `localhost` Weaviate connection,
  which doesn't apply inside the container network.)

### 7. Visit
Open **https://demo.yourdomain.com** — that's your portfolio link. The voice page is at `/voice`.

---

## Day-2 operations

- **Update after pushing changes:**
  ```bash
  git pull && docker compose -f docker-compose.prod.yml up -d --build
  ```
- **Logs:** `docker compose -f docker-compose.prod.yml logs -f <service>`
- **Back up patient memories** (the only irreplaceable state):
  ```bash
  docker run --rm -v fortifai_weaviate_data:/data -v "$PWD":/backup alpine \
    tar czf /backup/weaviate-backup.tgz -C /data .
  ```
- **Stop / remove:** `docker compose -f docker-compose.prod.yml down` (add `-v` to also wipe data).

---

## Caveats & hardening

- **Gemini free tier** is rate-limited (~15 req/min); upgrade to a paid key for a reliable public demo.
- **Rotate** the old dev key `fortifai-dev-key-2024` (set a fresh `API_KEY` in `.env`).
- **CORS** is restricted to `SITE_URL`; keep it accurate.
- Address the **Dependabot** vulnerabilities GitHub flagged on the default branch.
- This stack has **no user auth** — anyone with the link can read/write demo memories. Fine for a
  demo with sample data; don't use real data.

---

## Alternative hosts (if you'd rather not run a VM)

- **Frontend on Vercel/Netlify** (static) + **backends on Render/Railway** (containers, from these
  Dockerfiles) + **Weaviate Cloud** (managed, free sandbox). Note: free PaaS tiers sleep and cold-start.
- **Google Cloud Run** (scales to zero, pairs well with Gemini) for the stateless services +
  **Weaviate Cloud Serverless** for the DB. Whisper cold starts will be slow; consider swapping voice
  transcription to a hosted STT if you go serverless.

The single-VM + Compose path above is the most faithful and predictable for a demo, and the cheapest
to keep always-on.
