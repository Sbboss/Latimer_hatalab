from src.llm.azure_openai_client import openai_client, create_embedding
from src.storage.azure_vector_store import query_vectors


def main():
    query = "People should have equal rights regardless of race"

    print("Creating embedding for query...")
    client = openai_client()
    embedding = create_embedding(client, query)

    print("Querying Azure Cognitive Search vector index...\n")
    results = query_vectors(embedding, top_k=5)

    print("Top retrieved documents:\n")

    for i, r in enumerate(results, start=1):
        print(f"Result {i}")
        print("ID:", r.get("id"))
        print("Question:", r.get("content"))
        print("Categories:", r.get("categories"))
        print("Years:", r.get("year_start"), "-", r.get("year_end"))
        print("Options:", r.get("response_options"))
        print("-" * 60)


if __name__ == "__main__":
    main()
