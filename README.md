# Latimer AI Bias

Latimer AI Bias is a multi-model learning application that helps people notice and examine possible bias in their own language. It compares how different LLMs interpret the same text and grounds explanations in attributable General Social Survey (GSS) and International Social Survey Programme (ISSP) questions.

It combines a React frontend, a FastAPI backend, Azure AI Search retrieval, and multiple hosted models so you can inspect where the models agree, where they disagree, and how strongly they score bias signals.

## Hugging Face Deployment Metadata

The Hugging Face Space configuration now lives in `hf_space_metadata.yml` instead of at the top of this README. The sync workflow prepends that metadata only when publishing to Hugging Face, so this GitHub README stays clean and readable.

## What The App Does

- Runs the same input across multiple models
- Produces a structured bias score and category breakdown for each model
- Highlights trigger phrases directly in the input text
- Asks a non-accusatory reflection question before suggesting a rewrite
- Suggests more neutral rewrites
- Retrieves category-aligned GSS and ISSP survey items through Azure AI Search
- Shows survey, module, wave, country coverage, and annotation-quality metadata
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
  -> Optional semantic reranking with safe hybrid fallback
  -> RAG prompt assembly with GSS + ISSP evidence boundaries
  -> Parallel analysis across all configured models
  -> Structured JSON output
  -> Frontend comparison view with scores, highlights, and reasoning
```

## Repository Structure

```text
latimer-ai-bias/
├── frontend/                 React + Vite app
├── data/
│   ├── issp/                 canonical tagged ISSP corpus + validation report
│   └── evaluation/           retrieval gold queries
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
AZURE_COGNITIVE_SEARCH_SEMANTIC_ENABLED=true
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

## ISSP Data And Ingestion

The tracked canonical corpus contains all 532 supplied ISSP questions. It keeps formal multi-label tags and explicit states for uncertain, unlabeled, and unannotated records, while excluding annotator identities. The original ZIP remains outside the repository.

Validate the deployment payload without cloud access:

```bash
python -m src.data.azure_ingest --source issp --dry-run
```

With Azure/OpenAI variables configured, incrementally add ISSP documents to the existing index:

```bash
python -m src.data.azure_ingest --source issp
```

The operation uses stable `ISSP_...` IDs, adds only backward-compatible metadata fields and a semantic configuration, checks every Azure upload result, and never deletes existing GSS documents. Re-running it safely updates the same ISSP records.

Regenerate the canonical artifacts from a new tagging export:

```bash
python -m src.data.issp_ingest --zip "/path/to/ISSP Tagged.zip"
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

The system uses GSS- and ISSP-derived survey content in one Azure AI Search index. Retrieval is hybrid:

- vector similarity from the input embedding
- keyword ranking from the raw query text

Azure's reciprocal-rank fusion combines both result lists. When enabled and supported by the service, semantic ranking reranks 50 candidates; any semantic-service error falls back to the existing hybrid query. Evidence is then aligned to each detected category instead of copying the same top results to every highlight. When no direct match exists, the UI says so rather than presenting tangential evidence.

ISSP records in this export contain question wording and wave/country coverage, not response percentages. The prompt and UI explicitly prevent wave availability from being presented as an opinion trend.

## Reasoning / Thinking Support

Where the provider exposes it, the backend can capture a model's internal reasoning trace:

- OpenAI reasoning-model summaries through the Responses API
- Claude extended/adaptive thinking when supported by the Azure Foundry deployment

If a deployment does not expose a usable reasoning trace, the analysis still returns the normal structured bias result.

## Example Evaluation Files

- `test_case.md` contains seven sample passages
- `test_case_results.md` contains a comparison report across all four configured models
- `data/evaluation/issp_retrieval_gold.json` contains 20 paraphrased ISSP retrieval judgments

These are useful for sanity-checking how consistently the models classify historical text, partisan rhetoric, ethnocentric language, and ambiguous philosophical passages.

Run the dependency-free lexical retrieval baseline:

```bash
python -m src.retrieval.evaluate --mode lexical --top-k 5
```

After ingestion, run the actual Azure hybrid/semantic path with `--mode live`. Both modes report Recall@k, MRR, and nDCG@k.

## Current Limitations

- Indirect or coded bias language can still be harder to ground than direct survey-matched language
- Some models are stricter than others about what counts as political or demographic bias
- Reasoning trace availability depends on the provider and deployment capabilities
- Retrieval quality depends on the coverage and annotation quality of both surveys; rare ISSP labels and uncertain rows remain visibly flagged
- ISSP opinion trends require a separate response dataset; this export supports question retrieval and coverage only

## License

Research / academic use.
