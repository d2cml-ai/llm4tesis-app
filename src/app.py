from azure.search.documents import SearchClient, SearchItemPaged
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI, Stream
import streamlit as st
from Constants import CONTEXT_TEMPLATE, SYSTEM_PROMPT

def get_embeddings(text: str, embedding_client: AzureOpenAI) -> list[float]:
    embedding = embedding_client.embeddings.create(input=[text], model="text-embedding-3-small")
    return embedding.data[0].embedding

def get_relevant_chunks(prompt: str) -> SearchItemPaged[dict[str, str | list[str]]]:
        embedding_client = AzureOpenAI(
                azure_endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"],
                azure_deployment = st.secrets["EMBEDDINGS_DEPLOYMENT"],
                api_version = "2024-02-01",
                api_key = st.secrets["OPENAI_API_KEY"]
        )
        search_client = SearchClient(
                st.secrets["SEARCH_ENDPOINT"],
                st.secrets["INDEX_NAME"],
                AzureKeyCredential(st.secrets["AZURE_SEARCH_API_KEY"])
        )
        embedded_query: list[float] = get_embeddings(prompt, embedding_client)
        vector_query: VectorizedQuery = VectorizedQuery(
              vector = embedded_query,
              fields = "vector",
              exhaustive = True,
              k_nearest_neighbors = 3,
        )
        results = search_client.search(
              vector_queries = [vector_query],
              select = ["title", "author", "url", "abstract"]
        )
        return results

def process_relevant_chunks(relevant_chunks: SearchItemPaged[dict[str, str | list[str]]]) -> str:
        formatted_context: str = ""
        for index, result in enumerate(relevant_chunks):
                
                formatted_context += f"Document {index + 1}: \n"
                formatted_context += CONTEXT_TEMPLATE.format(
                        title = result["title"],
                        author = result["author"],
                        abstract = result["abstract"],
                        url = result["url"]
                )
                formatted_context += "\n\n"
        return formatted_context

def generate_response(prompt: str, messages: list[dict[str, str]]) -> Stream:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        relevant_chunks: SearchItemPaged[dict[str, str | list[str]]] = get_relevant_chunks(prompt)
        formatted_context: str = process_relevant_chunks(relevant_chunks)
        query_with_context = f"Query: {prompt}\nDocuments:\n{formatted_context}"
        messages_with_context = messages + [{"role": "user", "content": query_with_context}]
        generation_client: AzureOpenAI = AzureOpenAI(
                        azure_endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"],
                        azure_deployment = st.secrets["GENERATION_DEPLOYMENT"],
                        api_version = "2024-02-01",
                        api_key = st.secrets["OPENAI_API_KEY"]
                )
        response = generation_client.chat.completions.create(
                messages = messages_with_context,
                model = "gpt-4",
                stream = True
        )
        return response



def get_response() -> None:
        if st.session_state.prompt == "":
                return
        for message in st.session_state.chat_history[1:]:
                with st.chat_message(message["role"]):
                        st.markdown(message["content"])
        with st.chat_message("user"):
                st.write(st.session_state.prompt)
        response = generate_response(st.session_state.prompt, st.session_state.chat_history.copy())
        with st.chat_message("assistant"):
                assistant_message = st.write_stream(response)
        st.session_state.chat_history.append({
                "role": "assistant",
                "content": assistant_message
        })

        

def main() -> None:
        if "chat_history" not in st.session_state:
                st.session_state.chat_history = [{
                        "role": "system",
                        "content": SYSTEM_PROMPT
                }]
        
        if "stream" not in st.session_state:
                st.session_state.stream = None
        
        
        if prompt := st.chat_input(
                key = "prompt",
        ):
                get_response()

if __name__ == "__main__":
        try:
                main()
        except Exception as e:
                raise e

        
