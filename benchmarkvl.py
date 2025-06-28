import os
import time
import logging
from contextlib import contextmanager
import typer
from redis import Redis
from redisvl.schema import IndexSchema
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
SUPPORTED_OPERATIONS = ["load", "query"]
SUPPORTED_ALGORITHMS = ["flat", "hnsw"]
SUPPORTED_DISTANCE_METRICS = ["cosine", "l2", "ip"]
SUPPORTED_DATATYPES = ["float32"]
DEFAULT_SEED = 42


@contextmanager
def timer(operation_name="Operation"):
    """Context manager for timing operations."""
    start_time = time.perf_counter()
    yield
    end_time = time.perf_counter()
    logger.info(f"{operation_name} took: {end_time - start_time:.4f} seconds")


def validate_choice_argument(value, valid_choices, arg_name):
    """Validate that a value is in the list of valid choices."""
    if value not in valid_choices:
        logger.error(f"{arg_name} must be one of {valid_choices}, got: {value}")
        raise typer.Exit(1)


def get_numpy_dtype(datatype_str):
    """Convert datatype string to numpy dtype."""
    dtype_map = {"float32": np.float32}
    if datatype_str not in dtype_map:
        raise ValueError(f"Unsupported datatype: {datatype_str}. Only {list(dtype_map.keys())} are supported.")
    return dtype_map[datatype_str]


def generate_fake_embeddings(num_embeddings, embedding_dim, datatype_str, seed=DEFAULT_SEED):
    """Generate fake embeddings using random numbers."""
    if seed is not None:
        np.random.seed(seed)
    
    dtype = get_numpy_dtype(datatype_str)
    embeddings = np.random.rand(num_embeddings, embedding_dim).astype(dtype)
    return embeddings


def create_schema(index_name, dimension, distance_metric, algorithm, datatype):
    """Create and return the index schema."""
    return IndexSchema.from_dict({
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
    })


def load_data(client, schema, data_size, dimension, datatype):
    """Load data operation: create index and load embeddings."""
    logger.info("=== LOAD OPERATION ===")
    
    # Create the index
    with timer("Index creation"):
        index = SearchIndex(schema, client, validate_on_load=True)
        index.create(overwrite=True, drop=True)
    
    # Generate embeddings
    with timer("Generating fake embeddings"):
        fake_embeddings = generate_fake_embeddings(data_size, dimension, datatype)


    # Prepare data
    with timer("Data preparation "):
        data = [{"id": f"document:{i}", "vector": e.tobytes()} for i, e in enumerate(fake_embeddings)]
  
    with timer("Data Loading into index"):
        logger.info("Starting data loading into index.")
        index.load(data)
    
        


def query_data(client, schema, dimension, datatype):
    """Query operation: perform vector search queries."""
    logger.info("=== QUERY OPERATION ===")
    
    # Connect to existing index
    index = SearchIndex(schema, client, validate_on_load=False)
    
    # Generate query embedding
    with timer("Generating and executing query"):
        query_embedding = generate_fake_embeddings(1, dimension, datatype)[0]
        logger.info("Query embedding generated.")
        
        # Execute query
        query = VectorQuery(
            vector=query_embedding,
            vector_field_name="vector",
            num_results=3,
            return_fields=["vector"],
            return_score=True,
        )
        results = index.query(query)
        logger.info(f"Query executed. Found {len(results)} results.")
        
    logger.info("Query operation completed successfully!")


def main(
    operation: str = typer.Argument(..., help="Operation to perform: 'load' to create index and load data, 'query' to perform vector queries"),
    redis_host: str = typer.Option("localhost", "--redis-host", help="Redis server hostname"),
    redis_port: int = typer.Option(6379, "--redis-port", help="Redis server port"),
    redis_password: str = typer.Option("", "--redis-password", help="Redis server password"),
    index_name: str = typer.Option("redisvl", "--index-name", help="Name of the Redis index"),
    dimension: int = typer.Option(960, "--dimension", help="Vector dimension"),
    algorithm: str = typer.Option("flat", "--algorithm", help="Vector search algorithm (choices: flat, hnsw)"),
    distance_metric: str = typer.Option("cosine", "--distance-metric", help="Distance metric for vector similarity (choices: cosine, l2, ip)"),
    datatype: str = typer.Option("float32", "--datatype", help="Data type for vectors (choices: float32)"),
    data_size: int = typer.Option(1000000, "--data-size", help="Number of embeddings to generate and load"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level (choices: DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
):
    """Redis Vector Search Benchmark Tool"""
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        typer.echo(f"Error: Invalid log level: {log_level}")
        raise typer.Exit(1)
    logger.setLevel(numeric_level)
    
    # Validate all arguments
    validate_choice_argument(operation, SUPPORTED_OPERATIONS, "operation")
    validate_choice_argument(algorithm, SUPPORTED_ALGORITHMS, "algorithm")
    validate_choice_argument(distance_metric, SUPPORTED_DISTANCE_METRICS, "distance_metric")
    validate_choice_argument(datatype, SUPPORTED_DATATYPES, "datatype")
    
    # Setup Redis connection
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
    client = Redis.from_url(redis_url)
    
    # Create schema
    schema = create_schema(index_name, dimension, distance_metric, algorithm, datatype)
    
    # Execute operation
    if operation == "load":
        load_data(client, schema, data_size, dimension, datatype)
    elif operation == "query":
        query_data(client, schema, dimension, datatype)


if __name__ == "__main__":
    typer.run(main)