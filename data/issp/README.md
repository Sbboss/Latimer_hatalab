# Tagged ISSP question corpus

`issp_questions_tagged.json` is the deployment-ready canonical export used by
the Azure AI Search ingestion pipeline. It contains all 532 supplied ISSP
questions, formal multi-label annotations, survey metadata, explicit quality
states, and verified response distributions.

The canonical file excludes annotator names and timestamps. The original
`ISSP Tagged.zip` and official GESIS respondent-level files remain outside this
repository. Neither source is modified or committed.

Regenerate both tracked artifacts from the original ZIP:

```bash
python -m src.data.issp_ingest \
  --zip "/path/to/ISSP Tagged.zip"
```

The command fails on duplicate IDs, orphan annotations, missing question text,
or inconsistent wave and country counts. It never drops unannotated or
uncertain questions. If the canonical output exists, the command preserves its
separately verified response fields.

Build distributions from the eight official GESIS Stata downloads:

```bash
python -m pip install -r requirements-data.txt
python scripts/build_issp_response_distributions.py \
  --data-dir "/path/to/official/GESIS/files"
```

The script accepts original `.dta.zip` downloads or extracted `.dta` files. It
matches each tagged `source_question` to the exact source variable, uses the
official `WEIGHT` variable within each country, excludes codes absent from the
published response scale, and calculates the equal-country mean of those
country-level percentages for each year. This prevents countries with larger
samples from dominating the result. These are study-level descriptive results,
not a global population estimate.

`response_base_by_year` records weighted and unweighted bases and the number of
participating country samples. `response_distribution_report.json` records the
source versions, DOIs, file checksums, partial records, and missing records.
The official sources are GESIS cumulative files ZA4747, ZA5960, ZA8790, ZA8792,
ZA8793, ZA8794, ZA8795, and ZA8797.

A wave with no verified valid responses stays absent from
`responses_by_year` and appears in `response_data_missing_waves`. Values are
never inferred or fabricated.
