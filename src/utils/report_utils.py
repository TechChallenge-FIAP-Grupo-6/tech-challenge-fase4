import json
from pathlib import Path
from datetime import datetime

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def save_json(out_dir: str | Path, name: str, payload: dict) -> Path:
    out = ensure_dir(out_dir) / f"{name}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

def save_markdown(out_dir: str | Path, name: str, md: str) -> Path:
    out = ensure_dir(out_dir) / f"{name}.md"
    out.write_text(md, encoding="utf-8")
    return out

def build_markdown_report(result: dict) -> str:
    ts = result.get("timestamp")
    video = result.get("video", {})
    audio = result.get("audio", {})
    text = result.get("text", {})
    fusion = result.get("fusion", {})

    def bullet(items):
        if not items:
            return "- (nenhum achado relevante nesta etapa)"
        return "\n".join([f"- {x}" for x in items])

    return f"""# Relatório — HerCare AI

**Data/Hora:** {ts}

## Resumo
- **RiskScore final:** **{fusion.get('risk_final', 0):.2f}**
- **Classificação:** **{fusion.get('risk_level', 'N/A')}**
- **Alertas:** {', '.join(fusion.get('alerts', [])) if fusion.get('alerts') else 'Nenhum alerta acima do limiar.'}

---

## Vídeo
- **risk_video:** {video.get('risk_video', 0):.2f}
- **alerta_video:** {video.get('alert', False)}
### Achados
{bullet(video.get('findings', []))}

## Áudio
- **risk_audio:** {audio.get('risk_audio', 0):.2f}
- **alerta_audio:** {audio.get('alert', False)}
### Achados
{bullet(audio.get('findings', []))}

## Texto (transcrição)
- **risk_text:** {text.get('risk_text', 0):.2f}
- **alerta_texto:** {text.get('alert', False)}
### Gatilhos detectados
{bullet(text.get('findings', []))}

---

## Observações de privacidade
- Chaves de nuvem via `.env`.
- Recomenda-se dados anonimizados para demonstração.
"""
