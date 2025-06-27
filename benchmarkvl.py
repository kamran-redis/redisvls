import os
import time
import argparse
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


def load_data(client, schema, index_name, dimension, datatype, data_size):
    """
    Load data operation: create index and load embeddings.
    
    Args:
        client: Redis client
        schema: Index schema
        index_name: Name of the index
        dimension: Vector dimension
        datatype: Data type for vectors
        data_size: Number of embeddings to generate
    """
    print("=== LOAD OPERATION ===")
    
    # Create the index note we are setting validation load and also the index is recreated if it exists and dropping the data
    with timer("Index creation"):
        index = SearchIndex(schema, client, validate_on_load=True)
        index.create(overwrite=True, drop=True)

    type = np.float32
    if datatype == "float32": 
        type = np.float32
    else:
        raise ValueError(f"Unsupported datatype: {datatype}. Only float32 are supported.")      
    
    with timer("Generating fake embeddings"):
        fake_embeddings = generate_fake_embeddings(
            num_embeddings=data_size, embedding_dim=dimension, type=type, seed=42
        )
        print("Fake embeddings generated.")

    with timer("Data preparation"):
        data = [{"id": "document:" + str(i), "vector": e.tobytes()} for i, e in enumerate(fake_embeddings)]
        print("Data prepared for loading into index.")
    
    with timer("Data loading into index"):
        index.load(data)
        print("Data loaded into index.")
        
    print("Load operation completed successfully!")


def query_data(client, schema, dimension, datatype):
    """
    Query operation: perform vector search queries.
    
    Args:
        client: Redis client
        schema: Index schema
        dimension: Vector dimension
        datatype: Data type for vectors
    """
    print("=== QUERY OPERATION ===")
    
    # Connect to existing index without recreation or validation
    index = SearchIndex(schema, client, validate_on_load=False)
    
    # Generate a sample embedding for querying
    type = np.float32
    if datatype == "float32": 
        type = np.float32
    else:
        raise ValueError(f"Unsupported datatype: {datatype}. Only float32 are supported.")
        
    with timer("Generating query embedding"):
        query_embedding = generate_fake_embeddings(
            num_embeddings=1, embedding_dim=dimension, type=type, seed=42
        )[0]
        print("Query embedding generated.")
    
    # Let's query redis
    with timer("Vector query execution"):
        query = VectorQuery(
            vector=query_embedding,
            vector_field_name="vector",
            num_results=3,
            return_fields=["vector"],
            return_score=True,
        )
        results = index.query(query)
        print("Query executed.")
        print("Results:", len(results))
        
    print("Query operation completed successfully!")


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Redis Vector Search Benchmark")
    parser.add_argument(
        "--operation", 
        choices=["load", "query"], 
        required=True,
        help="Operation to perform: 'load' to create index and load data, 'query' to perform vector queries"
    )
    parser.add_argument(
        "--index-name",
        default="redisvl",
        help="Name of the Redis index (default: redisvl)"
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=960,
        help="Vector dimension (default: 960)"
    )
    parser.add_argument(
        "--algorithm",
        choices=["flat", "hnsw"],
        default="flat",
        help="Vector search algorithm (default: flat)"
    )
    parser.add_argument(
        "--distance-metric",
        choices=["cosine", "l2", "ip"],
        default="cosine",
        help="Distance metric for vector similarity (default: cosine)"
    )
    parser.add_argument(
        "--datatype",
        choices=["float32"],
        default="float32",
        help="Data type for vectors (default: float32)"
    )
    parser.add_argument(
        "--data-size",
        type=int,
        default=1000000,
        help="Number of embeddings to generate and load (default: 1000000)"
    )
    args = parser.parse_args()

    # If SSL is enabled on the endpoint, use rediss:// as the URL prefix
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
    client = Redis.from_url(REDIS_URL)

    # Use parameterized values from command line arguments
    index_name = args.index_name
    dimension = args.dimension
    algorithm = args.algorithm
    distance_metric = args.distance_metric
    datatype = args.datatype
    data_size = args.data_size

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

    if args.operation == "load":
        load_data(client, schema, index_name, dimension, datatype, data_size)
    elif args.operation == "query":
        query_data(client, schema, dimension, datatype)


if __name__ == "__main__":
    main()