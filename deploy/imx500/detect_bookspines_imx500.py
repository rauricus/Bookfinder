"""
On-device smoke test for the IMX500 book-spine detector.

Runs the quantized AABB model *on the Raspberry Pi AI Camera's IMX500 sensor* (not the Pi CPU)
via the Aitrios modlib, and reports live detections. Use it to confirm the exported model loads
onto the sensor and detects spines before building the full live-overlay app (roadmap Step 4).

Prerequisites (on the Pi — see deploy/imx500/README.md):
    sudo apt install imx500-all && sudo reboot
    pip install git+https://github.com/SonySemiconductorSolutions/aitrios-rpi-application-module-library.git
    # copy the export package (packerOut.zip + labels.txt) to --model-dir

Usage:
    python3 detect_bookspines_imx500.py                     # windowed, live overlay
    python3 detect_bookspines_imx500.py --no-display        # headless (SSH): print counts + FPS
    python3 detect_bookspines_imx500.py --conf 0.4 --frames 300
"""

import argparse
import os
import time

import numpy as np

# modlib is Pi/AI-Camera only. It is imported lazily inside main()/_build_model() so this file
# stays importable (and `--help` works) on a dev machine without modlib installed.

# Matches the export package produced by deploy/imx500/export_imx500.sh (single class: book-spine).
DEFAULT_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models", "aabb", "imx500")


def _build_model(model_dir):
    """Wrap the Ultralytics-exported IMX500 package as a modlib Model instance (Pi-only import).

    Defined inside a function because the base class `Model` comes from modlib, which only exists
    on the Pi/AI Camera — importing it at module scope would break `--help` on a dev machine.
    """
    from modlib.models import COLOR_FORMAT, MODEL_TYPE, Model
    from modlib.models.post_processors import pp_od_yolo_ultralytics

    class BookSpineModel(Model):
        def __init__(self, model_dir):
            packer = os.path.join(model_dir, "packerOut.zip")
            labels = os.path.join(model_dir, "labels.txt")
            if not os.path.exists(packer):
                raise FileNotFoundError(f"packerOut.zip not found in {model_dir} (run the export first)")
            super().__init__(
                model_file=packer,
                model_type=MODEL_TYPE.CONVERTED,   # Ultralytics-converted network
                color_format=COLOR_FORMAT.RGB,
                preserve_aspect_ratio=False,       # model trained/exported at square 320x320
            )
            self.labels = np.genfromtxt(labels, dtype=str, delimiter="\n")

        def post_process(self, output_tensors):
            return pp_od_yolo_ultralytics(output_tensors)

    return BookSpineModel(model_dir)


def main():
    parser = argparse.ArgumentParser(description="IMX500 on-sensor book-spine detection smoke test.")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR,
                        help="Directory holding packerOut.zip + labels.txt (default: models/aabb/imx500)")
    parser.add_argument("--conf", type=float, default=0.5,
                        help="Confidence threshold (default: 0.5, matching the FP32 validation baseline)")
    parser.add_argument("--frame-rate", type=int, default=16,
                        help="Requested camera frame rate (default: 16)")
    parser.add_argument("--frames", type=int, default=0,
                        help="Stop after N frames (0 = run until Ctrl-C)")
    parser.add_argument("--no-display", action="store_true",
                        help="Headless: print per-frame counts + FPS instead of showing a window")
    args = parser.parse_args()

    # Pi/AI-Camera-only imports, kept out of module scope so `--help` works on a dev machine.
    from modlib.apps import Annotator
    from modlib.devices import AiCamera

    device = AiCamera(frame_rate=args.frame_rate)
    model = _build_model(args.model_dir)
    print(f"Deploying model to the IMX500 sensor (first upload takes a few seconds)…")
    device.deploy(model)                       # uploads the network firmware to the sensor
    annotator = Annotator()

    n = 0
    t0 = time.time()
    with device as stream:
        for frame in stream:
            detections = frame.detections[frame.detections.confidence > args.conf]
            n += 1

            if args.no_display:
                if n % args.frame_rate == 0:   # ~once per second
                    fps = n / (time.time() - t0)
                    print(f"frame {n}: {len(detections)} spine(s)  |  {fps:.1f} FPS")
            else:
                labels = [f"{model.labels[class_id]}: {score:0.2f}"
                          for _, score, class_id, _ in detections]
                annotator.annotate_boxes(frame, detections, labels=labels,
                                         alpha=0.3, corner_radius=10)
                frame.display()

            if args.frames and n >= args.frames:
                break

    fps = n / (time.time() - t0)
    print(f"\nDone: {n} frames, {fps:.1f} FPS average (on-sensor inference).")


if __name__ == "__main__":
    main()
