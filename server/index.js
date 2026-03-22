const express = require("express");
const cors = require("cors");
const multer = require("multer");
const axios = require("axios");

// Node 20 has global FormData/Blob
const app = express();
const upload = multer(); // in-memory

const PY_API = process.env.PY_API || "http://127.0.0.1:8081";
const PORT = process.env.PORT || 3001;

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

// Load GEMINI_API_KEY from HazardDetection/.env
function loadHazardEnv() {
  const envPath = path.resolve(__dirname, "..", "HazardDetection", ".env");
  try {
    const lines = fs.readFileSync(envPath, "utf8").split("\n");
    const env = {};
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith("#")) {
        const [key, ...rest] = trimmed.split("=");
        if (key) env[key.trim()] = rest.join("=").trim();
      }
    }
    return env;
  } catch {
    return {};
  }
}
const hazardEnv = loadHazardEnv();

app.use(cors());
// We'll accept JSON from the frontend if it sends it,
// but we'll forward to Python using form-data / urlencoded as required.
app.use(express.json({ limit: "25mb" }));

app.get("/health", (req, res) => {
  res.json({ ok: true, py_api: PY_API });
});

/**
 * POST /api/process-text
 * Python expects: application/x-www-form-urlencoded with fields:
 *  - text
 *  - patient_id
 */
app.post("/api/process-text", async (req, res) => {
  try {
    // Accept either JSON body {text, patient_id} or form body from frontend.
    const text = req.body?.text;
    const patient_id = req.body?.patient_id;

    if (!text || !patient_id) {
      return res.status(400).json({ error: "Missing text or patient_id" });
    }

    const params = new URLSearchParams();
    params.append("text", text);
    params.append("patient_id", patient_id);

    const r = await axios.post(`${PY_API}/api/process-text`, params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      timeout: 120000,
    });

    res.status(r.status).send(r.data);
  } catch (e) {
    res.status(e.response?.status || 502).json({
      error: "Upstream /api/process-text failed",
      detail: e.message,
      upstream: e.response?.data,
    });
  }
});

/**
 * POST /api/process-voice
 * Python expects: multipart/form-data with fields:
 *  - audio (file)
 *  - patient_id (string)
 *
 * We'll accept an upload from the frontend as field name "audio".
 */
app.post("/api/process-voice", upload.single("audio"), async (req, res) => {
  try {
    const patient_id = req.body?.patient_id;

    if (!req.file) {
      return res.status(400).json({ error: "Missing audio file. Expected form-data field 'audio'." });
    }
    if (!patient_id) {
      return res.status(400).json({ error: "Missing patient_id" });
    }

    const form = new FormData();
    form.append("patient_id", patient_id);
    form.append("audio", new Blob([req.file.buffer]), req.file.originalname || "audio.wav");

    const r = await axios.post(`${PY_API}/api/process-voice`, form, {
      timeout: 300000,
      maxBodyLength: Infinity,
      // In Node 20, axios will set headers for FormData automatically in most cases.
      // If you run into issues, we can explicitly set boundary headers with a library.
    });

    res.status(r.status).send(r.data);
  } catch (e) {
    res.status(e.response?.status || 502).json({
      error: "Upstream /api/process-voice failed",
      detail: e.message,
      upstream: e.response?.data,
    });
  }
});

app.post("/api/hazard-detection", async (req, res) => {
  const { mode = "directory", imageDir, outputFile, pollInterval = 4.0 } = req.body || {};

  if (mode !== "directory") {
    return res.status(400).json({ error: "Only directory mode wired for now" });
  }
  if (!imageDir) return res.status(400).json({ error: "imageDir is required" });

  const projectRoot = path.resolve(__dirname, "..");
  const py = path.join(projectRoot, "venv", "Scripts", "python.exe");
  const script = path.join(projectRoot, "HazardDetection", "hazard_detector.py");

  // IMPORTANT: imageDir/outputFile should be relative to HazardDetection (like your terminal test)
  const args = [
    script,
    "--mode", "directory",
    "--image-dir", imageDir,
    "--output-file", outputFile || "testing_documentation/directory_results_ui.txt",
    "--poll-interval", String(pollInterval),
  ];

  console.log("[hazard-detection] Spawning Python:");
  console.log("  py:", py);
  console.log("  script:", script);
  console.log("  args:", args);
  console.log("  cwd:", projectRoot);

  const hazardDetectionDir = path.join(projectRoot, "HazardDetection");
  const p = spawn(py, args, { cwd: hazardDetectionDir, env: { ...process.env, ...hazardEnv } });

  p.on("error", (spawnErr) => {
    console.error("[hazard-detection] Failed to spawn process:", spawnErr.message);
    res.status(500).json({ success: false, error: spawnErr.message });
  });

  let out = "";
  let err = "";
  p.stdout.on("data", (d) => { out += d.toString(); console.log("[hazard-detection stdout]", d.toString()); });
  p.stderr.on("data", (d) => { err += d.toString(); console.error("[hazard-detection stderr]", d.toString()); });

  p.on("close", (code) => {
    console.log("[hazard-detection] Process exited with code:", code);
    // Extract JSON_RESULTS_START...JSON_RESULTS_END
    const start = out.indexOf("JSON_RESULTS_START:");
    const end = out.indexOf("JSON_RESULTS_END");
    let parsed = null;

    if (start !== -1 && end !== -1) {
      const jsonText = out.slice(start + "JSON_RESULTS_START:".length, end).trim();
      try { parsed = JSON.parse(jsonText); } catch {}
    }

    if (code !== 0) {
      console.error("[hazard-detection] Error - stderr:", err);
      console.error("[hazard-detection] Error - stdout:", out);
      return res.status(500).json({ success: false, code, stderr: err, stdout: out, parsed });
    }

    const images = parsed?.images || [];
    const hazardsFound = images.filter(img => img.result?.hazard_detected).length;
    const failed = images.filter(img => img.error).length;

    const message =
    `Hazard detection completed (mode: ${mode}) — ` +
    `processed ${images.length} image(s), hazards in ${hazardsFound}` +
    (failed ? `, failed ${failed}` : '');

    return res.json({
    success: true,
    message,        // ✅ what VoiceCommand.jsx expects
    output: out,    // ✅ terminal-style log (what your screenshot shows)
    images,         // ✅ what your UI uses to render the cards
    stderr: err || null,
    mode,           // optional but helpful
    });
  });
});

app.listen(PORT, () => {
  console.log(`✅ Node backend running: http://127.0.0.1:${PORT}`);
  console.log(`➡️  Proxying to Python: ${PY_API}`);
});