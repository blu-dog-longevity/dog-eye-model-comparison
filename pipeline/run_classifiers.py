import argparse
import json
from pathlib import Path

from PIL import Image

from model_runners import RADY4_CLASSES, RADY6_CLASSES
from model_runners import DogDiseaseRunner, RadyRunner, crop_eye


ROOT = Path(__file__).parent


def image_paths(input_dir: Path) -> list[Path]:
    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    return sorted(path for path in input_dir.iterdir() if path.suffix.lower() in extensions)


def run_rady(images: list[Path], output_dir: Path, model_name: str) -> list[dict]:
    model_path = ROOT / f"models/rady/{model_name}_efficientnet.pth"
    classes = RADY4_CLASSES if model_name == "rady4" else RADY6_CLASSES
    runner = RadyRunner(
        ROOT / "models/rady/yolo_eye_detection_best.pt", model_path, classes
    )
    rows = []
    for image_path in images:
        image = Image.open(image_path).convert("RGB")
        detections = runner.detect(image)
        if not detections:
            rows.append(
                {"image": image_path.name, "model": model_name, "status": "no_eye_detected"}
            )
            continue
        for index, detection in enumerate(detections, start=1):
            crop = crop_eye(image, detection["box"])
            crop_dir = output_dir / "crops" / image_path.stem
            crop_dir.mkdir(parents=True, exist_ok=True)
            crop_path = crop_dir / f"eye_{index}.jpg"
            crop.save(crop_path, quality=95)
            prediction = runner.classify(crop)
            rows.append(
                {
                    "image": image_path.name,
                    "eye": index,
                    "model": model_name,
                    "status": "ok",
                    "crop": str(crop_path.relative_to(output_dir)),
                    **detection,
                    **prediction,
                }
            )
    return rows


def run_dog_disease(images: list[Path]) -> list[dict]:
    runner = DogDiseaseRunner(ROOT / "models/dog_disease/best_model.pth")
    return [
        {
            "image": path.name,
            "model": "dog_disease_predictor",
            "status": "ok",
            **runner.classify(Image.open(path).convert("RGB")),
        }
        for path in images
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "data/images")
    parser.add_argument("--output", type=Path, default=ROOT / "runs/first-pass")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=["rady4", "rady6", "dog_disease_predictor"],
        default=["rady4", "rady6", "dog_disease_predictor"],
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    images = image_paths(args.input)
    results = []
    if "rady4" in args.models:
        results.extend(run_rady(images, args.output, "rady4"))
    if "rady6" in args.models:
        results.extend(run_rady(images, args.output, "rady6"))
    if "dog_disease_predictor" in args.models:
        results.extend(run_dog_disease(images))
    output = args.output / "results.json"
    output.write_text(json.dumps(results, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
