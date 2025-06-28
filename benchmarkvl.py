import os
import time
from contextlib import contextmanager
import typer
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


def main(
    operation: str = typer.Argument(..., help="Operation to perform: 'load' to create index and load data, 'query' to perform vector queries"),
    index_name: str = typer.Option("redisvl", "--index-name", help="Name of the Redis index"),
    dimension: int = typer.Option(960, "--dimension", help="Vector dimension"),
    algorithm: str = typer.Option("flat", "--algorithm", help="Vector search algorithm (choices: flat, hnsw)"),
    distance_metric: str = typer.Option("cosine", "--distance-metric", help="Distance metric for vector similarity (choices: cosine, l2, ip)"),
    datatype: str = typer.Option("float32", "--datatype", help="Data type for vectors (choices: float32)"),
    data_size: int = typer.Option(1000000, "--data-size", help="Number of embeddings to generate and load"),
):
    """Redis Vector Search Benchmark Tool"""
    
    # Validate all choice-based arguments
    if operation not in ["load", "query"]:
        typer.echo(f"Error: operation must be either 'load' or 'query', got: {operation}")
        raise typer.Exit(1)
    
    if algorithm not in ["flat", "hnsw"]:
        typer.echo(f"Error: algorithm must be either 'flat' or 'hnsw', got: {algorithm}")
        raise typer.Exit(1)
    
    if distance_metric not in ["cosine", "l2", "ip"]:
        typer.echo(f"Error: distance_metric must be one of 'cosine', 'l2', or 'ip', got: {distance_metric}")
        raise typer.Exit(1)
    
    if datatype not in ["float32"]:
        typer.echo(f"Error: datatype must be 'float32', got: {datatype}")
        raise typer.Exit(1)
    
    # If SSL is enabled on the endpoint, use rediss:// as the URL prefix
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
    client = Redis.from_url(REDIS_URL)

    # define the schema
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

    if operation == "load":
        load_data(client, schema, index_name, dimension, datatype, data_size)
    elif operation == "query":
        query_data(client, schema, dimension, datatype)


if __name__ == "__main__":
    typer.run(main)