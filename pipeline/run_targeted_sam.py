import json
import math
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor


ROOT = Path(__file__).parent
OUTPUT = ROOT / "runs/targeted-sam"
TRIALS = [
    {
        "id": "08_left_eye",
        "image": "08_iris_coloboma.png",
        "eye": "left",
        "status": "candidate",
        "roi": [125, 110, 455, 475],
        "pupil": {
            "box": [225, 195, 340, 365],
            "points": [[280, 260], [280, 330], [205, 270], [365, 270]],
            "labels": [1, 1, 0, 0],
            "candidate": 2,
        },
        "iris": {
            "box": [170, 165, 405, 415],
            "points": [[210, 285], [360, 285], [285, 360]],
            "labels": [1, 1, 1],
            "candidate": 3,
        },
    },
    {
        "id": "08_right_eye",
        "image": "08_iris_coloboma.png",
        "eye": "right",
        "status": "candidate",
        "roi": [1030, 100, 1370, 470],
        "pupil": {
            "box": [1115, 165, 1275, 325],
            "points": [[1190, 240], [1110, 245], [1290, 245], [1190, 345]],
            "labels": [1, 0, 0, 0],
            "candidate": 2,
        },
        "iris": {
            "box": [1095, 155, 1300, 365],
            "points": [[1125, 270], [1260, 270], [1190, 325]],
            "labels": [1, 1, 1],
            "candidate": 3,
        },
    },
    {
        "id": "02_dark_eye",
        "image": "02_dalmatian_eye.jpg",
        "eye": "single visible eye",
        "status": "failed_targeting",
        "reason": "The pupil and iris are too similar in contrast; both prompts select most of the exposed eye.",
        "roi": [150, 90, 510, 390],
        "pupil": {
            "box": [220, 160, 410, 320],
            "points": [[300, 225], [210, 235], [425, 235], [310, 335]],
            "labels": [1, 0, 0, 0],
            "candidate": 3,
        },
        "iris": {
            "box": [185, 135, 475, 350],
            "points": [[220, 245], [425, 245], [320, 315]],
            "labels": [1, 1, 1],
            "candidate": 3,
        },
    },
]


def predict_target(predictor: SAM2ImagePredictor, prompt: dict) -> tuple[np.ndarray, dict]:
    masks, scores, _ = predictor.predict(
        point_coords=np.asarray(prompt["points"], dtype=np.float32),
        point_labels=np.asarray(prompt["labels"], dtype=np.int32),
        box=np.asarray(prompt["box"], dtype=np.float32),
        multimask_output=True,
    )
    index = prompt["candidate"] - 1
    return masks[index].astype(bool), {
        "box": prompt["box"],
        "points": prompt["points"],
        "labels": prompt["labels"],
        "selected_candidate": prompt["candidate"],
        "selected_score": round(float(scores[index]), 6),
        "candidate_scores": [round(float(score), 6) for score in scores],
    }


def shape_asymmetry(mask: np.ndarray) -> float:
    ys, xs = np.where(mask)
    crop = mask[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    mirrored = np.fliplr(crop)
    union = np.logical_or(crop, mirrored).sum()
    overlap = np.logical_and(crop, mirrored).sum()
    return round(float(1 - overlap / union), 6)


def metrics(image: Image.Image, pupil: np.ndarray, iris_disk: np.ndarray) -> dict:
    pupil = np.logical_and(pupil, iris_disk)
    iris_ring = np.logical_and(iris_disk, ~pupil)
    pupil_area = int(pupil.sum())
    iris_area = int(iris_disk.sum())
    area_ratio = pupil_area / iris_area
    pupil_center = np.argwhere(pupil).mean(axis=0)
    iris_center = np.argwhere(iris_disk).mean(axis=0)
    iris_radius = math.sqrt(iris_area / math.pi)
    iris_pixels = np.asarray(image)[iris_ring].astype(np.float32)
    iris_hsv = np.asarray(image.convert("HSV"))[iris_ring].astype(np.float32)
    return {
        "pupil_area_px": pupil_area,
        "iris_disk_area_px": iris_area,
        "pupil_iris_area_ratio": round(float(area_ratio), 6),
        "pupil_iris_equivalent_diameter_ratio": round(float(math.sqrt(area_ratio)), 6),
        "pupil_shape_asymmetry": shape_asymmetry(pupil),
        "pupil_center_offset_iris_radius": round(
            float(np.linalg.norm(pupil_center - iris_center) / iris_radius), 6
        ),
        "iris_mean_red": round(float(iris_pixels[:, 0].mean()), 3),
        "iris_mean_green": round(float(iris_pixels[:, 1].mean()), 3),
        "iris_mean_blue": round(float(iris_pixels[:, 2].mean()), 3),
        "iris_mean_saturation": round(float(iris_hsv[:, 1].mean() / 255), 6),
    }


def draw_prompts(image: Image.Image, trial: dict) -> Image.Image:
    view = image.copy()
    draw = ImageDraw.Draw(view)
    for target, color in [("pupil", (220, 0, 130)), ("iris", (0, 170, 220))]:
        prompt = trial[target]
        draw.rectangle(prompt["box"], outline=color, width=3)
        for (x, y), label in zip(prompt["points"], prompt["labels"]):
            point_color = color if label else (235, 55, 60)
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=point_color, outline="white", width=2)
    return view


