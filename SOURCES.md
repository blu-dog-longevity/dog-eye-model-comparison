# Sources and provenance — BLU Dog eye model comparison

This is the archived August 26, 2026 comparison of existing models on eight public canine-eye photographs. The website publishes the saved results; it does not run inference or accept uploads. Source descriptions and model predictions are not veterinary ground truth.

## Models and roles

| Name | Input and role | Original publisher source |
| --- | --- | --- |
| Rady YOLO detector | Whole photograph → eye boxes. Shared by both Rady classifiers; confidence threshold 0.25. | [Pinned source](https://huggingface.co/spaces/abdelrahmanrady/dog-eye-diagnosis-AI/blob/7f02c10e6a2bd916dd109fbd85ac28c2daa65e88/app.py) |
| Rady-4 | Detected eye crop → EfficientNet-B3 with GeM pooling and squeeze/excitation; cataract, cherry eye, iris atrophy, healthy. | [Pinned source](https://huggingface.co/spaces/abdelrahmanrady/dog-eye-diagnosis-AI/blob/7f02c10e6a2bd916dd109fbd85ac28c2daa65e88/app.py) |
| Rady-6 | Same detector → separate six-output EfficientNet classifier; adds conjunctivitis and glaucoma. Class order is retained in the runner. | [Pinned source](https://huggingface.co/spaces/abdelrahmanrady/AI-Eye-Dog/blob/de6a686e89122722f9f4ab5030fa3e2c1b9e670a/app.py) |
| DogDiseasePredictor | Whole photograph → ViT, 20 mixed canine labels. Cherry eye and nuclear sclerosis are the two eye-specific labels. | [Pinned source](https://huggingface.co/spaces/AnishKumbhar/DogDiseasePredictor/blob/d1f3905a61644a888faadd0657f4d1b158efb755/app.py) |
| SAM 2.1 Hiera Tiny | Boxes and/or positive/negative points → masks. No disease classification. | [Meta source at the recorded revision](https://github.com/facebookresearch/sam2/tree/2b90b9f5ceec907a1c18123530e92e794ad901a4) |
| DogEyeSeg4 (not run) | A separate 145-image research dataset with masks; not a classifier used in this comparison. | [Burić et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11467576/) |

The recovered [model runner](pipeline/model_runners.py), [classifier driver](pipeline/run_classifiers.py), and [dependency list](pipeline/requirements.txt) preserve the implementation. Rady crops use 15% padding, resize to 224 × 224, and ImageNet normalization. DogDiseasePredictor receives the whole image resized to 224 × 224. Scores are model outputs, not calibrated probabilities of disease.

### Checkpoint identities

These URLs and expected SHA-256 values come from the original fetch script. Model weight files are not redistributed here. The publication did not redownload or rerun them; these are recorded expectations, not a new weight audit. Upstream code and weights retain their own terms; availability on Hugging Face is not a blanket reuse license.

- **models/rady/yolo_eye_detection_best.pt**: [pinned download](https://huggingface.co/spaces/abdelrahmanrady/dog-eye-diagnosis-AI/resolve/7f02c10e6a2bd916dd109fbd85ac28c2daa65e88/yolo_eye_detection_best.pt); SHA-256 `e5c9f8223d12c878692ca470a18490920ec27bb3515dcaaf9fe49ab6e4fae6af`.
- **models/rady/rady4_efficientnet.pth**: [pinned download](https://huggingface.co/spaces/abdelrahmanrady/dog-eye-diagnosis-AI/resolve/7f02c10e6a2bd916dd109fbd85ac28c2daa65e88/efficientnet_b3_se_gem_best.pth); SHA-256 `52abe206513ef94d40d4421dc29b2cb1d970db7ed78d438aa3ce89ff5236949c`.
- **models/rady/rady6_efficientnet.pth**: [pinned download](https://huggingface.co/spaces/abdelrahmanrady/AI-Eye-Dog/resolve/de6a686e89122722f9f4ab5030fa3e2c1b9e670a/efficientnet_b3_se_gem_best.pth); SHA-256 `a22d8ad31e89ddd6b5a6eb878317631253c81e4f0375dcfc13582b0928a0f2d8`.
- **models/dog_disease/best_model.pth**: [pinned download](https://huggingface.co/spaces/AnishKumbhar/DogDiseasePredictor/resolve/d1f3905a61644a888faadd0657f4d1b158efb755/best_model.pth); SHA-256 `214824b66bb9988b90dc3e699fcbbf37e5ab05b85657bfae45389b452e6dfd89`.
- **models/sam2/sam2.1_hiera_tiny.pt**: [pinned download](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt); SHA-256 `7402e0d864fa82708a20fbd15bc84245c2f26dff0eb43a4b5b93452deb34be69`.

## Image credits and licenses

All eight inputs are public Wikimedia Commons files. The original [sources.json](pipeline/sources.json) is preserved unchanged. Creator and license fields were checked against the Commons API on October 29, 2026; the [metadata response](provenance/wikimedia-metadata.json) is retained. Titles below link to the file pages, which provide the full source and licensing notices.

BLU Dog generated eye crops, yellow detection boxes, segmentation masks, transparent cutouts, colored overlays, and prompt diagrams from these inputs. Those changes are analytical annotations, not changes to the original source photographs. Adaptations of CC BY-SA images are offered under the same respective CC BY-SA license shown below; attribution to the original photographer remains required. Public-domain originals remain public domain. No photographer endorses these predictions.

### 01_dog_eye_macro.jpg

- **Source:** [Close-up dog eye](https://commons.wikimedia.org/wiki/File:Dog_eye_makro.jpg).
- **Creator:** Christian Pietzsch. **License:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- **Recorded download:** [Wikimedia image URL](https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Dog_eye_makro.jpg/1920px-Dog_eye_makro.jpg).
- **Retained input:** [image](pipeline/data/images/01_dog_eye_macro.jpg), 1920 × 1284 pixels, 333,263 bytes.
- **SHA-256:** `6ad8ded208ac45fec39db35239f4852dc9b6dc313e3a19922bd22c9e3e4c5a35`.

### 02_dalmatian_eye.jpg

- **Source:** [Close-up Dalmatian eye](https://commons.wikimedia.org/wiki/File:Oko_dalmaty%C5%84czyka.JPG).
- **Creator:** Olaf. **License:** [Public domain](https://commons.wikimedia.org/wiki/File:Oko_dalmaty%C5%84czyka.JPG).
- **Recorded download:** [Wikimedia image URL](https://upload.wikimedia.org/wikipedia/commons/f/fa/Oko_dalmaty%C5%84czyka.JPG).
- **Retained input:** [image](pipeline/data/images/02_dalmatian_eye.jpg), 640 × 480 pixels, 64,202 bytes.
- **SHA-256:** `fd0a5a3b0ad1bcc9b836b0709182a9c74fa8693af8e3936d35c32d3ad7027382`.

### 03_cataract_labrador.jpg

- **Source:** [Described by source as cataract in a Labrador](https://commons.wikimedia.org/wiki/File:Cataract_in_labrador.jpg).
- **Creator:** Nithin1111991. **License:** [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
- **Recorded download:** [Wikimedia image URL](https://upload.wikimedia.org/wikipedia/commons/8/84/Cataract_in_labrador.jpg).
- **Retained input:** [image](pipeline/data/images/03_cataract_labrador.jpg), 459 × 378 pixels, 25,333 bytes.
- **SHA-256:** `942bb28224bc8b16758045f1730b66cff9d375c64654d923cac112aee087d055`.

### 04_cataract_dog.jpg

- **Source:** [Described by source as a dog with cataract](https://commons.wikimedia.org/wiki/File:C%C3%A3o_com_catarata.jpg).
- **Creator:** André Koehne. **License:** [Public domain](https://commons.wikimedia.org/wiki/File:C%C3%A3o_com_catarata.jpg).
- **Recorded download:** [Wikimedia image URL](https://upload.wikimedia.org/wikipedia/commons/e/e5/C%C3%A3o_com_catarata.jpg).
- **Retained input:** [image](pipeline/data/images/04_cataract_dog.jpg), 1719 × 1823 pixels, 470,586 bytes.
- **SHA-256:** `693dd58d9201c0ac285367ab29b5ac3bd7ff1c9c8ae0494cfae1f0068a2f238c`.

### 05_cherry_eye.jpg

- **Source:** [Described by source as a Beagle-Cocker Spaniel mix with cherry eye](https://commons.wikimedia.org/wiki/File:Beagle%E2%80%93Cocker_Spaniel_Mix_with_cherry_eye.jpg).
- **Creator:** Tcr25. **License:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- **Recorded download:** [Wikimedia image URL](https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Beagle%E2%80%93Cocker_Spaniel_Mix_with_cherry_eye.jpg/1920px-Beagle%E2%80%93Cocker_Spaniel_Mix_with_cherry_eye.jpg).
- **Retained input:** [image](pipeline/data/images/05_cherry_eye.jpg), 1920 × 1080 pixels, 580,871 bytes.
- **SHA-256:** `8832edbe1de0e271b2a4af10e459e7f97cf7eb98ee48f38bf8cdf489ce758aa0`.

### 06_prolapsed_third_eyelid.jpg

- **Source:** [Described by source as a prolapsed gland of the third eyelid](https://commons.wikimedia.org/wiki/File:Prolapsed_gland_of_the_third_eyelid.JPG).
- **Creator:** Joel Mills. **License:** [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
- **Recorded download:** [Wikimedia image URL](https://upload.wikimedia.org/wikipedia/commons/7/77/Prolapsed_gland_of_the_third_eyelid.JPG).
- **Retained input:** [image](pipeline/data/images/06_prolapsed_third_eyelid.jpg), 1849 × 1317 pixels, 435,149 bytes.
- **SHA-256:** `c0d9987ea397d5fa0ab6e44a65e251ee67feddf53a838131edda7aa9880f9f1b`.

### 07_affected_nictitating_membrane.jpg

- **Source:** [Described by source as an affected nictitating membrane](https://commons.wikimedia.org/wiki/File:Affected_nicitating_membrane.jpg).
- **Creator:** Edward Morgan. **License:** [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/).
- **Recorded download:** [Wikimedia image URL](https://upload.wikimedia.org/wikipedia/commons/e/e2/Affected_nicitating_membrane.jpg).
- **Retained input:** [image](pipeline/data/images/07_affected_nictitating_membrane.jpg), 1593 × 2390 pixels, 1,379,724 bytes.
- **SHA-256:** `f25dc89e8ec327b989d31e562af615369068568356a226f8a7c3cf6258e0ed75`.

### 08_iris_coloboma.png

- **Source:** [Described by source as a left iris coloboma in a Border Collie](https://commons.wikimedia.org/wiki/File:Left_iris_coloboma_in_border_collie.png).
- **Creator:** Timdwilliamson. **License:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- **Recorded download:** [Wikimedia image URL](https://upload.wikimedia.org/wikipedia/commons/b/b3/Left_iris_coloboma_in_border_collie.png).
- **Retained input:** [image](pipeline/data/images/08_iris_coloboma.png), 1493 × 568 pixels, 1,368,965 bytes.
- **SHA-256:** `ccfb41a29a8c9e56e34adf1668ca1c81708d8ad0a20dad5df820575dae24d120`.

## How the outputs were produced

1. The same eight photographs were supplied to Rady-4, Rady-6, and DogDiseasePredictor. The Rady detector produced nine crop rows per classifier; two additional image rows record detector misses, for 11 rows per Rady sheet. DogDiseasePredictor has eight whole-image rows.
2. The first SAM pass used the Rady boxes plus manually supplied boxes for the two detector misses. Its 11 masks and descriptors are retained in [SAM results](pipeline/runs/sam2/metrics.json), [CSV](pipeline/runs/report/csv/sam2_metrics.csv), and the workbook. This pass is not a visible tab in the final August report.
3. The targeted SAM pass used manual boxes, positive/negative clicks, and manually selected mask candidates for two eyes in the coloboma image and one dark Dalmatian eye. Exact coordinates and candidate choices are in [run_targeted_sam.py](pipeline/run_targeted_sam.py) and [results.json](pipeline/runs/targeted-sam/results.json). The dark-eye attempt failed to separate pupil from iris, so its pupil/iris metrics were withheld.
4. The report uses saved classifier JSON, saved SAM JSON, and the images. It does not infer new labels when opened. [build_report.py](pipeline/build_report.py) generates the tabbed HTML, CSVs, workbook, and detection-box illustrations.

The targeted area ratio is pupil-mask area divided by iris-disk-mask area after intersecting the pupil with the iris disk. The equivalent-diameter ratio is the square root of that ratio. Shape asymmetry compares a mask with its horizontal reflection. Center offset is normalized by the equivalent iris radius. Color descriptors depend on illumination and camera settings. These quantities are exploratory pixel measurements, not validated clinical measurements. Exact formulas are in [run_sam_metrics.py](pipeline/run_sam_metrics.py) and [run_targeted_sam.py](pipeline/run_targeted_sam.py).

## Known limitations visible in the original results

- The Rady detector misses two input images, duplicates the visible Dalmatian eye, and detects the nose in another image. The report preserves these cases and marks the duplicate and nose detection.
- The two Rady classifiers disagree on some crops. Their predictions and confidence scores are retained as produced.
- DogDiseasePredictor gives diffuse scores on this set and frequently selects a non-eye class. No diagnostic accuracy estimate follows from these examples.
- SAM candidate selection was manual for the targeted examples. The saved ratios are not automated ground truth or evidence of disease.
- Eight selected public images do not form an independently labeled clinical benchmark. No sensitivity, specificity, Dice score against expert masks, or external validation was established here.

## Archive history and reproducibility

The original classifier source and image manifest were recovered from Git commit `d7a2a3cb35939a8a0139b423a3f0f06fbac02d24` of `blu-dog-longevity/blu-dog-longevity`, under `prototypes/canine-eye-pipeline/`. Later SAM and report-builder changes were recovered from the recorded August 26 editing session. The saved images and result files survived in the local prototype archive. Private session transcripts and unrelated platform files are not part of this public package.

Before adding publication links, running the recovered builder against the saved results reproduced the original report HTML byte for byte. The [original HTML checksum](provenance/original-report.sha256) records that comparison target. Publication changes add navigation, image credits, and this source record; the model outputs are unchanged. The archived workbook is retained byte for byte. No model inference was rerun for publication.

[SHA256SUMS](SHA256SUMS) identifies the published source files, inputs, raw results, derived images, and downloads. [asset-lineage.json](provenance/asset-lineage.json) maps every published image asset to its input photograph, transformation, creator, and license. Hashes identify these retained bytes; they do not establish veterinary ground truth.

For a local static preview, run `python -m http.server 8000` from the repository root. To regenerate the presentation from saved outputs, install Pillow and openpyxl and run `python pipeline/build_report.py`. No model downloads are required for that step. Full inference instructions and the historical dependency pins are in [pipeline/README.md](pipeline/README.md). The historical dependency list is not a complete environment lock; exact inference reproducibility on a fresh machine has not been revalidated.

## Files to inspect

- [Classifier predictions and detector boxes](pipeline/runs/first-pass/results.json)
- [SAM mask descriptors](pipeline/runs/sam2/metrics.json)
- [Targeted SAM prompts, candidate scores, and measurements](pipeline/runs/targeted-sam/results.json)
- [Excel workbook](pipeline/runs/report/model_outputs.xlsx)
- [Image source manifest](pipeline/sources.json)
- [Checkpoint manifest](provenance/models.json)
- [Implementation](pipeline/README.md)
