from pathlib import Path
import cv2

def extract_frames(video_path: str, out_dir: str, every_n_frames: int = 30, max_frames: int = 80) -> list[str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Não foi possível abrir o vídeo: {video_path}")

    frames = []
    i = 0
    saved = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if i % every_n_frames == 0:
            fp = out / f"frame_{saved:04d}.jpg"
            cv2.imwrite(str(fp), frame)
            frames.append(str(fp))
            saved += 1
            if saved >= max_frames:
                break

        i += 1

    cap.release()
    return frames
