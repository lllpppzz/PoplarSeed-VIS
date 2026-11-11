# PoplarSeed-VIS reanalysis materials

This package supports the revised analysis of 2,426 single-seed RGB images. It contains seven material labels, 13 archive-defined acquisition batches and four source regions. Each label combines variety identity and source; region and variety effects cannot be separated. Batches are retained as acquisition groups and do not establish independent mother-tree replication.

## Original archive and corrected counts

Original repository: https://github.com/lllpppzz/PoplarSeed-VIS
Immutable source commit: 190fbe59b25a12b5f4428e2e5869f9272b42da79
Original `date.zip` SHA256: eef9ae00c5efb338121cddadfff70641e9d9aa3d65d00537b25ea4d1c7f7489d

The original ZIP contains **2,426 TIFF images and 80 TXT measurement reports**, or 2,506 files in total. The earlier 2,506-image statement counted the TXT reports as images. No 80-image exclusion was applied. The 13 numbered folders are batches, not 13 varieties. Every TIFF in this package is byte-identical to its source image.

Regional metadata are corrected here: SHANXI QZ and SHANXI XY belong to North China; HENAN ZL belongs to Central China. Liaoning materials belong to Northeast China and NJFU 895 to East China. Original paths and their legacy region labels remain in `data/image_manifest.csv` to make every change traceable. The canonical `images/` tree uses corrected regions.

| Region | Material | Images | Batches |
|---|---|---:|---:|
| North China | SHANXI QZ | 378 | 2 |
| North China | SHANXI XY | 390 | 2 |
| Central China | HENAN ZL | 388 | 2 |
| East China | NJFU 895 | 781 | 4 |
| Northeast China | LIAON LHY | 192 | 1 |
| Northeast China | LIAON MZHY | 150 | 1 |
| Northeast China | LIAON XQY | 147 | 1 |
| Total | 7 materials | 2426 | 13 |

## Materials and provenance

The authors identify the material collection as the same collection described by Wang et al., *International Journal of Agricultural and Biological Engineering* 19(1), 197–212 (2026), doi:10.25165/j.ijabe.20261901.9850. That study already published a larger image resource and investigated morphological and chromatic measurements. This release is a curated reanalysis, not a claim of independent recollection or entirely new images.

The collection dates reported for the source materials are in May 2024. September 2024 timestamps occur in legacy report filenames; their role as acquisition or export times is not established. Mother-tree counts, a complete mapping from the 13 folders to independent harvest lots, and per-batch temperature, humidity and storage-duration logs are unavailable in the archive. No additional identity certification or molecular verification is claimed.

The 80 files in `legacy_reports/` carry the filename suffix `LWACstats`. They are legacy numerical measurement reports, not images or training records for this reanalysis. The full software-name expansion and version are not documented in the archived files. Current descriptors and masks were recomputed from the TIFF pixels with the supplied Python code; none of the 80 reports was used as an input feature or measurement ground truth.

## Package contents

- `images/`: original 230 × 230 TIFF pixels under corrected region folders.
- `masks/`: 2,426 automatically extracted binary PNG masks.
- `data/image_manifest.csv`: identifiers, material, batch, region, exact paths, hashes and fixed train/test membership.
- `data/seed_features.csv`: complete per-image records, 92 classifier descriptors and additional descriptive measurements.
- `data/feature_groups.json` and `analysis_feature_sets.json`: exact input columns including 81-, 35- and 68-descriptor retraining ablations.
- `data/tuning_cv_fold_manifest.csv`: five training-only validation folds; no held-out test seeds appear here.
- `data/primary_predictions.csv` and `batch_context_predictions.csv.gz`: individual predictions for all reported settings.
- `tables/`: full numerical results, uncertainty summaries, tuning search scores and ten held-out-batch outcome summaries.
- `code/`: feature extraction, cluster-resampling/REML analysis, SVM fits, ablations, permutations and figure generation.
- `reference/tables/`: earlier fixed-benchmark results used solely to check numerical reproduction, not to select new parameters.
- `audit/`: integrity checks and exact archive inventories.
- `SHA256SUMS.txt`: checksum of each delivered package file.

## Reproduction

Python 3.12 was used with the versions in `requirements.txt`. Install them in an isolated environment and run from the package directory:

```
python -m pip install -r requirements.txt
python code/extract_features.py
python code/cluster_analysis.py
python code/classification_revision.py
python code/make_revision_figures.py
```

The image scale is 20 μm/pixel in both directions. Foreground selection uses max-channel distance >8 from the estimated grey background, excludes border-connected and small components, retains the largest component and fills enclosed holes.

The existing 1,940/486 train/test membership is preserved. Fixed SVMs use RBF, C=50 and gamma='scale'. Sensitivity models select C and gamma separately using only training data and five-fold CV, with scaling refitted within each fold. The primary selection metric is macro-F1. Selection CV scores are not independent test performance estimates. The test set was already used in the original study; the new analyses are exploratory sensitivity analyses on that same split.

There are 2,000 hierarchical resamples and 1,000 block permutations per feature group. Resampling selects archive-defined batches within each material, then images within selected batches. Intervals for the three single-batch materials are conditional on those sole batches. Ten batches for four materials permit an exploratory random-intercept variance estimate after material fixed effects; this is not a genetic or geographical variance decomposition. Small batch counts and uncertain biological independence limit population inference.

The 32 four-material holdout combinations overlap. Ten unique held-out-batch outcomes report average recall and ranges across their training contexts, not 32 independent experimental replicates. Corpus majority fractions (32.19% for seven materials and 40.32% for four) are distinguished from each test set's actual training-majority baseline.

## Use and citation

Use is subject to the academic and non-commercial terms in `LICENSE.txt`, consistent with the source repository. Cite the PoplarSeed-VIS manuscript together with the source acquisition study. No DOI is assigned to this package. Use version `revision-2026-11-11`, the source commit and the ZIP SHA256 recorded alongside the package to identify the exact files. The original archive remains available for comparison.
