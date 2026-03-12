import argparse
import sys
import os
from datetime import datetime
from pathlib import Path
import moviepy.editor as mp # Usamos moviepy para converter qualquer coisa em WAV

# --- Imports dos Módulos ---
from video.inference_video import analyze_video
from audio.anomaly_audio import analyze_audio
from text.text_risk_rules import analyze_text
from fusion.fusion import fuse
from utils.report_utils import save_json, save_markdown, build_markdown_report
from audio.transcribe_azure import transcribe_with_azure

# Extensões suportadas
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".wma"}

def prepare_audio_file(input_path, output_wav_path):
    """
    Função Universal:
    - Se for vídeo: Extrai o áudio.
    - Se for áudio (mp3/m4a): Converte para WAV (padrão para Azure/Librosa).
    - Se já for wav: Apenas copia ou sobrescreve para garantir o formato.
    """
    try:
        # O AudioFileClip do MoviePy é inteligente: abre vídeo ou áudio
        clip = mp.AudioFileClip(str(input_path))
        
        # Cria a pasta se não existir
        os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)
        
        # Salva como WAV puro (essencial para Librosa e Azure funcionarem bem)
        clip.write_audiofile(output_wav_path, logger=None, verbose=False)
        clip.close()
        return True
    except Exception as e:
        print(f"Erro ao preparar áudio: {e}")
        return False

def run_pipeline(input_path_str: str, temp_audio_path: str):
    """Executa a análise adaptando-se se for Vídeo ou Áudio."""
    
    input_path = Path(input_path_str)
    suffix = input_path.suffix.lower()
    timestamp = datetime.now().isoformat(timespec="seconds")
    
    is_video = suffix in VIDEO_EXTS
    is_audio = suffix in AUDIO_EXTS

    if not (is_video or is_audio):
        print(f"Formato não suportado: {suffix}")
        return None

    # 1. Preparação do Áudio (Extração ou Conversão)
    print(f"Preparando áudio (convertendo para WAV)...")
    success = prepare_audio_file(input_path, temp_audio_path)
    
    if not success:
        print("Falha crítica: Não foi possível gerar o arquivo de áudio WAV.")
        return None

    # 2. Análise de Vídeo (SÓ RODA SE FOR VÍDEO)
    if is_video:
        print(f"Processando vídeo: {input_path.name}")
        try:
            video_result = analyze_video(str(input_path))
        except Exception as e:
            print(f"Erro no vídeo: {e}")
            video_result = {"risk_video": 0.0, "alert": False, "findings": ["Erro na análise de vídeo"]}
    else:
        print(f"Entrada é Áudio: Pulando análise de vídeo.")
        # Cria um resultado "falso" nulo para não quebrar a fusão
        video_result = {
            "risk_video": 0.0,
            "alert": False,
            "findings": ["Modo Áudio Puro: Análise de vídeo ignorada."],
            "meta": {"frames": 0, "detections": 0}
        }
    
    # 3. Análise de Áudio (Librosa)
    print(f"Processando áudio (Sinais): {Path(temp_audio_path).name}")
    audio_result = analyze_audio(temp_audio_path)

    # 4. Transcrição (AZURE AI)
    print(f"Realizando transcrição (Azure AI)...")
    transcript = transcribe_with_azure(temp_audio_path)
    
    if transcript and len(transcript) > 2:
        print(f"      Texto Detectado: \"{transcript[:60]}...\"")
    else:
        print(f"Sem texto detectado (áudio mudo ou ruído).")
        transcript = ""

    # 5. Análise de Texto (Palavras de Risco)
    text_result = analyze_text(transcript)
    audio_result["transcript"] = transcript

    # 6. Fusão Multimodal
    # Se for só áudio, o risco de vídeo é 0, então o risco final será baseado em áudio+texto
    fusion_result = fuse(video_result, audio_result, text_result)

    final_output = {
        "timestamp": timestamp,
        "input_type": "video" if is_video else "audio",
        "source_file": str(input_path),
        "video": video_result,
        "audio": audio_result,
        "text": text_result,
        "fusion": fusion_result,
    }
    return final_output

def save_results(result, out_dir_path, filename_prefix):
    if not result: return
    out_dir = Path(out_dir_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{filename_prefix}_{stamp}"

    save_json(out_dir, name, result)
    md = build_markdown_report(result)
    save_markdown(out_dir, name, md)

    print(f"Concluído. RiskScore: {result['fusion']['risk_final']:.2f}")
    print(f"Relatório salvo em: {out_dir / name}")
    print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Pipeline HerCare AI (Vídeo & Áudio)")
    
    # Argumentos
    parser.add_argument("--input_dir", default="../data/samples", help="Pasta com arquivos (mp4, wav, mp3)")
    parser.add_argument("--file", default=None, help="Caminho de um arquivo único específico")
    parser.add_argument("--out", default="../docs/evidencias", help="Pasta de saída")
    
    args = parser.parse_args()

    # --- LÓGICA DE SELEÇÃO DE ARQUIVOS ---
    files_to_process = []

    # Se o usuário passou um arquivo específico (--file)
    if args.file:
        p = Path(args.file)
        if p.exists():
            files_to_process.append(p)
        else:
            print(f"Arquivo não encontrado: {p}")
            return
    # Se não, varre a pasta padrão (--input_dir)
    elif args.input_dir:
        input_path = Path(args.input_dir)
        if input_path.exists():
            # Pega tanto vídeo quanto áudio
            valid_exts = VIDEO_EXTS.union(AUDIO_EXTS)
            files_to_process = [f for f in input_path.iterdir() if f.suffix.lower() in valid_exts]
            print(f"📂 Modo Lote: Encontrados {len(files_to_process)} arquivos na pasta.")
        else:
            print(f"Pasta não encontrada: {input_path}")
            return

    if not files_to_process:
        print("Nenhum arquivo compatível encontrado para processar.")
        return

    print("-" * 40)
    
    # --- LOOP DE PROCESSAMENTO ---
    for file_path in files_to_process:
        print(f"Iniciando Análise: {file_path.name}")
        
        # Define nome do arquivo temporário wav
        # Ex: video.mp4 -> video.wav | audio.mp3 -> audio.wav
        temp_wav_path = file_path.with_suffix(".wav")
        
        try:
            result = run_pipeline(str(file_path), str(temp_wav_path))
            save_results(result, args.out, f"relatorio_{file_path.stem}")
        except Exception as e:
            print(f"Erro ao processar {file_path.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()