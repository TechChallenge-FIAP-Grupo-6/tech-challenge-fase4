# HerCare AI — Tech Challenge FIAP (Fase 4)

Protótipo multimodal (**vídeo + áudio + texto**) para monitoramento preventivo em saúde da mulher, com **detecção de anomalias**, **fusão de evidências** e geração de **relatórios/alertas**.

> **Azure:** este projeto roda localmente e integra com **Azure Speech-to-Text** via API. Para a demonstração completa, configure `AZURE_SPEECH_KEY` e `AZURE_SPEECH_REGION` no `.env` (não versionar).

---

## Requisitos atendidos (mapeamento rápido)

**Análise de vídeo** com **YOLOv8 customizado** (Ultralytics) para detecção de instrumentos em cenas cirúrgicas.
**Detecção de anomalias em tempo real (por regras)** a partir da sequência de detecções por frame (ex.: instrumento crítico, simultaneidade, duração).
**Análise de áudio** com transcrição via **Azure Speech-to-Text** + extração de sinais/indicadores (ex.: risco psicológico/violência por regras/score).
**Texto** analisado a partir da transcrição (regras de risco) e incluído no relatório.
**Fusão multimodal** (vídeo + áudio + texto) → `RiskScore` final e relatório (pipeline).
**Boas práticas de segurança**: chaves via `.env`, sem dados sensíveis no Git.

---

## 1) Instalação

### 1.1 Criar ambiente virtual
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
1.2 Instalar dependências
pip install -r requirements.txt
2) Configurar Azure Speech-to-Text
Crie um arquivo .env na raiz (use .env.example como base) e preencha:

AZURE_SPEECH_KEY=...

AZURE_SPEECH_REGION=...

Se as variáveis não estiverem definidas, o projeto pode rodar em modo demo com transcrição simulada (para não travar). Para a entrega, recomenda-se demonstrar a integração real.

3) Executar pipeline (demo)
Coloque seus arquivos em data/samples/ (ou use caminhos absolutos) e rode:

python -m src.main --video data/samples/video_demo.mp4 --audio data/samples/audio_demo.wav
Saídas esperadas
Relatórios em docs/evidencias/ (Markdown + JSON)

Logs/alertas no terminal

4) Estrutura do projeto
hercare-ai/
  docs/
    RELATORIO_TECNICO.md
    evidencias/
  data/
    raw/
      video/
        m2cai16-tool-locations/         # dataset bruto (VOC)
    processed/
      yolo_m2cai16/                     # dataset pronto (YOLO)
        images/
          train/
          val/
        labels/
          train/
          val/
        dataset.yaml
      video_alerts/
        video_alerts.json               # alertas/anomalias do vídeo
    samples/
      video_demo.mp4
      audio_demo.wav
  runs/
    detect/
      train*/                           # outputs do treino
        weights/best.pt
        results.png
      **/predict*/                      # outputs do predict (imagens com box + labels)
  src/
    main.py
    video/
      prepare_yolo_dataset.py           # VOC -> YOLO
      video_anomaly_rules.py            # regras de anomalia (gera JSON)
    audio/
    text/
    fusion/
      # fusão multimodal (vídeo+áudio+texto) e relatório final
    utils/
      # utilidades
5) Módulo de Vídeo — YOLOv8 customizado + Anomalias
Este módulo cumpre a parte de análise de vídeo usando YOLOv8 custom para detectar instrumentos cirúrgicos em frames e gerar anomalias por regras com base na sequência de detecções.

5.1 Dataset e rótulos (VOC)
O dataset (M2CAI16 Tool Locations) vem no formato VOC:

JPEGImages/*.jpg → frames

Annotations/*.xml → “gabarito” com:

classe do objeto (ex.: Grasper)

bounding box (xmin, ymin, xmax, ymax)

Exemplo (VOC XML):

<name>Grasper</name> diz o que é

<bndbox>...</bndbox> diz onde está na imagem

5.2 Preparar dataset (VOC → YOLO)
Script:

src/video/prepare_yolo_dataset.py

O que faz:

lê XML VOC

converte para labels YOLO (labels/*.txt)

copia imagens para images/train e images/val

cria dataset.yaml com classes e caminhos

Rodar:

python .\src\video\prepare_yolo_dataset.py
Saída:

data/processed/yolo_m2cai16/images/*

data/processed/yolo_m2cai16/labels/*

data/processed/yolo_m2cai16/dataset.yaml

5.3 Treinar o YOLOv8 (custom)
Exemplo (treino leve):

yolo detect train data=data/processed/yolo_m2cai16/dataset.yaml model=yolov8n.pt epochs=8 imgsz=416 batch=8 workers=0 device=cpu
Artefatos principais:

runs/detect/train*/weights/best.pt (modelo treinado)

runs/detect/train*/results.png (métricas/curvas)

5.4 Inferência (predict) em imagens novas
Rodar inferência nos frames de validação (salvando .txt por imagem):

yolo detect predict model=runs/detect/train*/weights/best.pt \
  source=data/processed/yolo_m2cai16/images/val \
  save=True save_txt=True imgsz=416 conf=0.25
Saídas:

runs/detect/**/predict*/ → imagens com bounding boxes desenhadas

runs/detect/**/predict*/labels/*.txt → detecções por frame (classe + box + conf)

Observação: em alguns casos o Ultralytics pode salvar em caminho “duplicado” (runs/detect/runs/detect/predict). Basta apontar o script de regras para a pasta correta.

5.5 Anomalias por regras (alertas do vídeo)
Script:

src/video/video_anomaly_rules.py

Ele lê os .txt do predict/labels e aplica regras simples para gerar alertas:

Regras implementadas
CRITICAL_INSTRUMENT: se aparecer SpecimenBag → alerta crítico

MANY_TOOLS_SIMULTANEOUS: ≥ 3 instrumentos simultâneos por ≥ 25 frames

PROLONGED_TOOL_USAGE: instrumento presente continuamente por ≥ 75 frames
(tempo estimado com FPS=25)

Rodar:

python .\src\video\video_anomaly_rules.py
Saída:

data/processed/video_alerts/video_alerts.json

Exemplo de alerta:

{
  "type": "CRITICAL_INSTRUMENT",
  "class": "SpecimenBag",
  "start_frame": 30,
  "end_frame": 39,
  "start_time_sec": 1.2,
  "end_time_sec": 1.56
}
6) O que mostrar na apresentação (rápido e objetivo)
Um XML VOC → “como o modelo aprende (classe + box)”

Uma imagem do predict com box → “modelo detectando instrumentos”

video_alerts.json → “anomalia = regra em cima das detecções por frame”

7) Privacidade e segurança (resumo)
Chaves de API ficam em .env e não devem ser commitadas.

Por padrão, o projeto gera métricas derivadas e relatórios sem identificação pessoal.

A demonstração pode ser feita com dados anonimizados/sintéticos.


##  Integrantes do Grupo
-   Nathan
-   Denys
-   Fernanda

##  Referências
-   FIAP -- Pós IA para Desenvolvedores

##  Links 
Git Hub: https://github.com/TechChallenge-FIAP-Grupo-6/tech-challenge-fase4
Youtube: https://youtu.be/2PAf3nd-V3U
