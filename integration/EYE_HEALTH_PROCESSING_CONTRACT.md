# MEtech Eye Health — processing integration contract (draft)

Status: **implementation work in an isolated GitHub branch; not connected to Lovable or production Edge Functions**.

## Research and owner separation

One uploaded eye photo is the common immutable input for Rady-4, Rady-6, DogDiseasePredictor and SAM 2.1. All run independently. Gemini is a separate synthesis run that consumes the original image, every available completed model result, segmentation outputs, prior same-eye photographs and relevant PRO references. Failures remain visible in research statuses; no output is fabricated.

**Architecture decision (2026-10-29): Gemini is the owner-facing image observation and education service.** A successful Gemini-only pass can create an owner report without waiting for Rady-4, Rady-6, DogDiseasePredictor, or SAM. The report must describe visible findings and uncertainty, not a diagnostic classification or unvalidated medical condition. If Gemini cannot confidently evaluate the image, display **Unclear / Needs Review** and an appropriate next action. Rady-4, Rady-6, DogDiseasePredictor, and SAM remain independent *research-only* services and never provide the customer-facing category. Gemini may later run a separately versioned research synthesis using the other model outputs; this must not retroactively overwrite an owner report.

## Supabase data contract (project: BLU Dog Platform)

The additive initial schema exists; **no live inference writer or upload adapter is wired yet**:

1. `eye_photos`: one photograph with `dog_id`, `eye_side` left/right/unknown, private bucket and path; optional legacy link.
2. `eye_model_runs`: one run per photograph/model/version/retry; `status` queued/processing/completed/failed/skipped; errors and provenance.
3. `eye_classifications`: one result for each classification model run, all scores and detection boxes; never reinterpret model scores as probabilities of diagnosis.
4. `eye_sam_measurements`: one measurement per name/region/run, numeric value (NULL when unavailable), unit, mask private location, formula/version and quality/assistance metadata.
5. `eye_gemini_assessments`: one structured synthesis per Gemini run; model agreement/disagreement, image comparability, visible findings, SAM observations, PRO links, separate owner/research summaries.
6. `eye_reference_assessments`: distinct independently reviewed reference findings; never silently use published image captions as clinical ground truth.
7. `eye_display_results`: immutable owner display snapshot. `gemini_assessment_id` references the owner-assessment source; `classifier_run_id` stays NULL for Gemini-owned reports. Store `source='gemini'`, report/prompt version, observation-only labels and quality metadata in `presented_payload` until a dedicated source column is migrated. Do not generate Rady-4 owner labels.

**Service-only writes for initial foundation:** RLS protects the two owner-readable tables by `can_view_dog(dog_id)`. Other research tables have no authenticated-user grants or policies. Processing must use a trusted authenticated backend with authorization; never embed service-role credentials in browsers, GitHub, or model prompts.

## Critical validation before integration

- Supabase composite foreign keys now enforce matching dog and photo relationships for model runs, Gemini source and display results. Validate all cross-record consistency in worker transactions as well, including `input_run_ids` array provenance.
- `eye_side='unknown'` exists to preserve legacy uploads. New reporting should require explicit side.
- Confirm actual source bucket and legacy storage paths per upload: the two private buckets `dog-pro-uploads` and `dog-media` exist; a bucket default is not proof of the storage location.
- Do not edit `eye_check_submissions` (six existing records at foundation creation) or replace active `process-eye-check`; preserve provenance and plan a reversible adapter.
- The Rady YOLO detector missed two out of eight example images, duplicated one detection and selected a nose in another. Crop validation and no-eye / multi-eye handling are required.
- Rady weights and SAM weights are **not included** in this repository. Confirm licenses, pinned revisions/checksums, hosting capability and reproducibility before inference deployment.
- The archived SAM targeted masks required manual boxes/points and selection. Automated prompts, segmentation QA and standardized photo capture remain unvalidated; store invalid/missing measurements, never substitute 0.
- SAM area ratio and equivalent-diameter ratio are mathematically related and should not be counted as independent evidence.
- Gemini outputs require a strict JSON schema, constrained observations, citation/reference IDs to input runs and photos, and limits on inference; do not put personal identifiers or public image URLs in prompts.
- Veterinary-confirmed ground truth is required for **accuracy** (sensitivity, specificity, false positives/negatives); model agreement is a separate research metric.

## Proposed processing order

```
private upload -> authorize dog access -> eye_photos
                                    -> Rady detector/crop -> Rady-4 run/classification
                                                          -> Rady-6 run/classification
                                    -> DogDiseasePredictor run/classification
                                    -> SAM run/measurements and quality
            -> complete/failed status for each branch
            -> Gemini model run/synthesis (accept partial inputs, record what's missing)
            -> validated, explicit owner display snapshot (Rady-4 only)
```

Use idempotency keyed to `(photo_id, model_name, model_version, processing_attempt)` at the worker boundary. A reprocess creates new runs and never mutates historical results. A partial failure cannot block all other outputs. If Gemini is unavailable, the owner can still access original photos and a properly gated Rady-4 result.

## Acceptance checks before release

- Each image references exactly one dog and one eye side; cross-dog references rejected.
- Re-run and retry do not create duplicate display records or overwrite historical model runs.
- Four classifiers/segmentation branches independently save success, failure or skipped states and provenance.
- Unit tests confirm all Rady class orders from `pipeline/model_runners.py` and class-score preservation.
- No original images or private signed URLs are in logs or client-side research payloads.
- Owner can only access their dog’s photo metadata and selected display result; research results cannot be read by a regular user.
- Ambiguous, missing-eye and multi-eye crops yield review, not forced diagnosis.
- SAM missing/invalid records remain NULL with quality flags.
- Gemini produces structured fields, declares model disagreements, and never asserts clinical accuracy from consensus.
- Legacy six eye submissions and current processing function remain unchanged until explicit cutover authorization.

## Source materials
- [Original model runners](../pipeline/model_runners.py)
- [Archived visual comparison and limitations](../SOURCES.md)
- [Original classifier pipeline](../pipeline/run_classifiers.py)

## Updated execution plan: parallel owner + research

```
authorized owner photo upload / photo history
    -> Gemini owner-analysis (image + same-eye prior photographs + relevant owner PROs)
          -> structured observations with explicit uncertainty and provenance
          -> immutable eye_display_results snapshot (classification-run = NULL)
    -> independent research queue (not blocking owner delivery)
          -> Rady-4, Rady-6, DogDiseasePredictor, SAM 2.1
          -> separately versioned Gemini research-synthesis assessment
          -> veterinary-reference evaluation (not proof by model agreement)
```

Owner output requires photo and history authorization, image quality gate, human-readable observation-based explanation, consistent reporting, urgent veterinary referral for concerning signs, and no unsupported diagnosis. No experimental research scores, SAM metrics or contradictory model classifications in the standard customer UI. Existing code that marks Rady-4 as a display candidate is **legacy draft code, superseded for owner display**; do not call it from the application. Keep it for historical test comparison, with deprecation annotations or tests before release.

Owner Gemini must work with zero external model runs; research synthesis explicitly expects available run IDs and reports missing models. Keep these purposes in separate prompt versions and run kinds. Preserve all existing tables and legacy Eye Check records, and keep the published app unchanged pending explicit release authorization.
