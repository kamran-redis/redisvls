import os
import time
import logging
from contextlib import contextmanager
import typer
from redis import Redis
from redis.connection import ConnectionPool
from concurrent.futures import ThreadPoolExecutor, as_completed
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
import threading

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


def split_data_into_chunks(data, max_workers):
    """Split data into chunks with similar sizes, last chunk may be smaller."""
    if max_workers >= len(data):
        # More workers than data points - each worker gets 1 item max
        return [[item] for item in data]
    
    chunk_size = len(data) // max_workers
    chunks = []
    
    for i in range(max_workers):
        start_idx = i * chunk_size
        if i == max_workers - 1:  # Last chunk gets all remaining data
            end_idx = len(data)
        else:
            end_idx = (i + 1) * chunk_size
        
        chunk = data[start_idx:end_idx]
        chunks.append(chunk)
    
    return chunks


def load_chunk_with_pool(schema, connection_pool, data_chunk, chunk_id):
    """Load a chunk using a connection from the pool."""
    
    # Get connection from pool
    redis_client = Redis(connection_pool=connection_pool)
    
    try:
        # Create SearchIndex with pooled connection
        worker_index = SearchIndex(schema, redis_client, validate_on_load=False)
        
        # Load the chunk
        worker_index.load(data_chunk)
        
        return len(data_chunk)
        
    except Exception as e:
        # Log the error but let it propagate to be handled by the executor
        logger.error(f"Worker {chunk_id} error loading {len(data_chunk)} records: {e}")
        raise
    
    finally:
        # Connection automatically returns to pool when redis_client goes out of scope
        pass


def load_data_concurrent(client, schema, data, max_workers):
    """Load data concurrently using connection pool."""
    
    # Create connection pool (reuse client's connection config)
    connection_kwargs = client.connection_pool.connection_kwargs.copy()
    pool = ConnectionPool(
        host=connection_kwargs.get('host', 'localhost'),
        port=connection_kwargs.get('port', 6379),
        password=connection_kwargs.get('password', None),
        db=connection_kwargs.get('db', 0),
        max_connections=max_workers + 2  # Extra connections for safety
    )
    
    # Split data into chunks
    chunks = split_data_into_chunks(data, max_workers)
    logger.info(f"Split {len(data)} records into {len(chunks)} chunks for {max_workers} workers")
    
    # Track results
    successful_chunks = 0
    failed_chunks = 0
    total_loaded = 0
    errors = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all chunk loading tasks
        future_to_chunk = {
            executor.submit(load_chunk_with_pool, schema, pool, chunk, i): (chunk, i) 
            for i, chunk in enumerate(chunks)
        }
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_chunk):
            chunk, chunk_id = future_to_chunk[future]
            
            try:
                records_loaded = future.result()
                successful_chunks += 1
                total_loaded += records_loaded
                logger.info(f"Chunk {chunk_id} completed: {records_loaded} records loaded")
                
            except Exception as e:
                failed_chunks += 1
                error_msg = f"Chunk {chunk_id} failed: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                # Continue with other chunks - don't stop execution
    
    # Final reporting
    logger.info(f"Loading completed: {successful_chunks}/{len(chunks)} chunks successful")
    logger.info(f"Total records loaded: {total_loaded}")
    
    if errors:
        logger.warning(f"Failed chunks ({failed_chunks}): {errors}")
    
    # Close connection pool
    pool.disconnect()


def load_data(client, schema, data_size, dimension, datatype, include_id=True, max_workers=1):
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
        
        if max_workers == 1:
            # Single-threaded path (original behavior)
            index.load(data)
        else:
            # Multi-threaded path
            load_data_concurrent(client, schema, data, max_workers)
    
        


