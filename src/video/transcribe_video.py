import moviepy.editor as mp
import speech_recognition as sr
import os

def extract_audio_from_video(video_path, audio_output_path):
    """Extrai o áudio do vídeo e salva como .wav"""
    try:
        # Carrega o vídeo
        video = mp.VideoFileClip(video_path)
        
        # Cria a pasta se não existir
        os.makedirs(os.path.dirname(audio_output_path), exist_ok=True)
        
        # Extrai e salva o áudio
        video.audio.write_audiofile(audio_output_path, logger=None) # logger=None reduz o texto no terminal
        return True
    except Exception as e:
        print(f"❌ Erro ao extrair áudio: {e}")
        return False

def transcribe_audio_to_text(audio_path):
    """Lê o arquivo de áudio e retorna o texto transcrito."""
    recognizer = sr.Recognizer()
    
    if not os.path.exists(audio_path):
        return "Erro: Arquivo de áudio não encontrado."

    with sr.AudioFile(audio_path) as source:
        # print("   🎙️ Lendo áudio...")
        audio = recognizer.record(source)  # lê todo o áudio
        
        try:
            # Usa o Google Speech Recognition (Online)
            text = recognizer.recognize_google(audio, language="pt-BR")
            return text
                
        except sr.UnknownValueError:
            return "" # Retorna vazio se não entender nada (silêncio/ruído)
        except sr.RequestError as e:
            return f"Erro na API do Google: {e}"
        except Exception as e:
            return f"Erro na transcrição: {e}"