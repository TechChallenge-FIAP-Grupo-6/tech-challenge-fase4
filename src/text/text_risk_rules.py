import re
import csv
from pathlib import Path
from config import settings

def load_risk_terms():
    # 1. Pega o diretório do script e calcula o caminho do CSV
    script_dir = Path(__file__).resolve().parent
    csv_path = script_dir.parent.parent / "data" / "risk_keywords.csv"

    print(f"🔍 Buscando CSV em: {csv_path}")

    if not csv_path.exists():
        print(f"❌ ERRO: Arquivo não encontrado!")
        return ["medo", "ansiedade", "dor", "socorro", "ajuda"]

    terms = []

    # --- LÓGICA BLINDADA DE LEITURA ---
    # Tenta ler com UTF-8 primeiro. Se falhar, tenta Latin-1 (Windows)
    encodings_to_try = ['utf-8-sig', 'latin-1', 'cp1252']
    
    file_content = None
    used_encoding = None

    for enc in encodings_to_try:
        try:
            with open(csv_path, mode='r', encoding=enc) as f:
                # Força a leitura de tudo para testar o encoding agora
                file_content = list(csv.reader(f))
                used_encoding = enc
                break # Se funcionou, para o loop
        except UnicodeDecodeError:
            continue # Se deu erro, tenta o próximo da lista

    if file_content is None:
        print("❌ Erro Crítico: Não foi possível ler o arquivo com nenhum encoding conhecido.")
        return ["ajuda", "socorro"]

    print(f"✅ Arquivo lido com sucesso usando encoding: {used_encoding}")

    # Processa o conteúdo lido
    try:
        for row in file_content:
            if row:
                term = row[0].strip().lower()
                if term and term != "termo":
                    terms.append(term)
        
        print(f"📚 Total de termos carregados: {len(terms)}")
        return terms

    except Exception as e:
        print(f"❌ Erro ao processar termos: {e}")
        return ["ajuda", "socorro"]

# Carrega os termos
RISK_TERMS = load_risk_terms()

def analyze_text(transcript: str):
    text = (transcript or "").lower()
    hits = []

    for term in RISK_TERMS:
        if " " in term:
            if term in text:
                hits.append(term)
        else:
            if re.search(r'\b' + re.escape(term) + r'\b', text):
                hits.append(term)

    # Score ajustado
    risk_text = min(1.0, len(hits) / 5.0)

    findings = []
    if hits:
        unique_hits = sorted(list(set(hits)))
        findings.append(f"Termos de risco ({len(unique_hits)}): " + ", ".join(unique_hits))
    else:
        findings.append("Nenhum termo de risco detectado.")

    alert = risk_text >= settings.text_alert_threshold
    
    if alert:
        findings.append("ALERTA: Texto indica alto risco.")

    return {
        "risk_text": float(risk_text),
        "alert": bool(alert),
        "findings": findings,
        "hits": hits
    }