def save_views(
    image: Image.Image,
    trial: dict,
    pupil: np.ndarray,
    iris_disk: np.ndarray,
) -> dict[str, str]:
    array = np.asarray(image).copy()
    iris_ring = np.logical_and(iris_disk, ~pupil)
    overlap = np.logical_and(pupil, iris_disk)
    overlay = array.astype(np.float32)
    overlay[iris_ring] = overlay[iris_ring] * 0.45 + np.array([0, 185, 220]) * 0.55
    overlay[pupil] = overlay[pupil] * 0.45 + np.array([220, 0, 130]) * 0.55
    if trial["status"] == "failed_targeting":
        overlay[overlap] = overlay[overlap] * 0.4 + np.array([245, 170, 0]) * 0.6

    mask_view = np.zeros_like(array)
    mask_view[iris_ring] = [0, 185, 220]
    mask_view[pupil] = [220, 0, 130]
    if trial["status"] == "failed_targeting":
        mask_view[overlap] = [245, 170, 0]

    roi = tuple(trial["roi"])
    paths = {
        "prompt_view": OUTPUT / f"{trial['id']}_prompts.jpg",
        "overlay": OUTPUT / f"{trial['id']}_overlay.jpg",
        "mask_view": OUTPUT / f"{trial['id']}_masks.png",
    }
    draw_prompts(image, trial).crop(roi).save(paths["prompt_view"], quality=92)
    Image.fromarray(overlay.astype(np.uint8)).crop(roi).save(paths["overlay"], quality=92)
    Image.fromarray(mask_view).crop(roi).save(paths["mask_view"])
    return {key: str(path.relative_to(ROOT)) for key, path in paths.items()}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    model = build_sam2(
        "configs/sam2.1/sam2.1_hiera_t.yaml",
        ROOT / "models/sam2/sam2.1_hiera_tiny.pt",
        device="cpu",
        apply_postprocessing=False,
    )
    predictor = SAM2ImagePredictor(model)
    rows = []
    current_image = None

    with torch.inference_mode():
        for trial in TRIALS:
            if trial["image"] != current_image:
                image = Image.open(ROOT / "data/images" / trial["image"]).convert("RGB")
                predictor.set_image(np.asarray(image).copy())
                current_image = trial["image"]
            pupil, pupil_prompt = predict_target(predictor, trial["pupil"])
            iris_disk, iris_prompt = predict_target(predictor, trial["iris"])
            row = {
                "id": trial["id"],
                "image": trial["image"],
                "eye": trial["eye"],
                "status": trial["status"],
                "reason": trial.get("reason", ""),
                "pupil_prompt": pupil_prompt,
                "iris_prompt": iris_prompt,
                **save_views(image, trial, pupil, iris_disk),
            }
            if trial["status"] == "candidate":
                row.update(metrics(image, pupil, iris_disk))
            rows.append(row)

    output = OUTPUT / "results.json"
    output.write_text(json.dumps(rows, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
