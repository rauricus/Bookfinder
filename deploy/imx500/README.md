# IMX500 export & edge deployment

Tooling to run the AABB book-spine detector **on-chip** on the Raspberry Pi AI Camera (IMX500).
This is roadmap **Step 3, Track B** (see the main [README](../../README.md)). This document is the
living plan + status so the work can be paused and resumed anytime.

## Why this is structured the way it is

Ultralytics `format=imx` export is **Linux-only** and the Sony converter (`imxconv-pt`) ships
**x86_64 wheels only** — it runs on neither an arm64 host nor the arm64 Pi. So the export runs
inside an **x86_64 Ubuntu container** (`--platform linux/amd64`, emulated on Apple Silicon).
Deployment on the Pi uses the **Aitrios modlib**, which consumes `packerOut.zip` directly and
uploads the network to the sensor — there is no manual `.rpk` packaging step.

Source model: `models/aabb/YOLO11-n/detect-book-spines.train1.pt` (YOLO11n-detect, imgsz=320,
mAP50=0.959). FP32 baseline on the 8 `example-files/books/` shelves: **124 detections**, with
clutter (plush toys, figurines) correctly ignored.

## Files

| File | Runs on | Purpose |
|------|---------|---------|
| `Dockerfile` | x86_64 (amd64, emulated) | toolchain image for the export |
| `export_imx500.sh` | host | Build image + run `yolo export format=imx` against the model/dataset |
| `requirements.lock.txt` | — | Frozen transitive versions of the working toolchain |
| `detect_bookspines_imx500.py` | Raspberry Pi 5 | modlib smoke-test: load model on the AI Camera, print detections |

## How to run the export

```bash
# Docker Desktop (or Colima) must be running with linux/amd64 emulation.
./deploy/imx500/export_imx500.sh
# → models/aabb/YOLO11-n/detect-book-spines.train1_imx_model/
#   (packerOut.zip, labels.txt, model_imx.onnx, model_imx_MemoryReport.json, …)
```
Args (all optional): `export_imx500.sh [model] [data] [imgsz] [fraction]`. Defaults: the train1
model, the P2 aabb data.yaml, `imgsz=320`, `fraction=0.5` (~534 of the 1069 val images for INT8
calibration). The pinned toolchain is pre-installed in the image, so the export runs fully offline;
it is still slow under x86 emulation (~10–15 min for the 534-image quantization).

> **Docker memory:** the 534-image quantization needs **≥16 GiB** allocated to Docker Desktop
> (Settings → Resources → Memory). At the 8 GiB default it OOM-kills mid-quantization (exit 137).
> Lower memory works only with a smaller `fraction` (e.g. `0.02` ≈ 21 images, proven to complete).

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

## Next steps

**Next action:** run the full-quality export (Docker allocated ≥16 GiB):
```bash
./deploy/imx500/export_imx500.sh
```
Then continue with Phase 3 (validate) and Phase 4 (store artifacts). The export toolchain is fully
solved and reproducible — the only thing left in Phase 2 is a clean run that survives the OOM.

The pipeline is **already proven end-to-end**: an earlier `fraction=0.02` (21-image) run completed
quantization *and* the Sony converter, producing a valid `packerOut.zip` + `model_imx.onnx` +
`MemoryReport` (memory: 48% util, `Fit In Chip: true`). That partial artifact was intentionally
cleared; the pending run just redoes it with 534 calibration images for better INT8 accuracy.

## Verified working toolchain (baked into the image; frozen in `requirements.lock.txt`)

Determined empirically after fixing three conflicts (see `Dockerfile` comments):
`model-compression-toolkit==2.4.5`, `edge-mdt-cl==1.0.0`, `imx500-converter[pt]==3.17.3`,
`sony-custom-layers==0.3.0`, `numpy==1.26.4`, `opencv-python==4.11`, `protobuf==4.25.5`,
`ultralytics==8.4.87`, `torch==2.12.1+cpu`, **OpenJDK 21** (Sony packager needs Java ≥17).
Do **not** bump MCT past 2.5 without re-pinning `edge-mdt-cl` (breaks on `MulticlassNMSOBB`).

## Implementation status

Legend: ✅ done · 🔜 next · ⬜ todo · ⏸️ blocked (needs hardware)

- ✅ **Phase 0** — Verify FP32 model on all 8 example shelves (124 detections)
- ✅ **Phase 1** — Export environment: `Dockerfile` (pinned toolchain, Java 21) + `export_imx500.sh` + `requirements.lock.txt`. Docker `linux/amd64` emulation verified.
- 🔜 **Phase 2** — Full-quality export (534 calib images). Toolchain solved; pipeline proven at 21 images. **Remaining: one clean 534-image run with ≥16 GiB Docker memory** (see *Next steps*). Then check `model_imx_MemoryReport.json` (already known to fit: 48% util).
- ⬜ **Phase 3** — Validate the quantized model on the 8 example images; detection count must stay within a small tolerance of the FP32 baseline (124). First inspect `model_imx.onnx` output signature, then reuse the loop in `detect_bookspines.py:77-106`. Levers if it regresses: more calibration images, try `imgsz=640`.
- ⬜ **Phase 4** — Save deployable subset (`packerOut.zip`, `labels.txt`, `MemoryReport`) to `models/aabb/imx500/`; update `models/README.md` + main `README.md` roadmap.
- ⏸️ **Phase 5** — Deploy `detect_bookspines_imx500.py` on the Pi + AI Camera; confirm on-sensor detection + rough FPS. (Needs the Pi flashed with `imx500-all`.)

**Out of scope here (roadmap Step 4):** live bounding-box overlay UI, aspect-ratio routing into
the OBB/deskew/OCR pipeline, offline SQLite lookup.
