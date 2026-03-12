from ultralytics import YOLO
from config import settings
from utils.video_utils import extract_frames

def analyze_video(video_path: str, frames_dir: str = "docs/evidencias/frames"):
    # Carrega o modelo (na primeira execução ele baixa automaticamente)
    model = YOLO("yolov8n.pt")

    # Extrai frames do vídeo para analisar (ex: 1 frame a cada segundo)
    frames = extract_frames(video_path, frames_dir, every_n_frames=30, max_frames=60)

    total_dets = 0
    confs = []
    
    for fp in frames:
        # Roda a detecção no frame
        res = model.predict(fp, verbose=False)
        if not res:
            continue
            
        boxes = res[0].boxes
        if boxes is None:
            continue
            
        total_dets += len(boxes)
        
        for b in boxes:
            # --- CORREÇÃO AQUI ---
            # Antes: c = float(b.conf.cpu().numpy()) -> dava erro se fosse array
            # Agora: .item() extrai o valor numérico limpo, independente do formato
            if b.conf is not None:
                c = b.conf.item()
                confs.append(c)
            # ---------------------

    mean_conf = sum(confs) / len(confs) if confs else 0.0

    # Lógica simples de risco (Demo):
    # Se detectar muitas pessoas/objetos com alta confiança, aumenta o risco
    risk_video = min(1.0, (total_dets / 80.0) * 0.5 + mean_conf * 0.5)

    findings = []
    findings.append(f"Frames analisados: {len(frames)}")
    findings.append(f"Detecções totais: {total_dets}")
    findings.append(f"Confiança média: {mean_conf:.2f}")

    alert = risk_video >= settings.video_alert_threshold
    if alert:
        findings.append("Alerta: score de vídeo acima do limiar configurado.")

    return {
        "risk_video": float(risk_video),
        "alert": bool(alert),
        "findings": findings,
        "meta": {"frames": len(frames), "detections": total_dets, "mean_conf": float(mean_conf)},
    }