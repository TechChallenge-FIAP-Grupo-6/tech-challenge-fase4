import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import re


# ====== CONFIG ======
SRC_ROOT = Path("data/raw/video/m2cai16-tool-locations/m2cai16-tool-locations")
DST_ROOT = Path("data/processed/yolo_m2cai16")

VOC_ANN = SRC_ROOT / "Annotations"
VOC_IMG = SRC_ROOT / "JPEGImages"
IMGSETS = SRC_ROOT / "ImageSets" / "Main"

# Escolha simples: começar com poucas classes deixa o treino rápido
# Você pode mudar depois.
USE_ONLY_CLASSES = None  # ex.: {"grasper", "scissors", "hook"}  ou None para todas

def normalize_name(s: str) -> str:
    s = (s or "").strip()
    # remove prefixo numérico tipo "1 ", "2 ", "07 ", etc.
    s = re.sub(r"^\s*\d+\s*", "", s)
    return s.strip()

# ====================


def read_class_list():
    class_file = SRC_ROOT / "class_list.txt"
    names = []
    for line in class_file.read_text(encoding="utf-8").splitlines():
        x = line.strip()
        if x:
            names.append(normalize_name(x))
    return names



def parse_voc_xml(xml_path: Path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find("size")
    w = int(size.find("width").text)
    h = int(size.find("height").text)

    objects = []
    for obj in root.findall("object"):
        name = normalize_name(obj.find("name").text)

        bnd = obj.find("bndbox")
        xmin = float(bnd.find("xmin").text)
        ymin = float(bnd.find("ymin").text)
        xmax = float(bnd.find("xmax").text)
        ymax = float(bnd.find("ymax").text)
        objects.append((name, xmin, ymin, xmax, ymax, w, h))
    return objects


def voc_to_yolo_line(cls_id, xmin, ymin, xmax, ymax, w, h):
    # YOLO: class x_center y_center width height (all normalized 0..1)
    x_c = ((xmin + xmax) / 2.0) / w
    y_c = ((ymin + ymax) / 2.0) / h
    bw = (xmax - xmin) / w
    bh = (ymax - ymin) / h

    # clamp (safety)
    x_c = min(max(x_c, 0.0), 1.0)
    y_c = min(max(y_c, 0.0), 1.0)
    bw = min(max(bw, 0.0), 1.0)
    bh = min(max(bh, 0.0), 1.0)

    return f"{cls_id} {x_c:.6f} {y_c:.6f} {bw:.6f} {bh:.6f}"


def load_split(name: str):
    # train.txt / val.txt normalmente ficam aqui
    p = IMGSETS / f"{name}.txt"
    if not p.exists():
        raise FileNotFoundError(f"Não achei split: {p}")
    return [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def ensure_dirs():
    (DST_ROOT / "images/train").mkdir(parents=True, exist_ok=True)
    (DST_ROOT / "images/val").mkdir(parents=True, exist_ok=True)
    (DST_ROOT / "labels/train").mkdir(parents=True, exist_ok=True)
    (DST_ROOT / "labels/val").mkdir(parents=True, exist_ok=True)


def write_dataset_yaml(class_names):
    yaml_path = DST_ROOT / "dataset.yaml"
    # paths relative to yaml
    content = [
        f"path: {DST_ROOT.as_posix()}",
        "train: images/train",
        "val: images/val",
        f"nc: {len(class_names)}",
        "names:",
    ]
    for n in class_names:
        content.append(f"  - {n}")
    yaml_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    print(f"[OK] dataset.yaml criado em: {yaml_path}")


def process_split(split_name: str, ids, class_to_id):
    img_dst_dir = DST_ROOT / f"images/{split_name}"
    lab_dst_dir = DST_ROOT / f"labels/{split_name}"

    copied = 0
    labeled = 0

    for img_id in ids:
        # imagens geralmente são .jpg
        img_src = VOC_IMG / f"{img_id}.jpg"
        if not img_src.exists():
            # alguns datasets usam .png
            img_src = VOC_IMG / f"{img_id}.png"
        if not img_src.exists():
            print(f"[WARN] imagem não encontrada: {img_id}")
            continue

        xml_path = VOC_ANN / f"{img_id}.xml"
        if not xml_path.exists():
            print(f"[WARN] annotation não encontrada: {img_id}")
            continue

        objects = parse_voc_xml(xml_path)

        yolo_lines = []
        for (name, xmin, ymin, xmax, ymax, w, h) in objects:
            if USE_ONLY_CLASSES is not None and name not in USE_ONLY_CLASSES:
                continue
            if name not in class_to_id:
                continue
            cls_id = class_to_id[name]
            yolo_lines.append(voc_to_yolo_line(cls_id, xmin, ymin, xmax, ymax, w, h))

        # copia imagem
        shutil.copy2(img_src, img_dst_dir / img_src.name)
        copied += 1

        # escreve label (mesmo vazio, pra manter consistência)
        (lab_dst_dir / f"{img_id}.txt").write_text("\n".join(yolo_lines) + ("\n" if yolo_lines else ""), encoding="utf-8")
        labeled += 1

    print(f"[OK] {split_name}: imagens copiadas={copied}, labels geradas={labeled}")


def main():
    ensure_dirs()

    class_names = read_class_list()

    if USE_ONLY_CLASSES is not None:
        class_names = [c for c in class_names if c in USE_ONLY_CLASSES]

    class_to_id = {name: i for i, name in enumerate(class_names)}
    print("[INFO] classes:", class_names)

    # splits
    train_ids = load_split("train")
    val_ids = load_split("val") if (IMGSETS / "val.txt").exists() else load_split("test")  # fallback

    process_split("train", train_ids, class_to_id)
    process_split("val", val_ids, class_to_id)

    write_dataset_yaml(class_names)
    print("[DONE] dataset YOLO pronto em:", DST_ROOT)


if __name__ == "__main__":
    main()
