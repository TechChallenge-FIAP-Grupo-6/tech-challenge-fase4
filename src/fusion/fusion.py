from config import settings

def fuse(video: dict, audio: dict, text: dict) -> dict:
    rv = float(video.get("risk_video", 0.0))
    ra = float(audio.get("risk_audio", 0.0))
    rt = float(text.get("risk_text", 0.0))

    risk_final = settings.w_video * rv + settings.w_audio * ra + settings.w_text * rt
    risk_final = max(0.0, min(1.0, float(risk_final)))

    if risk_final >= 0.75:
        level = "Alto"
    elif risk_final >= 0.50:
        level = "Moderado"
    else:
        level = "Baixo"

    alerts = []
    if video.get("alert"):
        alerts.append("Vídeo")
    if audio.get("alert"):
        alerts.append("Áudio")
    if text.get("alert"):
        alerts.append("Texto")
    if risk_final >= settings.final_alert_threshold:
        alerts.append("Final")

    return {
        "risk_final": risk_final,
        "risk_level": level,
        "alerts": alerts,
        "weights": {"video": settings.w_video, "audio": settings.w_audio, "text": settings.w_text},
    }
