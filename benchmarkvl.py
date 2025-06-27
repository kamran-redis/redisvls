import os
import time
from contextlib import contextmanager
from redis import Redis
from redisvl.schema import IndexSchema
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery

import numpy as np


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")  # ex: 18374
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")  # ex: "1TNxTEdYRDgIDKM2gDfasupCADXXXX"


@contextmanager
def timer(operation_name="Operation"):
    """Context manager for timing operations."""
    start_time = time.perf_counter()
    yield
    end_time = time.perf_counter()
    print(f"{operation_name} took: {end_time - start_time:.4f} seconds")


def generate_fake_embeddings(num_embeddings=10, embedding_dim=128, type=np.float32 ,seed=None):
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
    index_name = "redisvl"
    dimension = 960  
    algorithm = "flat" 
    #algorithm = "hnsw" 
    distance_metric = "cosine" 
    datatype = "float32" 
    data_size = 1000000

    # define the scheama
    schema = IndexSchema.from_dict(
        {
            "index": {"name": index_name, "prefix": index_name, "storage_type": "hash"},
            "fields": [
                {
                    "name": "vector",
                    "type": "vector",
                    "attrs": {
                        "dims": dimension,
                        "distance_metric": distance_metric,
                        "algorithm": algorithm,
                        "datatype": datatype,
                    },
                },
                {
                    "name": "id",
                    "type": "text",
                },

            ],
        }
    )

    #create the index note we are setting  validation load and also the index is recreated if it exists and dropping the data
    with timer("Index creation"):
        index = SearchIndex(schema, client,validate_on_load=True)
        index.create(overwrite=True, drop=True )

    type= np.float32;
    if datatype == "float32": 
        type = np.float32
    else :
        raise ValueError(f"Unsupported datatype: {datatype}. Only float32 are supported.")      
    
    with timer("Generating fake embeddings"):
        fake_embeddings = generate_fake_embeddings(
            num_embeddings=data_size, embedding_dim=dimension, type=type ,seed=42
        )
        print("Fake embeddings generated.")

    # data with other fields
    #data = [{"id": i, "vector": e.tobytes()} for i, e in enumerate(fake_embeddings)]
    #print("Data prepared for loading into index.")
    #index.load(data, id_field="id")
    #print("Data loaded into index.")

    with timer("Data preparation"):
        data = [{"id": "document:" +str(i),"vector": e.tobytes()} for i, e in enumerate(fake_embeddings)]
        #data = [{"vector": e.tobytes()} for i, e in enumerate(fake_embeddings)]
        print("Data prepared for loading into index.")
    
    with timer("Data loading into index"):
        index.load(data)
        print("Data loaded into index.")
    
    #lets query redis
    with timer("Vector query execution"):
        query = VectorQuery(
            vector=fake_embeddings[0],
            vector_field_name="vector",
            num_results=3,
            return_fields=["vector"],
            return_score=True,
        )
        results = index.query(query)
        print("Query executed.")
        print("Results:", len( results))



if __name__ == "__main__":
    main()