# Redis Vector Search Benchmark Tool

A simple benchmarking tool for Redis Vector Search performance testing using RedisVL. This tool helps you test both data loading and query performance with various configuration options.

## Features

- **Load Benchmarking**: Create indexes and load vector embeddings with timing measurements
- **Query Benchmarking**: Execute vector similarity search queries with latency tracking
- **Real-time Monitoring**: Live performance statistics during query execution
- **Configurable Parameters**: Support for different algorithms, distance metrics, and data sizes
- **Performance Statistics**: Basic statistics including percentiles, QPS, and success rates
- **CLI Interface**: Command-line interface with configuration options

## Supported Configurations

- **Algorithms**: `flat`, `hnsw`
- **Distance Metrics**: `cosine`, `l2`, `ip`
- **Data Types**: `float32`
- **Operations**: `load`, `query`

## Installation

### Prerequisites

- Python 3.7+
- Redis server with RedisSearch module
- Git (for cloning the repository)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd redisvls
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The tool provides two main operations: `load` and `query`.

### Basic Usage

```bash
python benchmarkvl.py <operation> [OPTIONS]
```

### Load Operation

Create an index and load vector embeddings:

```bash
python benchmarkvl.py load \
  --redis-host localhost \
  --redis-port 6379 \
  --index-name my_index \
  --dimension 960 \
  --algorithm flat \
  --distance-metric cosine \
  --data-size 100000
```

### Query Operation

Perform vector similarity search queries:

```bash
python benchmarkvl.py query \
  --redis-host localhost \
  --redis-port 6379 \
  --index-name my_index \
  --dimension 960 \
  --algorithm flat \
  --distance-metric cosine \
  --query-count 1000 \
  --num-results 10
```

## Configuration Options

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--redis-host` | Redis server hostname | `localhost` |
| `--redis-port` | Redis server port | `6379` |
| `--redis-password` | Redis server password | `""` |
| `--index-name` | Name of the Redis index | `redisvl` |
| `--dimension` | Vector dimension | `960` |
| `--algorithm` | Vector search algorithm | `flat` |
| `--distance-metric` | Distance metric for similarity | `cosine` |
| `--datatype` | Data type for vectors | `float32` |

### Load Operation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--data-size` | Number of embeddings to generate and load | `1000000` |

### Query Operation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--query-count` | Number of queries to execute | `100` |
| `--num-results` | Number of results to return per query | `3` |

## Performance Metrics

The tool provides basic performance metrics:

### Load Operation Metrics
- Index creation time
- Embedding generation time
- Data preparation time
- Data loading time

### Query Operation Metrics
- **Latency Statistics**: Mean, Min, P50, P95, P99 (in milliseconds)
- **Throughput**: Queries per second (QPS)
- **Success Rate**: Percentage of successful queries
- **Live Updates**: Statistics updated every second during execution

## Example Output

### Load Operation
```
python benchmarkvl.py load

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       LOAD
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, FLAT, cosine, float32
Data Size:       1,000,000 embeddings
================================================================================
13:47:01 __main__ INFO   === LOAD OPERATION ===
13:47:01 __main__ INFO   Index creation took: 0.0008 seconds
13:47:06 __main__ INFO   Generating fake embeddings took: 4.5739 seconds
13:47:07 __main__ INFO   Data preparation  took: 1.0684 seconds
13:47:07 __main__ INFO   Starting data loading into index.
13:47:59 __main__ INFO   Data Loading into index took: 52.1235 seconds
```

### Query Operation
```
python benchmarkvl.py query

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, FLAT, cosine, float32
Query Config:    100 queries, 3 results each
================================================================================
13:48:42 __main__ INFO   Running 100 queries, returning 3 results each
13:48:42 __main__ INFO   Generated 100 query embeddings.
13:48:42 __main__ INFO   Generating query embeddings took: 0.0034 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
1.0        10           100.0        104.39       100.87     103.68     110.26     112.85     9.6
2.1        20           100.0        103.50       100.87     101.63     108.25     112.45     9.7
3.1        30           100.0        102.97       100.87     101.85     107.22     111.89     9.7
4.1        40           100.0        102.65       100.87     101.82     106.38     111.34     9.7
5.1        50           100.0        102.90       100.87     101.96     106.76     110.79     9.7
6.2        60           100.0        103.11       100.87     102.07     108.35     110.96     9.7
7.2        70           100.0        103.15       100.87     102.07     108.73     110.58     9.7
8.3        80           100.0        103.23       100.78     102.03     108.89     110.15     9.7
9.3        90           100.0        103.27       100.78     102.07     109.16     110.51     9.7
10.3       100          100.0        103.16       100.78     102.00     109.12     110.17     9.7
10.3       100          100.0        103.16       100.78     102.00     109.12     110.17     9.7
==============================================================================================================
13:48:53 __main__ INFO   Query operation completed successfully!
```






## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



## Dependencies

- Built with [RedisVL](https://github.com/RedisVentures/redisvl)
- CLI interface using [Typer](https://typer.tiangolo.com/)
- Performance utilities using [NumPy](https://numpy.org/) 