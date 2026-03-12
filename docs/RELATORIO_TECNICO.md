# Relatório Técnico — HerCare AI (Tech Challenge FIAP — Fase 4)

## 1. Visão Geral
O **HerCare AI** é um protótipo multimodal (vídeo + áudio + texto) voltado ao monitoramento preventivo em saúde da mulher. O sistema processa dados clínicos multimodais para identificar **sinais precoces de risco** e gerar **alertas** e **relatórios automáticos** que apoiam a equipe especializada.

> **Importante:** Este protótipo não substitui avaliação clínica. O objetivo é demonstrar integração e técnicas de IA para apoio ao monitoramento.

## 2. Objetivos atendidos (conforme enunciado)
O projeto atende aos objetivos abaixo:
- **Detectar precocemente riscos** em saúde materna e ginecológica (via indicadores de vídeo e voz).
- **Monitorar bem-estar psicológico** por sinais vocais e linguísticos (pausas, hesitação, termos de risco).
- **Utilizar serviços gerenciados em nuvem (Azure)** para ampliar capacidades especializadas (Speech-to-Text).
- **Aplicar detecção de anomalias** para monitoramento preventivo (scores + limiares + alertas).

## 3. Fluxo Multimodal (Pipeline)
### 3.1 Entradas
- **Vídeo (mp4):** vídeos de consultas/procedimentos/fisioterapia/triagem.
- **Áudio (wav):** gravações de consultas especializadas.
- **Texto:** transcrição do áudio (gerada via Azure Speech-to-Text).

### 3.2 Processamento de Vídeo (YOLOv8)
**Objetivo:** detecção de objetos/sinais visuais relevantes no contexto clínico, para gerar indicadores e possíveis anomalias.

**Etapas:**
1. Extração de frames em intervalos regulares.
2. Inferência com **YOLOv8 (Ultralytics)**.
3. Cálculo de métricas: quantidade de detecções, confiança média, variação temporal.
4. Geração de **score de risco de vídeo** e **flags** por limiar.

**Modelo aplicado:** YOLOv8 (com possibilidade de fine-tuning/treino customizado).  
**Saída:** `risk_video` (0–1), `findings_video`.

### 3.3 Processamento de Áudio (Voz)
**Objetivo:** extrair sinais vocais relacionados a estresse/hesitação e produzir indicadores que possam sugerir risco ou desconforto.

**Etapas:**
1. Transcrição via **Azure Speech-to-Text** (quando configurado).
2. Extração de features com `librosa`:
   - energia (RMS), zero crossing rate, MFCCs, pitch aproximado (via energia/variação espectral)
   - estimativa de pausas (janela de silêncio)
3. Normalização e cálculo de **score de anomalia** (IsolationForest ou heurística).
4. Geração de **risk_audio** (0–1) e achados textuais do áudio (ex.: “pausas elevadas”).

**Modelo aplicado:** detecção de anomalia clássica (IsolationForest) + heurísticas interpretáveis.  
**Saída:** `risk_audio` (0–1), `transcript`, `findings_audio`.

### 3.4 Processamento de Texto (Transcrição)
**Objetivo:** analisar a transcrição para identificar padrões linguísticos associados a risco (ansiedade, medo, relato de dor intensa, etc.), sem expor dados sensíveis.

**Etapas:**
1. Normalização (lowercase, remoção leve de pontuação).
2. Regras de risco por palavras/expressões (dicionário controlado).
3. Cálculo de `risk_text` (0–1) e lista de gatilhos detectados.

**Saída:** `risk_text` (0–1), `findings_text`.

### 3.5 Fusão Multimodal (Video + Audio + Text)
**Objetivo:** combinar evidências para produzir um **RiskScore final** e alertas.

**Método:**
- Combinação ponderada: `risk_final = wv*risk_video + wa*risk_audio + wt*risk_text`
- Pesos default: vídeo 0.40, áudio 0.40, texto 0.20 (ajustável)

**Saída final:**
- `risk_final` (0–1)
- classificação: baixo / moderado / alto
- alertas e justificativas (quais sinais contribuíram)

## 4. Integração com Azure (Cognitive Services)
Serviço utilizado:
- **Azure Speech-to-Text** (Cognitive Services / Speech)

Uso:
- Transcrição do áudio clínico para habilitar análise textual, auditoria e relatórios.

Segurança e privacidade:
- Chaves e região via variáveis de ambiente (`.env`).
- Recomenda-se não persistir áudios brutos em nuvem (modo demo local).
- Relatórios gerados não contêm identificação pessoal.

## 5. Resultados e evidências
O pipeline gera automaticamente:
- Relatório **Markdown** com achados, scores e alertas.
- Relatório **JSON** com estrutura para integração futura com dashboards.
- (Opcional) Frames com bounding boxes do YOLO para evidência visual.

Exemplos de achados:
- **Vídeo:** presença/ausência de detecções esperadas e variações abruptas → alerta.
- **Áudio:** aumento de pausas e variação de energia → alerta de estresse/hesitação.
- **Texto:** termos de risco detectados → elevação do score textual.

As evidências do experimento devem ser anexadas em `docs/evidencias/`.

## 6. Limitações e próximos passos
- Dataset reduzido e demonstração controlada.
- Próximas evoluções:
  - Treinamento customizado YOLOv8 com dataset rotulado por domínio.
  - Ajuste de pesos e calibração do RiskScore com validação supervisionada.
  - Dashboard para equipe clínica e trilhas de auditoria.

