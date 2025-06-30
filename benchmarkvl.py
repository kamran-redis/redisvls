import os
import time
import logging
from contextlib import contextmanager
import typer
from redis import Redis
from redisvl.schema import IndexSchema
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from utils import (
    print_table_header, 
    print_table_footer, 
    calculate_and_print_live_stats, 
    calculate_and_print_final_stats,
    print_benchmark_config
)

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


def create_schema(index_name, dimension, distance_metric, algorithm, datatype, include_id=True):
    """Create and return the index schema."""
    fields = [
        {
            "name": "vector",
            "type": "vector",
            "attrs": {
                "dims": dimension,
                "distance_metric": distance_metric,
                "algorithm": algorithm,
                "datatype": datatype,
            },
        }
    ]
    
    # Conditionally add ID field
    if include_id:
        fields.append({
            "name": "id",
            "type": "text",
        })
    
    return IndexSchema.from_dict({
        "index": {"name": index_name, "prefix": index_name, "storage_type": "hash"},
        "fields": fields,
    })


def load_data(client, schema, data_size, dimension, datatype, include_id=True):
    """Load data operation: create index and load embeddings."""
    logger.info("=== LOAD OPERATION ===")
    
    # Create the index
    with timer("Index creation"):
        index = SearchIndex(schema, client, validate_on_load=False)
        index.create(overwrite=True, drop=True)
    
    # Generate embeddings
    with timer("Generating fake embeddings"):
        fake_embeddings = generate_fake_embeddings(data_size, dimension, datatype)

    # Prepare data
    with timer("Data preparation "):
        if include_id:
            data = [{"id": f"document:{i}", "vector": e.tobytes()} for i, e in enumerate(fake_embeddings)]
        else:
            data = [{"vector": e.tobytes()} for e in fake_embeddings]
  
    with timer("Data Loading into index"):
        logger.info("Starting data loading into index.")
        index.load(data)
    
        


def query_data(client, schema, dimension, datatype, query_count=100, num_results=10):
    """Query operation: perform vector search queries and measure latency."""
    logger.info(f"Running {query_count} queries, returning {num_results} results each")
    
    # Connect to existing index
    index = SearchIndex(schema, client, validate_on_load=False)
    
    # Initialize list to store latency measurements
    latencies = []
    
    # Generate query embeddings ahead of time to avoid impacting latency measurement
    with timer("Generating query embeddings"):
        query_embeddings = generate_fake_embeddings(query_count, dimension, datatype)
        logger.info(f"Generated {query_count} query embeddings.")
    
    # Print header for real-time results
    print_table_header()
    
    # Execute queries and measure latency
    successful_queries = 0
    start_benchmark = time.perf_counter()
    last_print_time = start_benchmark
    
    for i in range(query_count):
        try:
            # Start timing
            start_time = time.perf_counter()
            
            # Execute query
            query = VectorQuery(
                vector=query_embeddings[i],
                vector_field_name="vector",
                num_results=num_results,
                return_fields=["vector"],
                return_score=True,
            )
            results = index.query(query)
            
            # End timing
            end_time = time.perf_counter()
            
            # Record latency in milliseconds
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            successful_queries += 1
            
            # Print intermediate results every 1 second
            current_time = time.perf_counter()
            if current_time - last_print_time >= 1.0 or i == query_count - 1:
                elapsed_time = current_time - start_benchmark
                success_rate = (successful_queries / (i + 1)) * 100
                qps = successful_queries / elapsed_time if elapsed_time > 0 else 0
                
                calculate_and_print_live_stats(latencies, elapsed_time, i+1, success_rate, qps)
                last_print_time = current_time
                
        except Exception as e:
            logger.error(f"Query {i + 1} failed: {e}")
    
    # Calculate and display final statistics
    total_time = time.perf_counter() - start_benchmark
    calculate_and_print_final_stats(latencies, successful_queries, query_count, total_time)
    
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
    data_size: int = typer.Option(1000000, "--data-size", help="Number of embeddings to generate and load (used for 'load' operation)"),
    query_count: int = typer.Option(100, "--query-count", help="Number of queries to run (used for 'query' operation)"),
    num_results: int = typer.Option(3, "--num-results", help="Number of results to return per query (used for 'query' operation)"),
    include_id: bool = typer.Option(True, "--include-id/--no-id", help="Include ID field in schema (default: True)"),
):
    """Redis Vector Search Benchmark Tool"""
    
    # Validate all arguments
    validate_choice_argument(operation, SUPPORTED_OPERATIONS, "operation")
    validate_choice_argument(algorithm, SUPPORTED_ALGORITHMS, "algorithm")
    validate_choice_argument(distance_metric, SUPPORTED_DISTANCE_METRICS, "distance_metric")
    validate_choice_argument(datatype, SUPPORTED_DATATYPES, "datatype")
    
    # Validate query-specific parameters
    if operation == "query":
        if query_count <= 0:
            logger.error("query_count must be greater than 0")
            raise typer.Exit(1)
        if num_results <= 0:
            logger.error("num_results must be greater than 0")
            raise typer.Exit(1)
    
    # Setup Redis connection
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
    
    try:
        client = Redis.from_url(redis_url)
        # Test the connection with a ping
        client.ping()
    except Exception as e:
        logger.error(f"Failed to connect to Redis at {redis_host}:{redis_port}: {e}")
        raise typer.Exit(1)
    
    # Print configuration
    print_benchmark_config(
        operation, redis_host, redis_port, index_name, dimension,
        algorithm, distance_metric, datatype, data_size, query_count, num_results, include_id
    )
    
    # Create schema
    schema = create_schema(index_name, dimension, distance_metric, algorithm, datatype, include_id)
    
    # Execute operation
    if operation == "load":
        load_data(client, schema, data_size, dimension, datatype, include_id)
    elif operation == "query":
        query_data(client, schema, dimension, datatype, query_count, num_results)


if __name__ == "__main__":
    typer.run(main)