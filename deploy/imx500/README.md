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

> **Docker memory:** the exporter's memory peak is cumulative across the whole run, so the OOM lands late.
> On a 24 GiB Mac (Docker VM capped at ~20 GiB) the ceiling that completes is **`fraction=0.15`
> (~160 images)**. Larger fractions OOM-kill (exit 137, `OOMKilled=true`) progressively later:
> `0.5` dies right after calibration, `0.3` after the MIP solve, `0.2` on the final packaging line.
> This matches a known upstream issue ([ultralytics#22512](https://github.com/ultralytics/ultralytics/issues/22512));
> the maintainers' fix is to **run the export on a larger x86 Linux host**. To get Sony's
> recommended >300 calibration images, regenerate on a cloud box with ≥48 GiB (see *Next steps*).
>
> Diagnosing OOM: run the container **detached** (`docker run -d`, no `--rm`) and read the true
> cause with `docker inspect -f '{{.State.OOMKilled}} {{.State.ExitCode}}' <name>` — a plain
> foreground run just prints "Killed" and `--rm` erases the evidence.

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

**Local export is done** — a deployable INT8 model exists at `models/aabb/imx500/`
(`packerOut.zip` + `labels.txt` + `MemoryReport`), built at `fraction=0.15` (160 calib images),
`Fit In Chip: true` @ 48%, and validated at **92.7% detection retention** vs FP32 (115 vs 124 on
the 8 example shelves). Good enough to deploy; the one open improvement is calibration quality.

**Next action — higher-accuracy rebuild on a larger x86 host (cloud).** The 24 GiB Mac can't fit
Sony's recommended >300 calibration images (see the Docker-memory note above). On a native-x86
box with ≥48 GiB the same toolchain runs the full `fraction=0.5` (or `1.0`) with no bisection and
no emulation tax:
```bash
# On an Ubuntu x86 VM (e.g. Hetzner/DigitalOcean) with Docker installed:
#   1. copy this repo (or just the .pt model + the calibration dataset)
#   2. run the SAME script — the Dockerfile targets linux/amd64 natively:
./deploy/imx500/export_imx500.sh   # defaults to fraction=0.5, ~534 images
#   3. copy the resulting packerOut.zip + labels.txt back into models/aabb/imx500/
```
Expect only a modest accuracy gain (INT8 calibration statistics plateau past a few hundred images),
but it lifts calibration into Sony's recommended range and closes most of the 7.3% gap.

Then re-run Phase 3 validation and swap the higher-accuracy artifact into `models/aabb/imx500/`.

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
- ✅ **Phase 2** — Export produced a valid `packerOut.zip`. Full 534-image run OOM-kills even at ~20 GiB Docker memory (the peak is cumulative + a Java packager on top); `fraction=0.15` (160 images) is the ceiling that completes locally. `model_imx_MemoryReport.json`: `Fit In Chip: true`, 48% util. A full-fraction rebuild belongs on a bigger x86 host (see *Next steps*).
- ✅ **Phase 3** — Validated INT8 vs FP32 on the 8 shelves at conf=0.5, imgsz=320: **115 vs 124 detections (92.7% retention)**, two shelves identical. Ultralytics loads the `_imx_model/` dir directly for predict (registers Sony custom layers) — no manual ONNX output parsing needed.
- ✅ **Phase 4** — Deployable subset saved to `models/aabb/imx500/` (`packerOut.zip`, `labels.txt`, `MemoryReport`); `models/README.md` gained an IMX500 section and the main `README.md` roadmap (Step 3 Track B) marked done. Raw `_imx_model/` export dir git-ignored.
- ⏸️ **Phase 5** — Deploy `detect_bookspines_imx500.py` on the Pi + AI Camera; confirm on-sensor detection + rough FPS. (Needs the Pi flashed with `imx500-all`.)

**Out of scope here (roadmap Step 4):** live bounding-box overlay UI, aspect-ratio routing into
the OBB/deskew/OCR pipeline, offline SQLite lookup.
