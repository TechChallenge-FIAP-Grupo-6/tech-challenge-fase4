# HerCare AI — Tech Challenge FIAP (Fase 4)

Protótipo multimodal (vídeo + áudio + texto) para monitoramento preventivo em saúde da mulher, com detecção de anomalias, fusão de evidências e geração de relatórios e alertas.

> **Observação importante (Azure):** este projeto roda localmente e integra com **Azure Speech-to-Text** via API. Para a demonstração completa, configure `AZURE_SPEECH_KEY` e `AZURE_SPEECH_REGION` no `.env` (não versionar).

## Requisitos atendidos (mapeamento rápido)
- ✅ **Análise de vídeo** com detecção por YOLOv8 (Ultralytics) e geração de achados/alertas.
- ✅ **Análise de áudio** com transcrição via Azure Speech-to-Text + features de voz + score de anomalia.
- ✅ **Texto** analisado a partir da transcrição (regras de risco) e incluído na fusão multimodal.
- ✅ **Fusão multimodal** (vídeo + áudio + texto) → `RiskScore` final e relatório.
- ✅ **Boas práticas de segurança**: chaves via `.env`, sem dados sensíveis no Git.

---

## 1) Instalação

### 1.1 Criar ambiente virtual
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 1.2 Instalar dependências
```bash
pip install -r requirements.txt
```

## 2) Configurar Azure Speech-to-Text
Crie um arquivo `.env` na raiz (use `.env.example` como base) e preencha:

- `AZURE_SPEECH_KEY=...`
- `AZURE_SPEECH_REGION=...`

> Se as variáveis não estiverem definidas, o projeto roda em **modo demo** com transcrição simulada (para não travar). Para a entrega FIAP, recomenda-se demonstrar a integração real.

## 3) Executar pipeline (demo)
Coloque seus arquivos em `data/samples/` (ou use caminhos absolutos) e rode:

```bash
python -m src.main --video data/samples/video_demo.mp4 --audio data/samples/audio_demo.wav
```

### Saídas
- Relatórios em `docs/evidencias/` (Markdown + JSON)
- Logs/alertas no terminal

## 4) Estrutura do projeto
```
hercare-ai/
  docs/
    RELATORIO_TECNICO.md
    evidencias/
  data/
    samples/
  src/
    video/
    audio/
    text/
    fusion/
    utils/
    main.py
```

## 5) Privacidade e segurança (resumo)
- Chaves de API ficam em `.env` e **não** devem ser commitadas.
- Por padrão, o projeto gera **métricas derivadas** e relatórios sem identificação pessoal.
- A demonstração pode ser feita com dados anonimizados/sintéticos.
