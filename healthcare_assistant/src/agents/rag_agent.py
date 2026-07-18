import os

from src import config
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

from src.llm_client import call_llm


class RAGAgent:
    """
    RAG Agent:
    Performs semantic search over healthcare policy documents
    using FAISS and generates grounded answers using Ollama LLM.
    """

    def __init__(self, index_path=config.VECTOR_STORE_PATH):

        self.embeddings = OllamaEmbeddings(
            model=config.OLLAMA_EMBEDDING_MODEL
        )


        if not os.path.exists(index_path):

            raise FileNotFoundError(
                f"FAISS index not found at {index_path}. "
                "Run load_policies.py first."
            )


        self.vector_db = FAISS.load_local(
            index_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )


        self.system_instruction = (
            "You are a helpful Hospital Policy Assistant (RAG Agent).\n"
            "Your task is to answer the user's question about hospital policies "
            "using ONLY the provided context snippets.\n\n"

            "Rules:\n"
            "1. Ground your answers strictly in the provided context. "
            "Do not invent information.\n"

            "2. Cite the source file names "
            "(example: [admission_policy.md]) "
            "where the information is found.\n"

            "3. If the context does not contain enough information, "
            "state that the policy details are unavailable and direct the user "
            "to contact the appropriate hospital department."
        )



    def retrieve_context(
            self,
            query: str,
            top_k: int = 3
    ) -> tuple[str, list]:
        """
        Retrieves relevant policy chunks from FAISS.
        """

        results = self.vector_db.similarity_search_with_score(
            query,
            k=top_k
        )
        results = self.vector_db.similarity_search_with_score(
        query,
        k=3
        )

        print("\nRetrieved Chunks:")
        print("-" * 60)

        for i, (doc, distance) in enumerate(results):
            print(f"\nChunk {i+1}")
            print(f"Source   : {doc.metadata['source']}")
            print(f"Distance : {distance:.4f}")
            print(f"Content  : {doc.page_content[:250]}...")


        if not results:
            return "", []



        context_parts = []
        citations = []


        for i, (doc, distance) in enumerate(results):

            source = doc.metadata.get(
                "source",
                "Unknown Policy"
            )


            context_parts.append(
                f"Snippet {i + 1} "
                f"[Source: {source}]:\n"
                f"{doc.page_content}"
            )


            citations.append(
                {
                    "text": doc.page_content,
                    "source": source,
                    "distance": float(distance)
                }
            )



        context = "\n\n".join(
            context_parts
        )


        return context, citations




    def query(self, nl_query: str) -> dict:
        """
        Retrieves context and generates a grounded response.
        """

        context, citations = self.retrieve_context(
            nl_query
        )


        if not context:

            answer = (
                "I'm sorry, I could not find any relevant policies "
                "in the document database regarding your query. "
                "Please consult the appropriate hospital department "
                "for more details."
            )


            return {
                "query": nl_query,
                "answer": answer,
                "citations": []
            }



        prompt = (
            f"Context:\n{context}\n\n"
            f"User Question: {nl_query}\n\n"
            "Answer:"
        )



        answer = call_llm(
            prompt=prompt,
            system_instruction=self.system_instruction,
            temperature=0.2
        )



        return {
            "query": nl_query,
            "answer": answer,
            "citations": citations
        }




if __name__ == "__main__":

    agent = RAGAgent()


    response = agent.query(
        "What is the discharge checkout time?"
    )


    print(response)