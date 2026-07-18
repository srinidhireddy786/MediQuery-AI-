import os
import re

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings


# Config
POLICIES_DIR = r"C:\Users\Sriram reddy\.gemini\antigravity\scratch\healthcare_assistant\policies"

VECTOR_STORE_PATH = r"C:\Users\Sriram reddy\.gemini\antigravity\scratch\healthcare_assistant\vector_store\faiss_policy_index"



def chunk_text(text, source_name, chunk_size=800, chunk_overlap=150):
    """
    Splits text into overlapping chunks.
    """

    text = re.sub(r'\s+', ' ', text).strip()

    chunks = []

    start = 0
    text_len = len(text)


    while start < text_len:

        end = min(start + chunk_size, text_len)


        if end < text_len:

            boundary = -1

            for i in range(
                end,
                max(end - chunk_overlap, start),
                -1
            ):

                if text[i] in ['.', '!', '?']:
                    boundary = i + 1
                    break


            if boundary != -1:
                end = boundary


        chunk = text[start:end].strip()


        if chunk:

            chunks.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": source_name,
                        "length": len(chunk)
                    }
                )
            )


        start = end - chunk_overlap if end < text_len else text_len


        if start <= 0 or start >= end:
            start = end


    return chunks




def build_vector_store(
        policies_dir=POLICIES_DIR,
        output_path=VECTOR_STORE_PATH
):

    """
    Reads policies, creates chunks,
    generates Ollama embeddings,
    and stores FAISS index.
    """


    documents = []


    if not os.path.exists(policies_dir):

        print(
            f"Policies directory not found: {policies_dir}"
        )

        return



    for filename in os.listdir(policies_dir):

        if filename.endswith(".md") or filename.endswith(".txt"):

            filepath = os.path.join(
                policies_dir,
                filename
            )


            print(
                f"Processing {filename}..."
            )


            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()


            chunks = chunk_text(
                content,
                filename
            )


            print(
                f"Generated {len(chunks)} chunks"
            )


            documents.extend(chunks)



    if not documents:

        print(
            "No documents found."
        )

        return



    print(
        "Loading Ollama embedding model..."
    )


    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )


    print(
        "Creating FAISS vector index..."
    )


    vector_store = FAISS.from_documents(
        documents,
        embeddings
    )


    os.makedirs(
        output_path,
        exist_ok=True
    )


    vector_store.save_local(
        output_path
    )


    print(
        f"FAISS index saved at {output_path}"
    )




if __name__ == "__main__":

    build_vector_store()