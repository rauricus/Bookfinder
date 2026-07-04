# x86_64 Linux environment for exporting the AABB book-spine model to Sony IMX500 format.
#
# WHY THIS EXISTS: Ultralytics `format=imx` export is Linux-only and the Sony converter
# (imxconv-pt) ships x86_64 wheels only. It runs on neither the arm64 Mac nor the arm64 Pi.
# This image is built and run with `--platform linux/amd64` (emulated on Apple Silicon) so the
# whole export/quantization toolchain works locally. See deploy/imx500/export_imx500.sh.
#
# The IMX-specific extras (model-compression-toolkit, sony-custom-layers, imx500-converter[pt],
# onnx, onnxruntime, onnxsim, edge-mdt-tpc) are intentionally NOT pre-installed here: Ultralytics
# auto-installs the versions it is compatible with on the first `yolo export format=imx` run.
# That first run therefore needs network access (docker run has it by default). If the known
# sony_custom_layers install friction appears (ultralytics#22662), pin the versions below.

FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    YOLO_CONFIG_DIR=/tmp/Ultralytics

# System deps: Python 3.10 (matches the project's conda env), a JRE for the Sony converter,
# git, and the OpenCV runtime libs Ultralytics needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv \
        default-jre-headless \
        git \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch keeps the image lean and avoids CUDA under emulation (quantization is CPU-bound).
RUN pip3 install --no-cache-dir \
        torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install --no-cache-dir ultralytics

WORKDIR /workspace

# The repo is bind-mounted at /workspace at run time (see export_imx500.sh); the actual export
# command is passed by that script so this image stays a reusable toolchain, not a one-shot.
CMD ["bash"]
