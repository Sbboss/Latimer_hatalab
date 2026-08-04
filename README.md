---
title: Latimer AI Bias
emoji: ⚖️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Latimer AI Bias

Latimer AI Bias is a multi-model bias-analysis application that compares how different LLMs interpret the same text, highlights potentially biased phrasing, and grounds explanations with retrieved General Social Survey (GSS) evidence.

It combines a React frontend, a FastAPI backend, Azure AI Search retrieval, and multiple hosted models so you can inspect where the models agree, where they disagree, and how strongly they score bias signals.

## What The Top Table Is

The YAML block at the top of this file is Hugging Face Space metadata. Hugging Face reads it to configure the Space title, emoji, SDK type, and port, and displays it as a table in the Space UI. It is not part of the app logic.

## What The App Does

- Runs the same input across multiple models
- Produces a structured bias score and category breakdown for each model
- Highlights trigger phrases directly in the input text
- Suggests more neutral rewrites
- Retrieves related GSS survey items through Azure AI Search
- Shows where models agree and where they disagree

## Configured Models

The current environment is set up for:

- `GPT-5.5`
- `Claude-Opus-4.8`
- `Llama-3.3-70B-Instruct`
- `DeepSeek-V4-Pro`

The frontend reads model names dynamically from the backend, so the UI stays aligned with the `.env` configuration.

## High-Level Flow

```text
Input text
  -> Embedding with Azure OpenAI
  -> Hybrid retrieval from Azure AI Search
  -> RAG prompt assembly with GSS evidence
  -> Parallel analysis across all configured models
  -> Structured JSON output
  -> Frontend comparison view with scores, highlights, and reasoning
```

## Repository Structure

```text
latimer-ai-bias/
├── frontend/                 React + Vite app
├── src/
│   ├── api/                  FastAPI endpoints
│   ├── data/                 ingestion and normalization scripts
│   ├── llm/                  model client logic
│   ├── retrieval/            prompt building and retrieval orchestration
│   └── storage/              Azure AI Search integration
├── streamlit_app.py          optional side-by-side model tester
├── test_case.md              sample evaluation inputs
├── test_case_results.md      example cross-model evaluation report
├── requirements.txt
└── pyproject.toml
```

## Environment Setup

Create a local environment file:

```bash
cp .env.example .env
```

Typical configuration looks like this:

```bash
AZURE_API_KEY=...
AZURE_ENDPOINT=https://<resource>.services.ai.azure.com/openai/v1
AZURE_API_VERSION=2024-06-01

AZURE_DEFAULT_MODEL=GPT-5.5
AZURE_MODEL_DEPLOYMENTS_JSON={"DeepSeek-V4-Pro":"DeepSeek-V4-Pro","GPT-5.5":"gpt-5.5","Claude-Opus-4.8":"claude-opus-4-8","Llama-3.3-70B-Instruct":"Llama-3.3-70B-Instruct"}

AZURE_COGNITIVE_SEARCH_ENDPOINT=...
AZURE_COGNITIVE_SEARCH_API_KEY=...
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

If you are using Claude through Azure Foundry, also set:

```bash
AZURE_ANTHROPIC_ENDPOINT=...
AZURE_ANTHROPIC_API_KEY=...
```

## Local Development

### Backend

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI backend:

```bash
uvicorn src.api.fastapi_app:app --reload --port 8001
```

Health check:

```bash
http://127.0.0.1:8001/health
```

### Frontend

Install and run the Vite app:

```bash
cd frontend
npm install
npm run dev
```

Open:

```bash
http://localhost:5174
```

The frontend proxies API requests to the backend on port `8001`.

### Optional Streamlit Comparison UI

```bash
streamlit run streamlit_app.py
```

## API Endpoints

Important backend endpoints:

- `GET /health` and `GET /api/health`
- `GET /ready` and `GET /api/ready`
- `GET /models` and `GET /api/models`
- `POST /analyze` and `POST /api/analyze`
- `POST /bias-query` and `POST /api/bias-query`

`/analyze` runs the full multi-model bias workflow and returns one structured result per model.

## Retrieval And Grounding Notes

The system uses GSS-derived survey content stored in Azure AI Search. Retrieval is hybrid:

- vector similarity from the input embedding
- keyword ranking from the raw query text

This improves matching for direct bias statements and for more coded phrasing. When the retrieved GSS evidence is only loosely related, the prompt now instructs models to say so explicitly instead of overstating the grounding connection.

## Reasoning / Thinking Support

Where the provider exposes it, the backend can capture a model's internal reasoning trace:

- OpenAI reasoning-model summaries through the Responses API
- Claude extended/adaptive thinking when supported by the Azure Foundry deployment

If a deployment does not expose a usable reasoning trace, the analysis still returns the normal structured bias result.

## Example Evaluation Files

- `test_case.md` contains seven sample passages
- `test_case_results.md` contains a comparison report across all four configured models

These are useful for sanity-checking how consistently the models classify historical text, partisan rhetoric, ethnocentric language, and ambiguous philosophical passages.

## Current Limitations

- Indirect or coded bias language can still be harder to ground than direct survey-matched language
- Some models are stricter than others about what counts as political or demographic bias
- Reasoning trace availability depends on the provider and deployment capabilities
- Retrieval quality depends heavily on the coverage and wording of the indexed GSS material

## License

Research / academic use.

