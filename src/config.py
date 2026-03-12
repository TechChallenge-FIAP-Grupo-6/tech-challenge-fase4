from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

@dataclass(frozen=True)
class Settings:
    azure_speech_key: str | None = os.getenv("AZURE_SPEECH_KEY") or None
    azure_speech_region: str | None = os.getenv("AZURE_SPEECH_REGION") or None

    video_alert_threshold: float = _get_float("VIDEO_ALERT_THRESHOLD", 0.65)
    audio_alert_threshold: float = _get_float("AUDIO_ALERT_THRESHOLD", 0.65)
    text_alert_threshold: float = _get_float("TEXT_ALERT_THRESHOLD", 0.60)
    final_alert_threshold: float = _get_float("FINAL_ALERT_THRESHOLD", 0.70)

    # Fusion weights
    w_video: float = _get_float("W_VIDEO", 0.40)
    w_audio: float = _get_float("W_AUDIO", 0.40)
    w_text: float = _get_float("W_TEXT", 0.20)

settings = Settings()
