# Datasets

RailVision AI trains a custom **YOLO26** detector on a 15-class railway
obstacle taxonomy (see `railvision/data.yaml`).

## Layout (YOLO format)

```
datasets/railvision/
├── data.yaml
├── images/{train,val,test}/*.jpg
└── labels/{train,val,test}/*.txt   # one <class cx cy w h> per line, normalised
```

## Dataset versioning (DVC)

Large image/label folders are **not** committed to git. They are versioned with
[DVC](https://dvc.org) so experiments are reproducible:

```bash
dvc init
dvc add datasets/railvision/images datasets/railvision/labels
git add datasets/railvision/*.dvc .gitignore
dvc remote add -d storage s3://railvision-datasets
dvc push
```

## Building the dataset

Suggested public sources to compose and re-label into this taxonomy
(respect each source's license and add attribution):

- Railway track / obstacle datasets (Roboflow Universe, OpenRailLab).
- Animal classes: from COCO / Open Images (cow, elephant, dog, sheep→goat).
- Vehicles: COCO (car, truck, bus, motorcycle).
- `fallen_tree`, `rock`, `construction_barrier`, `debris`, `unknown`: curate
  and hand-label railway incident footage.

Use `python -m app.mlops.train --data datasets/railvision/data.yaml` to fine-tune.
```
