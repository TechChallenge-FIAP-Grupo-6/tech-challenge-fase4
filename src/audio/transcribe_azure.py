import os
import time
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

def transcribe_with_azure(audio_path):
    """
    Transcreve áudio usando Azure Cognitive Services (Speech SDK).
    Suporta arquivos longos através de reconhecimento contínuo.
    """
    
    # 1. Recupera as chaves
    speech_key = os.getenv('AZURE_SPEECH_KEY')
    service_region = os.getenv('AZURE_SPEECH_REGION')

    if not speech_key or not service_region:
        print("Erro: Chaves da Azure não configuradas no arquivo .env")
        return ""

    if not os.path.exists(audio_path):
        print(f"Erro: Arquivo de áudio não encontrado: {audio_path}")
        return ""

    try:
        # 2. Configurações do Serviço
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_recognition_language = "pt-BR"
        
        # Otimiza para ditado/conversa (pontuação e formatação)
        speech_config.set_profanity(speechsdk.ProfanityOption.Raw) 

        # 3. Configuração do Áudio
        audio_config = speechsdk.AudioConfig(filename=audio_path)

        # 4. Inicializa o Reconhecedor
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Listas para armazenar os resultados
        all_results = []
        done = False

        # --- Funções de Callback (Eventos) ---
        
        def stop_cb(evt):
            """Chamado quando a sessão para (fim do arquivo ou erro)"""
            # print(f'CLOSING on {evt}')
            nonlocal done
            done = True

        def recognized_cb(evt):
            """Chamado quando uma frase completa é reconhecida"""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # print(f"Recognized: {evt.result.text}")
                all_results.append(evt.result.text)
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                print("NOMATCH: Speech could not be recognized.")

        # Conecta os eventos
        recognizer.recognized.connect(recognized_cb)
        recognizer.session_stopped.connect(stop_cb)
        recognizer.canceled.connect(stop_cb)

        # 5. Inicia o reconhecimento contínuo
        # print("Conectando à Azure AI Speech...")
        recognizer.start_continuous_recognition()

        # Aguarda até terminar (loop de espera)
        while not done:
            time.sleep(0.5)

        # 6. Para o reconhecimento e junta o texto
        recognizer.stop_continuous_recognition()
        
        final_text = " ".join(all_results)
        return final_text

    except Exception as e:
        print(f"Erro crítico na Azure: {e}")
        return ""