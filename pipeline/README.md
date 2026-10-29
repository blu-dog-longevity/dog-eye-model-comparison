# Canine eye pipeline prototype

**Question:** Can one staged image set expose the behavior of the public classifiers and a first segmentation/measurement pass?

**Audience:** Logan and BLU's research team.

This is an isolated research prototype. It does not use production uploads and its outputs are not diagnoses.

## What each name means

- `rady4`: Rady's YOLO eye cropper followed by a four-output EfficientNet classifier: cataract, cherry eye, iris atrophy, healthy.
- `rady6`: the same YOLO checkpoint followed by a separate six-output EfficientNet classifier that adds conjunctivitis and glaucoma.
- `dog_disease_predictor`: a separate whole-image ViT with 20 mixed canine labels. Only cherry eye and nuclear sclerosis are eye-specific.
- `DogEyeSeg4`: not used here. It is a separate 145-image research dataset containing masks for four visible findings; no reusable trained model was located.
- `SAM 2.1`: uses each Rady eye box as a prompt, plus manual boxes for the two detector misses, then calculates rough visual descriptors from each mask.

## Run

```bash
uv venv --system-site-packages
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python fetch_assets.py
.venv/bin/python run_classifiers.py
.venv/bin/python run_sam_metrics.py
.venv/bin/python run_targeted_sam.py
.venv/bin/python build_report.py
```

Open `runs/report/index.html` for the tabbed visual report. `runs/report/model_outputs.xlsx` contains separate Rady-4, Rady-6, DogDisease, SAM2-Metrics, and Targeted-SAM sheets; the same tables are also exported individually under `runs/report/csv/`.

Inputs land in `data/images/`, pinned model files in `models/`, classifier results and crops in `runs/first-pass/`, and segmentation outputs in `runs/sam2/`. Generated assets are ignored by Git.

The staged images are public Wikimedia files with attribution recorded in `sources.json`. Their page descriptions are useful for behavior checks, not veterinary ground truth.

The targeted SAM tab uses manual pupil/iris prompts on one clear and one difficult image. Its selected masks and ratios are feasibility evidence—not clinical measurements or an automated pipeline.
