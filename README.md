# PoplarSeed-VIS

**A multi-regional poplar seed visual image dataset for phenotypic analysis**  
**多地区杨树种子可视化图像数据集（用于表型分析）**

---

## Overview | 数据集简介

PoplarSeed-VIS is a high-resolution TIF image dataset of poplar (*Populus* spp.) seeds collected from four major geographic regions of China. Each seed sample is accompanied by morphological statistics measured via imaging analysis software (LWAC). The dataset supports research in seed morphology, species identification, and machine learning-based phenotypic classification.

本数据集收录了中国四大地理区域杨树种子的高分辨率 TIF 图像，每张图像附有通过图像分析软件（LWAC）采集的形态学统计数据，适用于种子形态分析、品种识别及机器学习表型分类研究。

---

## Dataset Structure | 数据集结构

```
date/
├── Central China/          # 华中
│   ├── SHANXI QZ-1/        # 山西群众杨 - 1
│   ├── SHANXI QZ-2/        # 山西群众杨 - 2
│   ├── SHANXI XY-1/        # 山西小叶杨 - 1
│   └── SHANXI XY-2/        # 山西小叶杨 - 2
├── East China/             # 华东
│   ├── NJFU 895-1/         # 南京林业大学 895 杨 - 1
│   ├── NJFU 895-2/         # 南京林业大学 895 杨 - 2
│   ├── NJFU 895-3/         # 南京林业大学 895 杨 - 3
│   └── NJFU 895-4/         # 南京林业大学 895 杨 - 4
├── North China/            # 华北
│   ├── HENAN ZL-1/         # 河南中林杨 - 1
│   └── HENAN ZL-2/         # 河南中林杨 - 2
└── Northeast China/        # 东北
    ├── LIAON LHY-1/        # 辽宁辽胡杨 - 1
    ├── LIAON MZHY-1/       # 辽宁美洲黑杨 - 1
    └── LIAON XQY-1/        # 辽宁小青杨 - 1
```

Each variety folder contains:  
每个品种文件夹包含：
- **`*.tif`** — Single-seed image (high-resolution TIF format) | 单粒种子图像（高分辨率 TIF 格式）
- **`*LWACstats.txt`** — Morphological statistics for each batch | 每批次形态学统计数据

---

## Statistics | 数据统计

| Item | Value |
|------|-------|
| Total images | 2,506 |
| Image format | TIF |
| Regions | 4 |
| Varieties | 13 |
| Collection date | September 2024 |

---

## Varieties | 品种信息

| Region | Code | Chinese Name | Poplar Species |
|--------|------|-------------|----------------|
| Central China | SHANXI QZ-1/2 | 山西群众杨 | *Populus* × *qunzhong* |
| Central China | SHANXI XY-1/2 | 山西小叶杨 | *Populus simonii* |
| East China | NJFU 895-1/2/3/4 | 南京林业大学 895 杨 | *Populus* × *euramericana* cl. '895' |
| North China | HENAN ZL-1/2 | 河南中林杨 | *Populus* × *zhonglin* |
| Northeast China | LIAON LHY-1 | 辽宁辽胡杨 | *Populus euphratica* (辽宁种源) |
| Northeast China | LIAON MZHY-1 | 辽宁美洲黑杨 | *Populus deltoides* |
| Northeast China | LIAON XQY-1 | 辽宁小青杨 | *Populus pseudo-simonii* |

---

## File Naming Convention | 文件命名规则

**TIF images:**
```
{VarietyCode}-{index}.tif
e.g., SHANXI QZ-1-1.tif, SHANXI QZ-1-100.tif
```

**Statistics files (LWACstats.txt):**
```
{ChineseName}{timestamp}LWACstats.txt
e.g., 山西群众场 120240907162325960LWACstats.txt
```
The timestamp format is `YYYYMMDDHHMMSSMS`.

---

## Data Format | 数据格式

- **Images**: Single-channel or multi-channel TIF, approximately 159 KB per image
- **Stats files**: Text format containing morphological measurements (Length, Width, Area, Color, etc.) exported by LWAC imaging software

---

## Download | 数据下载

The full dataset is packaged as `date.zip` in this repository.

```bash
git clone https://github.com/lllpppzz/PoplarSeed-VIS.git
cd PoplarSeed-VIS
unzip date.zip
```

---

## Intended Use | 用途

- Seed morphology and phenotypic analysis | 种子形态与表型分析
- Multi-variety poplar seed classification | 多品种杨树种子分类
- Machine learning / deep learning training dataset | 机器学习 / 深度学习训练数据
- Geographic provenance identification | 地理种源鉴别研究

---

## Citation | 引用

If you use this dataset in your research, please cite it as:

```
@dataset{PoplarSeed-VIS,
  title   = {PoplarSeed-VIS: A Multi-Regional Poplar Seed Visual Image Dataset},
  author  = {lllpppzz},
  year    = {2024},
  url     = {https://github.com/lllpppzz/PoplarSeed-VIS}
}
```

---

## License | 许可证

This dataset is released for academic and non-commercial research use only.  
本数据集仅供学术和非商业研究使用。
