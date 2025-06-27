import os
from redis import Redis
from redis.commands.search.field import VectorField, TagField, NumericField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType


import numpy as np


def generate_fake_embeddings(num_embeddings=10, embedding_dim=128, seed=None):
    """
    Generate fake embeddings using random numbers.

    Args:
        num_embeddings (int): Number of embeddings to generate.
        embedding_dim (int): Dimension of each embedding vector.
        seed (int, optional): Random seed for reproducibility.

    Returns:
        np.ndarray: A matrix of shape (num_embeddings, embedding_dim) with fake embeddings.
    """
    if seed is not None:
        np.random.seed(seed)

    embeddings = np.random.rand(num_embeddings, embedding_dim).astype(np.float32)
    return embeddings


# Example usage


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")  # ex: 18374
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")  # ex: "1TNxTEdYRDgIDKM2gDfasupCADXXXX"

# If SSL is enabled on the endpoint, use rediss:// as the URL prefix


def main():
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
    client = Redis.from_url(REDIS_URL)
    print(client.ping())

    index_name = "test_index"

    schema = VectorField(
        "vector", "HNSW", {"TYPE": "FLOAT32", "DIM": 384, "DISTANCE_METRIC": "COSINE"}
    )

    try:
        client.ft(index_name).info()
        print("Index exists!")
    except:
        # index Definition
        definition = IndexDefinition(index_type=IndexType.HASH)

        # create Index
        client.ft(index_name).create_index(fields=schema, definition=definition)


if __name__ == "__main__":
    main()
