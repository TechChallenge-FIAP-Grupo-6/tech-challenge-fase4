import json
from pathlib import Path
from collections import defaultdict

PRED_DIR = Path("runs/detect/runs/detect/predict")
LABELS_DIR = PRED_DIR / "labels"

OUT_DIR = Path("data/processed/video_alerts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Ajuste se quiser: fps "fictício" para converter frame->tempo (como estamos em frames soltos)
FPS = 25

# Regras (simples e defensáveis)
CRITICAL_CLASS = "SpecimenBag"      # alerta se aparecer
MANY_TOOLS_THRESHOLD = 3            # >=3 ferramentas simultâneas
MANY_TOOLS_MIN_FRAMES = 25          # ~1s se FPS=25
PROLONGED_MIN_FRAMES = 75           # ~3s se FPS=25


def load_class_names_from_yaml():
    # tenta achar dataset.yaml para nomes bonitos
    yaml_path = Path("data/processed/yolo_m2cai16/dataset.yaml")
    if not yaml_path.exists():
        return None
    names = []
    in_names = False
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("names:"):
            in_names = True
            continue
        if in_names:
            if s.startswith("- "):
                names.append(s[2:].strip())
            elif s and not s.startswith("#"):
                # parou a lista
                break
    return names if names else None


def parse_label_file(p: Path):
    """
    label format (Ultralytics save_txt):
    cls x y w h [conf]
    """
    dets = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.strip().split()
        cls_id = int(float(parts[0]))
        conf = float(parts[5]) if len(parts) >= 6 else None
        dets.append((cls_id, conf))
    return dets


def contiguous_ranges(indices):
    """convert list of ints -> list of (start,end) contiguous inclusive ranges"""
    if not indices:
        return []
    indices = sorted(indices)
    ranges = []
    start = prev = indices[0]
    for x in indices[1:]:
        if x == prev + 1:
            prev = x
        else:
            ranges.append((start, prev))
            start = prev = x
    ranges.append((start, prev))
    return ranges


def main():
    if not LABELS_DIR.exists():
        raise SystemExit(f"Não achei {LABELS_DIR}. Rode o predict com save_txt=True.")

    class_names = load_class_names_from_yaml()
    if class_names:
        id_to_name = {i: n for i, n in enumerate(class_names)}
    else:
        id_to_name = None

    # lista de frames pelo nome do arquivo .txt (mesmo nome da imagem)
    label_files = sorted(LABELS_DIR.glob("*.txt"))
    if not label_files:
        raise SystemExit(f"Nenhum .txt em {LABELS_DIR}")

    # Map: frame_index -> set(classes present)
    frame_classes = []
    frame_conf = []  # optional: max conf per class in frame
    for lf in label_files:
        dets = parse_label_file(lf)
        classes = [d[0] for d in dets]
        frame_classes.append(set(classes))

        conf_map = defaultdict(float)
        for cls_id, conf in dets:
            if conf is not None:
                conf_map[cls_id] = max(conf_map[cls_id], conf)
        frame_conf.append(conf_map)

    # --- Rule 1: critical class appears
    critical_id = None
    if id_to_name:
        for k, v in id_to_name.items():
            if v == CRITICAL_CLASS:
                critical_id = k
                break

    critical_frames = []
    if critical_id is not None:
        for i, s in enumerate(frame_classes):
            if critical_id in s:
                critical_frames.append(i)

    critical_ranges = contiguous_ranges(critical_frames)

    # --- Rule 2: many tools simultaneous
    many_frames = [i for i, s in enumerate(frame_classes) if len(s) >= MANY_TOOLS_THRESHOLD]
    many_ranges = [(a, b) for (a, b) in contiguous_ranges(many_frames) if (b - a + 1) >= MANY_TOOLS_MIN_FRAMES]

    # --- Rule 3: prolonged tool usage (per class)
    prolonged_alerts = []
    # build per-class presence frames
    all_class_ids = sorted({c for s in frame_classes for c in s})
    for cid in all_class_ids:
        idxs = [i for i, s in enumerate(frame_classes) if cid in s]
        ranges = contiguous_ranges(idxs)
        for a, b in ranges:
            length = b - a + 1
            if length >= PROLONGED_MIN_FRAMES:
                prolonged_alerts.append((cid, a, b, length))

    def frame_to_time(f):
        return round(f / FPS, 2)

    alerts = []

    for a, b in critical_ranges:
        alerts.append({
            "type": "CRITICAL_INSTRUMENT",
            "class": CRITICAL_CLASS,
            "start_frame": a,
            "end_frame": b,
            "start_time_sec": frame_to_time(a),
            "end_time_sec": frame_to_time(b),
        })

    for a, b in many_ranges:
        alerts.append({
            "type": "MANY_TOOLS_SIMULTANEOUS",
            "threshold": MANY_TOOLS_THRESHOLD,
            "start_frame": a,
            "end_frame": b,
            "start_time_sec": frame_to_time(a),
            "end_time_sec": frame_to_time(b),
        })

    for cid, a, b, length in prolonged_alerts:
        cname = id_to_name[cid] if id_to_name else str(cid)
        alerts.append({
            "type": "PROLONGED_TOOL_USAGE",
            "class": cname,
            "frames": length,
            "seconds": round(length / FPS, 2),
            "start_frame": a,
            "end_frame": b,
            "start_time_sec": frame_to_time(a),
            "end_time_sec": frame_to_time(b),
        })

    # ordena
    alerts.sort(key=lambda x: (x["start_frame"], x["type"]))

    report = {
        "case_id": "case_val_frames",
        "source": str(PRED_DIR),
        "fps_assumed": FPS,
        "rules": {
            "critical_class": CRITICAL_CLASS,
            "many_tools_threshold": MANY_TOOLS_THRESHOLD,
            "many_tools_min_frames": MANY_TOOLS_MIN_FRAMES,
            "prolonged_min_frames": PROLONGED_MIN_FRAMES,
        },
        "alerts_count": len(alerts),
        "alerts": alerts,
    }

    out_path = OUT_DIR / "video_alerts.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Alertas gerados: {out_path}")
    print(f"[OK] Total alertas: {len(alerts)}")
    if len(alerts) == 0:
        print("[INFO] Nenhum alerta com os thresholds atuais. Você pode reduzir os thresholds (min_frames).")


if __name__ == "__main__":
    main()
