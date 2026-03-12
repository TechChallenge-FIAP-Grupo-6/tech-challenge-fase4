import numpy as np
from sklearn.ensemble import IsolationForest

from config import settings
from utils.audio_utils import load_audio, compute_audio_features

def analyze_audio(audio_path: str):
    y, sr = load_audio(audio_path)
    feats = compute_audio_features(y, sr)

    # Garante que mfcc_mean seja uma lista para concatenar corretamente
    mfcc_values = feats["mfcc_mean"]
    if hasattr(mfcc_values, "tolist"):
        mfcc_values = mfcc_values.tolist()
    
    # Constrói o vetor de características
    vec = np.array([feats["rms"], feats["zcr"], feats["silence_ratio"]] + list(mfcc_values), dtype=float).reshape(1, -1)

    # Demo: treina com ele mesmo + ruído (baseline não supervisionado)
    X_train = np.vstack([vec, vec + np.random.normal(0, 0.01, size=vec.shape), vec + np.random.normal(0, 0.01, size=vec.shape)])
    clf = IsolationForest(random_state=42, contamination=0.15)
    clf.fit(X_train)

    # Maior anomalia => maior risco
    score = -float(clf.score_samples(vec)[0])  # inverte o sinal
    
    # Normaliza grosseiramente para 0..1
    risk_audio = float(min(1.0, max(0.0, (score - 0.2) / 0.8)))
    
#RMS (Energia/Volume) = 0.07: Isso é baixo. A pessoa não está gritando desesperadamente. Se fosse um grito de pavor, isso estaria perto de 0.3 ou 0.5.
#ZCR (Aspereza) = 0.14: O "Zero Crossing Rate" mede a vibração rápida. Vozes chorosas ou gritos estridentes têm ZCR alto. 0.14 é uma fala normal, talvez um pouco manhosa, mas não aguda.
#Silence Ratio = 0.10: Apenas 10% de silêncio. A pessoa falou continuamente, sem longas pausas de respiração ou desmaio

    findings = [
        f"RMS (Energia/Volume): {feats['rms']:.4f}",
        f"ZCR (Aspereza, axa de cruzamento por zero): {feats['zcr']:.4f}",
        f"Silence ratio (pausas estimadas): {feats['silence_ratio']:.2f}",
        f"Score de anomalia (demo): {score:.3f}",
    ]

    alert = risk_audio >= settings.audio_alert_threshold
    if alert:
        findings.append("Alerta: score de áudio acima do limiar configurado.")

    return {
        "risk_audio": risk_audio,
        "alert": bool(alert),
        "findings": findings,
        "features": feats,
    }