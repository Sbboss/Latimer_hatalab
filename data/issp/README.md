# Tagged ISSP question corpus

`issp_questions_tagged.json` is the deployment-ready, canonical export used by
the Azure AI Search ingestion pipeline. It contains all 532 supplied ISSP
questions, their formal multi-label annotations, survey metadata, and explicit
annotation-quality states.

The canonical file intentionally excludes annotator names and timestamps. The
original `ISSP Tagged.zip` remains outside this repository and is not modified
or committed.

Regenerate both tracked artifacts from the original ZIP:

```bash
python -m src.data.issp_ingest \
  --zip "/path/to/ISSP Tagged.zip"
```

The command fails on duplicate IDs, orphan annotations, missing question text,
or inconsistent wave/country counts. It never drops unannotated or uncertain
questions; see `validation_report.json` for the exact coverage.

Important: this corpus contains harmonized question wording and availability
metadata, not per-wave response percentages. `available_waves` proves that a
question is comparable across listed waves; it must not be rendered as a public
opinion trend without separate response data.
