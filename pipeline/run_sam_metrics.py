import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor


ROOT = Path(__file__).parent
MANUAL_PROMPTS = {
    "05_cherry_eye.jpg": [[650, 285, 820, 420]],
    "06_prolapsed_third_eyelid.jpg": [[520, 470, 1330, 970]],
}


def prompts_by_image(results: list[dict]) -> dict[str, list[dict]]:
    prompts = {}
    for row in results:
        if row["model"] != "rady4":
            continue
        if row["status"] == "ok":
            prompts.setdefault(row["image"], []).append(
                {"eye": row["eye"], "box": row["box"], "source": "rady_yolo"}
            )
    for image, boxes in MANUAL_PROMPTS.items():
        prompts[image] = [
            {"eye": index, "box": box, "source": "manual_box"}
            for index, box in enumerate(boxes, start=1)
        ]
    return prompts


def mask_metrics(image: np.ndarray, mask: np.ndarray, box: list[float]) -> dict:
    height, width = mask.shape
    x1, y1, x2, y2 = box
    x1 = max(0, int(x1))
    y1 = max(0, int(y1))
    x2 = min(width, int(x2))
    y2 = min(height, int(y2))
    ys, xs = np.where(mask)
    mx1, mx2 = int(xs.min()), int(xs.max()) + 1
    my1, my2 = int(ys.min()), int(ys.max()) + 1

    pixels = image[mask].astype(np.float32)
    hsv = np.asarray(Image.fromarray(image).convert("HSV"))[mask].astype(np.float32)
    mask_crop = mask[my1:my2, mx1:mx2]
    flipped_mask = np.fliplr(mask_crop)
    union = np.logical_or(mask_crop, flipped_mask).sum()
    overlap = np.logical_and(mask_crop, flipped_mask).sum()

    rgb_crop = image[my1:my2, mx1:mx2].astype(np.float32) / 255.0
    paired = np.logical_and(mask_crop, flipped_mask)
    mirrored_rgb = np.fliplr(rgb_crop)

    return {
        "mask_area_px": int(mask.sum()),
        "mask_area_ratio": round(float(mask.sum() / ((x2 - x1) * (y2 - y1))), 6),
        "width_height_ratio": round(float((mx2 - mx1) / (my2 - my1)), 6),
        "mean_red": round(float(pixels[:, 0].mean()), 3),
        "mean_green": round(float(pixels[:, 1].mean()), 3),
        "mean_blue": round(float(pixels[:, 2].mean()), 3),
        "redness_index": round(
            float((pixels[:, 0] - (pixels[:, 1] + pixels[:, 2]) / 2).mean() / 255),
            6,
        ),
        "mean_saturation": round(float(hsv[:, 1].mean() / 255), 6),
        "mean_brightness": round(float(hsv[:, 2].mean() / 255), 6),
        "dark_pixel_ratio": round(float((hsv[:, 2] < 64).mean()), 6),
        "bright_low_saturation_ratio": round(
            float(np.logical_and(hsv[:, 2] > 160, hsv[:, 1] < 64).mean()), 6
        ),
        "shape_asymmetry": round(float(1 - overlap / union), 6),
        "color_asymmetry": round(
            float(np.abs(rgb_crop - mirrored_rgb)[paired].mean()), 6
        ),
    }


def save_images(
    image: Image.Image,
    mask: np.ndarray,
    box: list[float],
    output_dir: Path,
    stem: str,
) -> dict[str, str]:
    image_array = np.asarray(image)
    overlay = image_array.astype(np.float32)
    overlay[mask] = overlay[mask] * 0.55 + np.array([0, 190, 170]) * 0.45
    overlay_image = Image.fromarray(overlay.astype(np.uint8))
    draw = ImageDraw.Draw(overlay_image)
    draw.rectangle(box, outline=(255, 196, 0), width=max(2, image.width // 500))

    ys, xs = np.where(mask)
    x1, x2 = int(xs.min()), int(xs.max()) + 1
    y1, y2 = int(ys.min()), int(ys.max()) + 1
    segment = image.crop((x1, y1, x2, y2)).convert("RGBA")
    segment.putalpha(Image.fromarray((mask[y1:y2, x1:x2] * 255).astype(np.uint8)))

    overlay_path = output_dir / f"{stem}_overlay.jpg"
    segment_path = output_dir / f"{stem}_segment.png"
    mask_path = output_dir / f"{stem}_mask.png"
    overlay_image.save(overlay_path, quality=90)
    segment.save(segment_path)
    Image.fromarray((mask * 255).astype(np.uint8)).save(mask_path)
    return {
        "overlay": str(overlay_path.relative_to(ROOT)),
        "segment": str(segment_path.relative_to(ROOT)),
        "mask": str(mask_path.relative_to(ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results", type=Path, default=ROOT / "runs/first-pass/results.json"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "runs/sam2")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    results = json.loads(args.results.read_text())
    prompts = prompts_by_image(results)
    image_names = sorted(prompts)
    if args.limit:
        image_names = image_names[: args.limit]

    model = build_sam2(
        "configs/sam2.1/sam2.1_hiera_t.yaml",
        ROOT / "models/sam2/sam2.1_hiera_tiny.pt",
        device="cpu",
        apply_postprocessing=False,
    )
    predictor = SAM2ImagePredictor(model)
    rows = []
    args.output.mkdir(parents=True, exist_ok=True)

    with torch.inference_mode():
        for image_name in image_names:
            image = Image.open(ROOT / "data/images" / image_name).convert("RGB")
            image_array = np.asarray(image).copy()
            predictor.set_image(image_array)
            for prompt in prompts[image_name]:
                box = np.asarray(prompt["box"], dtype=np.float32)
                masks, scores, _ = predictor.predict(
                    box=box[None, :], multimask_output=False
                )
                mask = masks[0].astype(bool)
                stem = f"{Path(image_name).stem}_eye_{prompt['eye']}"
                paths = save_images(image, mask, prompt["box"], args.output, stem)
                rows.append(
                    {
                        "image": image_name,
                        "eye": prompt["eye"],
                        "prompt_source": prompt["source"],
                        "box": [round(float(value), 3) for value in prompt["box"]],
                        "sam_score": round(float(scores[0]), 6),
                        **mask_metrics(image_array, mask, prompt["box"]),
                        **paths,
                    }
                )

    output = args.output / "metrics.json"
    output.write_text(json.dumps(rows, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
