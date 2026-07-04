# IMX500 export & edge deployment

Tooling to run the AABB book-spine detector **on-chip** on the Raspberry Pi AI Camera (IMX500).
This is roadmap **Step 3, Track B** (see the main [README](../../README.md)). This document is the
living plan + status so the work can be paused and resumed anytime.

## Why this is structured the way it is

Ultralytics `format=imx` export is **Linux-only** and the Sony converter (`imxconv-pt`) ships
**x86_64 wheels only** — it runs on neither the arm64 Mac nor the arm64 Pi. So the export runs
inside an **x86_64 Ubuntu container** (`--platform linux/amd64`, emulated on Apple Silicon).
Deployment on the Pi uses the **Aitrios modlib**, which consumes `packerOut.zip` directly and
uploads the network to the sensor — there is no manual `.rpk` packaging step.

Source model: `models/aabb/YOLO11-n/detect-book-spines.train1.pt` (YOLO11n-detect, imgsz=320,
mAP50=0.959). FP32 baseline on the 8 `example-files/books/` shelves: **124 detections**, clutter
(plush toys, figurines) correctly ignored — established 2026-07-04.

## Files

| File | Runs on | Purpose |
|------|---------|---------|
| `Dockerfile` | Mac (amd64 emulated) | x86_64 toolchain image for the export |
| `export_imx500.sh` | Mac | Build image + run `yolo export format=imx` against the model/dataset |
| `detect_bookspines_imx500.py` | Raspberry Pi 5 | modlib smoke-test: load model on the AI Camera, print detections |

## How to run the export (Mac)

```bash
# Docker Desktop (or Colima) must be running with linux/amd64 emulation.
./deploy/imx500/export_imx500.sh
# → models/aabb/YOLO11-n/detect-book-spines.train1_imx_model/
#   (packerOut.zip, labels.txt, model_imx.onnx, model_imx_MemoryReport.json, …)
```
Args (all optional): `export_imx500.sh [model] [data] [imgsz] [fraction]`. Defaults: the train1
model, the P2 aabb data.yaml, `imgsz=320`, `fraction=0.1`. The first export run auto-installs the
IMX extras (MCT, sony-custom-layers, imx500-converter) and is slow under emulation.

## How to deploy on the Pi

```bash
sudo apt update && sudo apt full-upgrade
sudo apt install imx500-all          # sensor firmware + tools + camera stack
sudo reboot
python -m venv ~/bookfinder-imx && source ~/bookfinder-imx/bin/activate
pip install git+https://github.com/SonySemiconductorSolutions/aitrios-rpi-application-module-library.git
# copy models/aabb/imx500/ (packerOut.zip + labels.txt) to the Pi, then:
python deploy/imx500/detect_bookspines_imx500.py
```

## Implementation status

Legend: ✅ done · 🔜 next · ⬜ todo · ⏸️ blocked (needs hardware)

- ✅ **Phase 0** — Verify FP32 model on all 8 example shelves (124 detections; done 2026-07-04)
- ✅ **Phase 1** — Export environment: `Dockerfile` + `export_imx500.sh`. Docker Desktop confirmed running, `linux/amd64` emulation verified.
- 🔜 **Phase 2** — Run the export/quantization in the container → produce `*_imx_model/`. Check `model_imx_MemoryReport.json` fits the IMX500 budget.
- ⬜ **Phase 3** — Validate the quantized model on the 8 example images; detection count must stay within a small tolerance of the FP32 baseline (124). Levers if it regresses: raise `fraction`, ensure shelf-like calibration images, try `imgsz=640`.
- ⬜ **Phase 4** — Save deployable subset to `models/aabb/imx500/`; update `models/README.md` + main `README.md` roadmap.
- ⏸️ **Phase 5** — Deploy `detect_bookspines_imx500.py` on the Pi + AI Camera; confirm on-sensor detection + rough FPS. (Needs the Pi flashed with `imx500-all`.)

**Out of scope here (roadmap Step 4):** live bounding-box overlay UI, aspect-ratio routing into
the OBB/deskew/OCR pipeline, offline SQLite lookup.

Full approved plan (with rationale + verified doc facts): `~/.claude/plans/cryptic-yawning-sonnet.md`.
