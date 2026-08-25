"""Azure AI Search schema, safe incremental upload, and ranked retrieval."""

from __future__ import annotations

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from src.config import (
    AZURE_COGNITIVE_SEARCH_API_KEY,
    AZURE_COGNITIVE_SEARCH_ENDPOINT,
    AZURE_COGNITIVE_SEARCH_INDEX_NAME,
    AZURE_COGNITIVE_SEARCH_SEMANTIC_CONFIG_NAME,
    AZURE_COGNITIVE_SEARCH_SEMANTIC_ENABLED,
    AZURE_COGNITIVE_SEARCH_VECTOR_CANDIDATES,
)


LEGACY_SELECT_FIELDS = [
    "id",
    "content",
    "var",
    "categories",
    "year_start",
    "year_end",
    "response_options",
    "responses_by_year",
]

METADATA_SELECT_FIELDS = LEGACY_SELECT_FIELDS + [
    "question_text",
    "source_survey",
    "module_name",
    "source_dataset",
    "available_waves",
    "countries",
    "country_count",
    "wave_count",
    "cross_wave_question_available",
    "limitations",
    "annotation_status",
    "annotation_uncertain",
    "annotation_notes",
]


def _credential() -> AzureKeyCredential:
    if not AZURE_COGNITIVE_SEARCH_ENDPOINT or not AZURE_COGNITIVE_SEARCH_API_KEY:
        raise ValueError(
            "AZURE_COGNITIVE_SEARCH_ENDPOINT and AZURE_COGNITIVE_SEARCH_API_KEY must be set"
        )
    return AzureKeyCredential(AZURE_COGNITIVE_SEARCH_API_KEY)


def create_search_client() -> SearchClient:
    return SearchClient(
        endpoint=AZURE_COGNITIVE_SEARCH_ENDPOINT,
        index_name=AZURE_COGNITIVE_SEARCH_INDEX_NAME,
        credential=_credential(),
    )


def _index_fields() -> list:
    """Keep the legacy schema intact and add only backward-compatible fields."""

    return [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            analyzer_name="en.lucene",
        ),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="vector-profile",
        ),
        SimpleField(
            name="var",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="categories",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="year_start",
            type=SearchFieldDataType.Int32,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="year_end",
            type=SearchFieldDataType.Int32,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="response_options",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
        ),
        SimpleField(name="responses_by_year", type=SearchFieldDataType.String),
        SearchableField(name="question_text", type=SearchFieldDataType.String),
        SimpleField(
            name="source_survey",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SearchableField(
            name="module_name",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="source_dataset",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="available_waves",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="countries",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
        ),
        SimpleField(
            name="country_count",
            type=SearchFieldDataType.Int32,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="wave_count",
            type=SearchFieldDataType.Int32,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="cross_wave_question_available",
            type=SearchFieldDataType.Boolean,
            filterable=True,
        ),
        SimpleField(name="limitations", type=SearchFieldDataType.String),
        SimpleField(
            name="annotation_status",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="annotation_uncertain",
            type=SearchFieldDataType.Boolean,
            filterable=True,
        ),
        SimpleField(name="annotation_notes", type=SearchFieldDataType.String),
    ]


def _index_definition() -> SearchIndex:
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ],
    )
    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name=AZURE_COGNITIVE_SEARCH_SEMANTIC_CONFIG_NAME,
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="question_text"),
                    content_fields=[SemanticField(field_name="content")],
                ),
            )
        ]
    )
    return SearchIndex(
        name=AZURE_COGNITIVE_SEARCH_INDEX_NAME,
        fields=_index_fields(),
        vector_search=vector_search,
        semantic_search=semantic_search,
    )


def create_index() -> None:
    create_or_update_index()


def create_or_update_index() -> None:
    """Add metadata fields/configuration without deleting indexed documents."""

    client = SearchIndexClient(
        endpoint=AZURE_COGNITIVE_SEARCH_ENDPOINT,
        credential=_credential(),
    )
    client.create_or_update_index(_index_definition())
    print(f"Created or incrementally updated index: {AZURE_COGNITIVE_SEARCH_INDEX_NAME}")


def upload_documents(documents: list[dict]):
    """Upload idempotent documents and fail if Azure rejects any individual row."""

    client = create_search_client()
    results = client.upload_documents(documents)
    failures = [
        result
        for result in results
        if not getattr(result, "succeeded", False)
    ]
    if failures:
        details = [
            {
                "key": getattr(result, "key", None),
                "error": getattr(result, "error_message", None),
            }
            for result in failures
        ]
        raise RuntimeError(f"Azure AI Search rejected documents: {details}")
    return results


def list_indexed_document_ids(source_survey: str) -> set[str]:
    """Read back every indexed ID for one survey for post-upload verification."""

    escaped_source = source_survey.replace("'", "''")
    results = create_search_client().search(
        search_text="*",
        filter=f"source_survey eq '{escaped_source}'",
        select=["id"],
    )
    return {
        str(result["id"])
        for result in results
        if result.get("id") is not None
    }


def _run_search(
    client: SearchClient,
    *,
    vector_query: VectorizedQuery,
    query_text: str | None,
    top_k: int,
    semantic: bool,
    select_fields: list[str],
) -> list[dict]:
    kwargs = {
        "search_text": query_text if query_text else "*",
        "vector_queries": [vector_query],
        "top": top_k,
        "select": select_fields,
    }
    if semantic and query_text:
        kwargs.update(
            {
                "query_type": "semantic",
                "semantic_configuration_name": AZURE_COGNITIVE_SEARCH_SEMANTIC_CONFIG_NAME,
                "query_caption": "extractive",
            }
        )
    return list(client.search(**kwargs))


def query_vectors(
    query_embedding: list[float],
    query_text: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    client = create_search_client()
    use_semantic = AZURE_COGNITIVE_SEARCH_SEMANTIC_ENABLED and bool(query_text)
    candidate_count = (
        max(top_k, AZURE_COGNITIVE_SEARCH_VECTOR_CANDIDATES)
        if use_semantic
        else top_k
    )
    try:
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=candidate_count,
            fields="content_vector",
        )
    except TypeError:
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k=candidate_count,
            fields="content_vector",
        )

    attempts = []
    if use_semantic:
        attempts.append((True, METADATA_SELECT_FIELDS))
    attempts.extend(
        [
            (False, METADATA_SELECT_FIELDS),
            (False, LEGACY_SELECT_FIELDS),
        ]
    )

    raw_results: list[dict] | None = None
    last_error: HttpResponseError | None = None
    for semantic, fields in attempts:
        try:
            raw_results = _run_search(
                client,
                vector_query=vector_query,
                query_text=query_text,
                top_k=top_k,
                semantic=semantic,
                select_fields=fields,
            )
            break
        except HttpResponseError as exc:
            last_error = exc

    if raw_results is None:
        assert last_error is not None
        raise last_error

    normalized: list[dict] = []
    for result in raw_results:
        record_id = result.get("id")
        source_survey = result.get("source_survey") or (
            "ISSP" if str(record_id).startswith("ISSP_") else "GSS"
        )
        normalized.append(
            {
                field: result.get(field)
                for field in METADATA_SELECT_FIELDS
            }
            | {
                "source_survey": source_survey,
                "search_score": result.get("@search.score"),
                "reranker_score": result.get("@search.reranker_score"),
            }
        )
    return normalized
