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

Latimer AI Bias is a **multi‑model bias analysis system** that evaluates text using multiple LLMs and grounds explanations using **General Social Survey (GSS) data retrieved via Azure AI Search**.

The system highlights potentially biased phrases, explains why they may signal bias, and supports **model‑to‑model comparison** of bias detection.

---

# System Overview

The system consists of three main layers:

Frontend (React + Vite)
- interactive bias analysis UI
- phrase highlighting
- model comparison tabs
- bias cockpit visualization

Backend (FastAPI)
- multi‑model LLM inference
- RAG pipeline using GSS data
- phrase detection and scoring
- Azure AI Search vector retrieval

Data Layer
- General Social Survey dataset
- Azure AI Search vector index
- survey‑grounded reasoning

---

# Architecture

User Text
	↓
Embedding (Azure OpenAI)
	↓
Azure AI Search Vector Retrieval
	↓
RAG Prompt Construction
	↓
Multi‑Model Analysis
	↓
Structured Bias Output
	↓
Frontend Visualization

---

# Repository Structure

```
latimer-ai-bias/

frontend/                React UI
src/
	api/                  FastAPI endpoints
	data/                 ingestion + normalization
	llm/                  Azure model clients
	retrieval/            RAG orchestration
	storage/              Azure vector store

data/                    processed datasets
notebooks/               exploration
legacy/                  prototype artifacts

streamlit_app.py         model comparison UI
requirements.txt
pyproject.toml
```

---

# Features

Multi‑model bias analysis
- GPT‑5.5
- Claude Opus
- Llama 3
- DeepSeek

Phrase detection
- identifies bias trigger phrases
- highlights spans directly in text

RAG‑grounded explanations
- retrieves relevant GSS survey questions
- explanations reference empirical social data

Model comparison
- compare bias scores across models
- inspect different reasoning paths

Interactive cockpit
- bias strength score
- bias dimension breakdown
- suggested rewrite

---

# Environment Setup

Copy environment template

```
cp .env.example .env
```

Example configuration

```
AZURE_API_KEY=...
AZURE_ENDPOINT=https://<resource>.services.ai.azure.com/openai/v1
AZURE_ANTHROPIC_ENDPOINT=https://<resource>.services.ai.azure.com/anthropic

AZURE_DEFAULT_MODEL=GPT-5.5

AZURE_MODEL_DEPLOYMENTS_JSON={"GPT-5.5":"gpt-5.5","Claude-Opus-4.6":"claude-opus-4-6","Llama-3.3-70B-Instruct":"Llama-3.3-70B-Instruct","DeepSeek-V4-Pro":"DeepSeek-V4-Pro"}
```

---

# Running the Backend

Install dependencies

```
pip install -r requirements.txt
```

Start FastAPI server

```
uvicorn src.api.fastapi_app:app --reload
```

Server runs at

```
http://127.0.0.1:8000
```

---

# Running the Frontend

```
cd frontend
npm install
npm run dev
```

Open

```
http://localhost:5173
```

---

# Optional Streamlit Model Comparison UI

Run:

```
streamlit run streamlit_app.py
```

This interface lets you test prompts across all configured models side‑by‑side.

---

# Data Source

The bias reasoning pipeline is grounded using the **General Social Survey (GSS)** dataset.

The vector index stores:

- survey questions
- categories
- year ranges
- response options

These are retrieved during analysis and used to ground model reasoning.

---

# Future Improvements

- stronger JSON output enforcement
- richer timeline evidence visualization
- improved phrase alignment across models
- evaluation metrics for model bias detection

---

# License

Research / academic use.

