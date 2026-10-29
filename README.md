# BLU Dog eye model comparison

[Open the website](https://blu-dog-longevity.github.io/dog-eye-model-comparison/) · [Sources and image provenance](SOURCES.md) · [Excel results](pipeline/runs/report/model_outputs.xlsx)

The original August 26, 2026 visual comparison of Rady-4, Rady-6, DogDiseasePredictor, and targeted SAM 2.1 segmentation on eight public dog-eye photographs. Includes all saved inputs, predictions, crops, masks, prompt diagrams, CSVs, and the recovered analysis scripts.

This is an archived research prototype. Predictions and measurements are not clinically validated. There are no uploads, credentials, production records, or inference services on this website.

Image credits, individual licenses, model revisions, checkpoint checksums, manual interventions, and known limitations are in **[SOURCES.md](SOURCES.md)**. Derived image lineage is in [provenance/asset-lineage.json](provenance/asset-lineage.json); verify retained files with `sha256sum -c SHA256SUMS`.

Serve locally with `python -m http.server 8000`. GitHub Pages serves the repository root from `main`; no application build is required.
