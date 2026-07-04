# x86_64 Linux environment for exporting the AABB book-spine model to Sony IMX500 format.
#
# WHY THIS EXISTS: Ultralytics `format=imx` export is Linux-only and the Sony converter
# (imxconv-pt) ships x86_64 wheels only. It runs on neither the arm64 Mac nor the arm64 Pi.
# This image is built and run with `--platform linux/amd64` (emulated on Apple Silicon) so the
# whole export/quantization toolchain works locally. See deploy/imx500/export_imx500.sh.
#
# The IMX toolchain is PINNED and pre-installed here (not left to Ultralytics' runtime
# auto-install) because that auto-install resolves dependencies incrementally and drifts into
# broken combinations. Two conflicts were hit and fixed by the pins below:
#   1. protobuf/tensorboard mismatch -> resolved by installing the whole stack in one pass.
#   2. model-compression-toolkit floats to 2.6.0, which needs edge-mdt-cl>=1.1.0 (MulticlassNMSOBB),
#      but Ultralytics requires edge-mdt-cl<1.1.0. Pin MCT==2.4.5, the newest that pairs with 1.0.0.
# Also: the Sony packager (sdspconv) is a Java 17+ app -> Java 21 is required (default-jre was too
# old); and the converter backend needs the `imx500-converter[pt]` extra, not the bare package.
# Do NOT bump model-compression-toolkit past 2.5 without re-pinning edge-mdt-cl, or the export
# silently rebreaks. Exact transitive versions are frozen in requirements.lock.txt.

FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    YOLO_CONFIG_DIR=/tmp/Ultralytics

# System deps: Python 3.10, Java 21 (Sony packager needs >=17), git, and OpenCV runtime libs.
# openjdk-21-jre-headless is the only JRE installed, so it becomes the default `java`.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv \
        openjdk-21-jre-headless \
        git \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch keeps the image lean and avoids CUDA under emulation (quantization is CPU-bound).
RUN pip3 install --no-cache-dir \
        torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install --no-cache-dir ultralytics

# Pinned IMX export toolchain. numpy<2 / opencv-python<5 keep the MCT/tensorflow stack coherent.
RUN pip3 install --no-cache-dir \
        "numpy<2" \
        "opencv-python<5" \
        "model-compression-toolkit==2.4.5" \
        "edge-mdt-cl==1.0.0" \
        "edge-mdt-tpc>=1.2.0" \
        "pydantic<2.12" \
        "imx500-converter[pt]" \
        "sony-custom-layers[pt]" \
        onnx onnxruntime onnxsim

# Fail the build early if the toolchain can't import or the converter binary is missing.
RUN python3 -c "import model_compression_toolkit as m; print('MCT', m.__version__)" \
    && imxconv-pt --version \
    && java -version

WORKDIR /workspace

# The repo is bind-mounted at /workspace at run time (see export_imx500.sh); the actual export
# command is passed by that script so this image stays a reusable toolchain, not a one-shot.
CMD ["bash"]