def execute_single_query(schema, connection_pool, query_embedding, num_results, query_id):
    """Execute a single query using a connection from the pool."""
    
    # Get connection from pool
    redis_client = Redis(connection_pool=connection_pool)
    
    try:
        # Create SearchIndex with pooled connection
        worker_index = SearchIndex(schema, redis_client, validate_on_load=False)
        
        # Start timing
        start_time = time.perf_counter()
        
        # Execute query
        query = VectorQuery(
            vector=query_embedding.tolist(),  # Convert numpy array to list
            vector_field_name="vector",
            num_results=num_results,
            return_fields=["vector"],
            return_score=True,
        )
        results = worker_index.query(query)
        
        # End timing
        end_time = time.perf_counter()
        
        # Calculate latency in milliseconds
        latency_ms = (end_time - start_time) * 1000
        
        return {
            'query_id': query_id,
            'latency_ms': latency_ms,
            'success': True,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Query {query_id} error: {e}")
        return {
            'query_id': query_id,
            'latency_ms': None,
            'success': False,
            'error': str(e)
        }
    
    finally:
        # Connection automatically returns to pool when redis_client goes out of scope
        pass


def _execute_query(index, query_embedding, num_results, query_id):
    """Helper function to execute a single query and return timing/result info."""
    try:
        start_time = time.perf_counter()
        
        query = VectorQuery(
            vector=query_embedding.tolist(),
            vector_field_name="vector",
            num_results=num_results,
            return_fields=["vector"],
            return_score=True,
        )
        results = index.query(query)
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        return {
            'query_id': query_id,
            'latency_ms': latency_ms,
            'success': True,
            'results': results
        }
    except Exception as e:
        logger.error(f"Query {query_id} failed: {e}")
        return {
            'query_id': query_id,
            'latency_ms': None,
            'success': False,
            'error': str(e)
        }


def _process_query_results(latencies, successful_queries, completed_queries, total_queries, start_time, last_print_time):
    """Helper function to calculate and print live statistics during query execution."""
    current_time = time.perf_counter()
    should_print = (current_time - last_print_time >= 1.0) or (completed_queries == total_queries)
    
    if should_print:
        elapsed_time = current_time - start_time
        success_rate = (successful_queries / completed_queries) * 100 if completed_queries > 0 else 0
        qps = successful_queries / elapsed_time if elapsed_time > 0 else 0
        calculate_and_print_live_stats(latencies, elapsed_time, completed_queries, success_rate, qps)
        return current_time
    
    return last_print_time


def _run_queries_single_threaded(index, query_embeddings, num_results):
    """Execute queries in single-threaded mode."""
    latencies = []
    successful_queries = 0
    start_time = time.perf_counter()
    last_print_time = start_time
    
    for i, embedding in enumerate(query_embeddings):
        result = _execute_query(index, embedding, num_results, i)
        
        if result['success']:
            latencies.append(result['latency_ms'])
            successful_queries += 1
        
        # Update live statistics
        last_print_time = _process_query_results(
            latencies, successful_queries, i + 1, len(query_embeddings), start_time, last_print_time
        )
    
    total_time = time.perf_counter() - start_time
    failed_queries = len(query_embeddings) - successful_queries
    
    return latencies, successful_queries, failed_queries, total_time


def _run_queries_concurrent(client, schema, query_embeddings, num_results, max_workers):
    """Execute queries in concurrent mode using connection pool."""
    # Create connection pool
    connection_kwargs = client.connection_pool.connection_kwargs.copy()
    pool = ConnectionPool(
        host=connection_kwargs.get('host', 'localhost'),
        port=connection_kwargs.get('port', 6379),
        password=connection_kwargs.get('password', None),
        db=connection_kwargs.get('db', 0),
        max_connections=max_workers + 2
    )
    
    # Thread-safe result tracking
    results_lock = threading.Lock()
    latencies = []
    successful_queries = 0
    failed_queries = 0
    completed_queries = 0
    
    start_time = time.perf_counter()
    last_print_time = start_time
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all query tasks
        future_to_query = {
            executor.submit(execute_single_query, schema, pool, embedding, num_results, i): i
            for i, embedding in enumerate(query_embeddings)
        }
        
        # Process completed tasks
        for future in as_completed(future_to_query):
            query_id = future_to_query[future]
            
            try:
                result = future.result()
                
                with results_lock:
                    completed_queries += 1
                    
                    if result['success']:
                        successful_queries += 1
                        latencies.append(result['latency_ms'])
                    else:
                        failed_queries += 1
                    
                    # Update live statistics
                    current_time = time.perf_counter()
                    if current_time - last_print_time >= 1.0 or completed_queries == len(query_embeddings):
                        elapsed_time = current_time - start_time
                        success_rate = (successful_queries / completed_queries) * 100 if completed_queries > 0 else 0
                        qps = successful_queries / elapsed_time if elapsed_time > 0 else 0
                        calculate_and_print_live_stats(latencies, elapsed_time, completed_queries, success_rate, qps)
                        last_print_time = current_time
                        
            except Exception as e:
                logger.error(f"Query {query_id} processing failed: {e}")
                with results_lock:
                    failed_queries += 1
                    completed_queries += 1
    
    pool.disconnect()
    total_time = time.perf_counter() - start_time
    
    return latencies, successful_queries, failed_queries, total_time


def query_data(client, schema, dimension, datatype, query_count=100, num_results=10, max_workers=1):
    """Query operation: perform vector search queries and measure latency."""
    logger.info(f"Running {query_count} queries, returning {num_results} results each")
    
    # Connect to existing index
    index = SearchIndex(schema, client, validate_on_load=False)
    
    # Generate query embeddings ahead of time
    with timer("Generating query embeddings"):
        query_embeddings = generate_fake_embeddings(query_count, dimension, datatype)
        logger.info(f"Generated {query_count} query embeddings.")
    
    # Print header for real-time results
    print_table_header()
    
    # Execute queries based on worker count
    if max_workers == 1:
        #logger.info("Running queries in single-threaded mode")
        latencies, successful_queries, failed_queries, total_time = _run_queries_single_threaded(
            index, query_embeddings, num_results
        )
    else:
        #logger.info(f"Running queries in concurrent mode with {max_workers} workers")
        latencies, successful_queries, failed_queries, total_time = _run_queries_concurrent(
            client, schema, query_embeddings, num_results, max_workers
        )
    
    # Calculate and display final statistics
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
    max_workers: int = typer.Option(1, "--max-workers", help="Number of workers for concurrent operation - applies to both 'load' and 'query' operations (default: 1 for single-threaded)"),
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
    
    # Validate load-specific parameters  
    if operation == "load":
        if data_size <= 0:
            logger.error("data_size must be greater than 0")
            raise typer.Exit(1)
    
    # Validate max_workers for both operations
    if max_workers <= 0:
        logger.error("max_workers must be greater than 0")
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
        algorithm, distance_metric, datatype, data_size, query_count, num_results, include_id, max_workers
    )
    
    # Create schema
    schema = create_schema(index_name, dimension, distance_metric, algorithm, datatype, include_id)
    
    # Execute operation
    if operation == "load":
        load_data(client, schema, data_size, dimension, datatype, include_id, max_workers)
    elif operation == "query":
        query_data(client, schema, dimension, datatype, query_count, num_results, max_workers)


if __name__ == "__main__":
    typer.run(main)