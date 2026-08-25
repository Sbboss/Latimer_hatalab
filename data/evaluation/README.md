# ISSP retrieval evaluation set

`issp_retrieval_gold.json` contains user-style paraphrases and manually checked
relevant ISSP record IDs. It is intentionally separate from the source question
wording so exact string matching cannot masquerade as semantic retrieval quality.

Run the dependency-free lexical sanity baseline:

```bash
python -m src.retrieval.evaluate --mode lexical --top-k 5
```

After setting Azure/OpenAI environment variables and ingesting ISSP, run the
actual hybrid/semantic pipeline:

```bash
python -m src.retrieval.evaluate --mode live --top-k 5
```

The report includes Recall@k, MRR, and nDCG@k. Add failure-derived queries to
this file over time; never tune against only the successful examples.
