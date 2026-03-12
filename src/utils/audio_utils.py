import numpy as np
import librosa

def load_audio(audio_path: str, sr: int = 16000):
    y, sr = librosa.load(audio_path, sr=sr, mono=True)
    return y, sr

def compute_audio_features(y: np.ndarray, sr: int) -> dict:
    # Basic, interpretable features
    rms = librosa.feature.rms(y=y).mean()
    zcr = librosa.feature.zero_crossing_rate(y).mean()
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)

    # Pause estimate: % of frames below small threshold
    frame_len = int(0.03 * sr)  # 30ms
    hop = int(0.01 * sr)        # 10ms
    frames = librosa.util.frame(y, frame_length=frame_len, hop_length=hop)
    energy = np.sqrt(np.mean(frames**2, axis=0))
    silence_ratio = float(np.mean(energy < (np.percentile(energy, 10) + 1e-8)))

    return {
        "rms": float(rms),
        "zcr": float(zcr),
        "mfcc_mean": [float(x) for x in mfcc],
        "silence_ratio": silence_ratio,
    }
