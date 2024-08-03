import os

from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
INDEX_NAME = "ragtube"


def create_index():
    pc.create_index(
        name=INDEX_NAME,
        dimension=768,  # Replace with your model dimensions
        metric="cosine",  # Replace with your model metric
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )


if __name__ == "__main__":
    create_index()
