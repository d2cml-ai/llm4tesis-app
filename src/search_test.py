import streamlit as st
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery

def get_embeddings(text: str, embedding_client: AzureOpenAI) -> list[float]:
    # There are a few ways to get embeddings. This is just one example.
    embedding = embedding_client.embeddings.create(input=[text], model="text-embedding-3-small")
    return embedding.data[0].embedding

def main() -> None:

        embedding_client: AzureOpenAI = AzureOpenAI(
                azure_endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"],
                azure_deployment = st.secrets["EMBEDDINGS_DEPLOYMENT"],
                api_version = "2024-02-01",
                api_key = st.secrets["OPENAI_API_KEY"]
        )
        generation_client: AzureOpenAI = AzureOpenAI(
                azure_endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"],
                azure_deployment = st.secrets["GENERATION_DEPLOYMENT"],
                api_version = "2024-02-01",
                api_key = st.secrets["OPENAI_API_KEY"]
        )
        search_client: SearchClient = SearchClient(
                st.secrets["SEARCH_ENDPOINT"],
                st.secrets["INDEX_NAME"],
                AzureKeyCredential(st.secrets["AZURE_SEARCH_API_KEY"])
        )

        query: str = "desigualdad de ingresos"

        embedded_query: list[float] = get_embeddings(query, embedding_client)
        vector_query: VectorizedQuery = VectorizedQuery(
              vector = embedded_query,
              fields = "vector",
              exhaustive = True,
              k_nearest_neighbors = 3,
        )
        results = search_client.search(
              vector_queries = [vector_query],
              select = ["title", "author", "url", "text"]

        )
        print(type(results))
        for result in results:
              print(result)
              print(type(result))

if __name__ == "__main__":
        try:
               main()
        except Exception as e:
               raise e