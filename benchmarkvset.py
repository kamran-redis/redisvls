import os
from redis import Redis
from redis.commands.vectorset.commands import  QuantizationOptions

import numpy as np


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")  # ex: 18374
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")  # ex: "1TNxTEdYRDgIDKM2gDfasupCADXXXX"


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


def main():
    # If SSL is enabled on the endpoint, use rediss:// as the URL prefix
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
    client = Redis.from_url(REDIS_URL)

    # Define the index name
    key_name = "test"

    fake_embeddings = generate_fake_embeddings(
        num_embeddings=500, embedding_dim=384, seed=42
    )
    print("Fake embeddings generated.")
    fake_embeddings2=list()
    for emb in fake_embeddings:
        fake_embeddings2.append(emb.tobytes());
    print("Fake embeddings converted.")
    
    for i,emb in enumerate(fake_embeddings2):
        client.vset().vadd(key_name,emb, str(i),quantization=QuantizationOptions.NOQUANT,cas=True)

    print("Data loaded into index.")


if __name__ == "__main__":
    main()
