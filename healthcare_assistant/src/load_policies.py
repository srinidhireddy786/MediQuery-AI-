import sys
import os

# Add src directory to path
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from src.ingest_policies import build_vector_store, VECTOR_STORE_PATH


def main():

    print(
        "Starting FAISS Policy Vector Store Ingestion..."
    )

    build_vector_store()

    print(
        "FAISS Vector Store Ingestion completed!"
    )


if __name__ == "__main__":
    main()