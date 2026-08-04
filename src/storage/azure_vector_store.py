from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.search.documents.models import VectorizedQuery

from src.config import AZURE_COGNITIVE_SEARCH_API_KEY, AZURE_COGNITIVE_SEARCH_ENDPOINT, AZURE_COGNITIVE_SEARCH_INDEX_NAME


def create_search_client() -> SearchClient:
    credential = AzureKeyCredential(AZURE_COGNITIVE_SEARCH_API_KEY)
    return SearchClient(endpoint=AZURE_COGNITIVE_SEARCH_ENDPOINT, index_name=AZURE_COGNITIVE_SEARCH_INDEX_NAME, credential=credential)


def create_index():
    client = SearchIndexClient(endpoint=AZURE_COGNITIVE_SEARCH_ENDPOINT, credential=AzureKeyCredential(AZURE_COGNITIVE_SEARCH_API_KEY))

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="hnsw-config")
        ],
        profiles=[
            VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")
        ],
    )

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="vector-profile",
        ),
        SimpleField(name="var", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="categories", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True, facetable=True),
        SimpleField(name="year_start", type=SearchFieldDataType.Int32, filterable=True, facetable=True),
        SimpleField(name="year_end", type=SearchFieldDataType.Int32, filterable=True, facetable=True),
        SimpleField(name="response_options", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
        SimpleField(name="responses_by_year", type=SearchFieldDataType.String),
    ]

    index = SearchIndex(
        name=AZURE_COGNITIVE_SEARCH_INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )

    try:
        client.create_index(index)
        print(f"Created Azure Cognitive Search index: {AZURE_COGNITIVE_SEARCH_INDEX_NAME}")
    except Exception as exc:
        if "already exists" in str(exc).lower():
            print(f"Index already exists: {AZURE_COGNITIVE_SEARCH_INDEX_NAME}")
        else:
            raise


def create_or_update_index():
    client = SearchIndexClient(endpoint=AZURE_COGNITIVE_SEARCH_ENDPOINT, credential=AzureKeyCredential(AZURE_COGNITIVE_SEARCH_API_KEY))
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="hnsw-config")
        ],
        profiles=[
            VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")
        ],
    )

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="vector-profile",
        ),
        SimpleField(name="var", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="categories", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True, facetable=True),
        SimpleField(name="year_start", type=SearchFieldDataType.Int32, filterable=True, facetable=True),
        SimpleField(name="year_end", type=SearchFieldDataType.Int32, filterable=True, facetable=True),
        SimpleField(name="response_options", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
        SimpleField(name="responses_by_year", type=SearchFieldDataType.String),
    ]

    index = SearchIndex(
        name=AZURE_COGNITIVE_SEARCH_INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )

    client.create_or_update_index(index)
    print(f"Created or updated Azure Cognitive Search index: {AZURE_COGNITIVE_SEARCH_INDEX_NAME}")


def upload_documents(documents: list[dict]):
    client = create_search_client()
    result = client.upload_documents(documents)
    print(f"Uploaded {len(documents)} documents to {AZURE_COGNITIVE_SEARCH_INDEX_NAME}")
    return result


def query_vectors(query_embedding: list[float], query_text: str | None = None, top_k: int = 5):
    client = create_search_client()
    try:
        # Newer SDKs
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="content_vector",
        )
    except TypeError:
        # Older SDKs
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k=top_k,
            fields="content_vector",
        )

    # Coded/implicit bias phrasing (e.g. "surprisingly articulate given his
    # background") rarely resembles the literal wording of GSS survey
    # questions, so pure vector search alone can surface weakly-related
    # "evidence". Passing the raw query text alongside the vector enables
    # Azure AI Search's hybrid ranking (BM25 keyword + vector, RRF-fused),
    # which measurably improves match quality without losing semantic
    # matches for queries that vector search alone handles well.
    results = client.search(
        search_text=query_text if query_text else "*",
        vector_queries=[vector_query],
        top=top_k,
        select=["id", "content", "var", "categories", "year_start", "year_end", "response_options", "responses_by_year"],
    )
    return [
        {
            "id": result.get("id"),
            "content": result.get("content"),
            "var": result.get("var"),
            "categories": result.get("categories"),
            "year_start": result.get("year_start"),
            "year_end": result.get("year_end"),
            "response_options": result.get("response_options"),
            "responses_by_year": result.get("responses_by_year"),
        }
        for result in results
    ]
