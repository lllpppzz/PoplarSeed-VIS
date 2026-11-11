# PoplarSeed-VIS

## Download and reproduce

- [Complete dataset and analysis package](Supplementary_Data_S1.zip) with images, masks, descriptors, exact splits and code.
- [SHA256 checksum](Supplementary_Data_S1.sha256).
- [Browse the analysis code](reanalysis/code) and [metadata and data splits](reanalysis/data).
- [Original archive](date.zip), preserved unchanged.

For a self-contained run, unpack Supplementary_Data_S1.zip and follow its README. The browsable reanalysis directory provides the same scripts and numeric records; image and mask payloads are in the complete package.


We provide PoplarSeed-VIS for individual-seed phenotyping and identification of poplar seed materials. Our dataset contains **2,426 RGB images**, covering **seven materials**, **13 harvest batches** and **four source regions**. Each image is linked to a foreground mask, phenotype measurements and a fixed training/test assignment.

## Dataset composition

| Region | Material | Images | Harvest batches |
|---|---|---:|---:|
| North China | SHANXI QZ | 378 | 2 |
| North China | SHANXI XY | 390 | 2 |
| Central China | HENAN ZL | 388 | 2 |
| East China | NJFU 895 | 781 | 4 |
| Northeast China | LIAON LHY | 192 | 1 |
| Northeast China | LIAON MZHY | 150 | 1 |
| Northeast China | LIAON XQY | 147 | 1 |
| Total | 7 materials | 2,426 | 13 |

The TIFF images are 230 × 230 pixels, with a standardized image scale of **20 μm/pixel** in both directions. The original `date.zip` contains 2,426 images and 80 TXT measurement reports, giving 2,506 files in total. The TXT files are separate from the image dataset.

We organize the images by region, material and harvest batch. Folder suffixes distinguish seed harvest dates within a cultivar. The four NJFU 895 folders are harvest batches of the same cultivar. For materials with multiple batches, harvests were separated by several days; `-1` denotes an earlier harvest. Exact dates and numerical day intervals are not supplied. The canonical image folders assign Shanxi to North China and Henan to Central China. We retain the original archive paths and file hashes in `data/image_manifest.csv` so that each image can be traced across the two folder structures.

## Files and records

- `images/`: 2,426 original TIFF images under the canonical region folders.
- `masks/`: one automatically extracted binary PNG mask per image.
- `data/batch_metadata.csv`: harvest-batch definitions and available relative timing.
- `data/image_manifest.csv`: image identifiers, material, harvest batch, region, paths, SHA256 hashes and training/test membership.
- `data/seed_features.csv`: per-image phenotype measurements, including all 92 classification descriptors.
- `data/feature_dictionary.csv`: descriptor definitions and units.
- `data/feature_groups.json` and `data/analysis_feature_sets.json`: input columns for individual, combined and reduced descriptor groups.
- `data/tuning_cv_fold_manifest.csv`: five validation folds drawn exclusively from the training set.
- `data/training_cv_folds.csv` and `data/fixed_training_cv_predictions.csv`: archived fixed-benchmark fold membership and out-of-fold predictions. These folds are distinct from the parameter-selection folds.
- `data/primary_predictions.csv` and `data/batch_context_predictions.csv.gz`: image-level predictions.
- `tables/`: descriptive statistics, resampling intervals, parameter-search results, retraining comparisons and harvest-batch outcomes.
- `code/`: executable image processing, statistical analysis, SVM classification and plotting scripts.
- `reference/tables/`: saved fixed-model benchmark tables for checking numerical reproduction.
- `legacy_reports/`: the 80 archived TXT measurement reports with the suffix `LWACstats`.
- `audit/`: file inventories and numerical verification records.
- `SHA256SUMS.txt`: SHA256 hashes for the package files.

We compute the current masks and descriptors directly from TIFF pixels. The archived TXT reports are retained as accompanying records and are not used as classification inputs.

## Phenotypes and image processing

We extract 11 morphological descriptors, 57 HSV color descriptors and 24 texture descriptors. Morphology includes length, width, area, perimeter and outline-shape measurements. Color combines pixel-level HSV summaries and normalized histograms. Texture uses grey-level co-occurrence matrices and local binary patterns.

Foreground selection uses a maximum-channel difference greater than 8 from the estimated grey background. Border-connected and small components are excluded; the largest remaining component is retained and enclosed holes are filled. The exact settings and measurement definitions are supplied in the code and feature dictionary.

## Reproduce the analysis

We used Python 3.12 with the dependency versions listed in `requirements.txt`. Unpack the complete package, open its directory and run:

```
python -m pip install -r requirements.txt
python code/extract_features.py
python code/cluster_analysis.py
python code/classification_revision.py
python code/make_revision_figures.py
```

The fixed allocation contains 1,940 training images and 486 test images. All descriptor comparisons use these same records. Fixed RBF SVMs use `C=50` and `gamma='scale'`. We reproduce fixed-benchmark cross-validation on its archived folds and provide the metrics and individual predictions. Parameter selection uses a separate allocation of five training-only folds, with standardization refitted within each fold and macro-F1 as the selection criterion. The saved test set is shared by the fixed, tuned and reduced-feature comparisons. Parameter tuning applies to the seven-material comparisons; the paired four-material harvest-batch benchmark retains fixed SVM settings.

We supply 2,000 hierarchical resamples and 1,000 block permutations per descriptor group. Resampling selects harvest batches within each material, followed by images within the selected groups. We also evaluate the four materials with multiple harvest batches using 32 overlapping holdout configurations and summarize the ten distinct held-out groups separately.

## Interpretation of the records

Each material label combines a variety name and its recorded source. Variety and source effects cannot be separated in this collection. Batch identifiers refer to different seed harvest dates within each material. Mother-tree membership and batch-specific storage logs are unavailable, so harvest batches do not establish independent mother-tree replication. The three LIAON materials each have one group, so their resampling intervals remain conditional on that observed group. The 32 holdout configurations share batches and are not independent biological replicates. They evaluate transfer in both temporal directions, not prospective early-to-late prediction alone.

## Version and use

We provide these files for academic and non-commercial research use under the conditions in `LICENSE.txt`.

- Package version: `revision-2026-11-11-v4`.
- Original archive commit: `190fbe59b25a12b5f4428e2e5869f9272b42da79`.
- Original `date.zip` SHA256: `eef9ae00c5efb338121cddadfff70641e9d9aa3d65d00537b25ea4d1c7f7489d`.
- The complete package SHA256 is provided in `Supplementary_Data_S1.sha256` alongside the ZIP.

The original image archive remains unchanged. Version identifiers, manifests and checksums support reproducible use of the dataset.
