"""
Performance printing utilities for Redis Vector Search Benchmark Tool.

This module contains table formatting and printing functions for displaying
query performance statistics in a clean, readable format.
"""

import numpy as np

# Table formatting constants
TABLE_WIDTH = 110
HEADER_FORMAT = f"{'Time (s)':<10} {'Completed':<12} {'Success Rate':<12} {'Mean (ms)':<12} {'Min (ms)':<10} {'P50 (ms)':<10} {'P95 (ms)':<10} {'P99 (ms)':<10} {'QPS':<10}"


def print_table_header():
    """Print the table header for query results."""
    print("\n" + "=" * TABLE_WIDTH)
    print(HEADER_FORMAT)
    print("=" * TABLE_WIDTH)


def print_table_footer():
    """Print the table footer."""
    print("=" * TABLE_WIDTH)


def _format_time_value(time_val):
    """Helper function to format time values consistently."""
    if isinstance(time_val, str):
        return f"{time_val:<10}"
    else:
        return f"{time_val:<10.1f}"


def _calculate_stats(latencies):
    """Helper function to calculate statistics from latencies array."""
    if not latencies:
        return None
    
    latencies_array = np.array(latencies)
    return {
        'mean': np.mean(latencies_array),
        'min': np.min(latencies_array),
        'p50': np.percentile(latencies_array, 50),
        'p95': np.percentile(latencies_array, 95),
        'p99': np.percentile(latencies_array, 99)
    }


def _print_row(time_val, completed, success_rate, stats=None, qps=0):
    """Helper function to print a row with consistent formatting."""
    time_str = _format_time_value(time_val)
    
    if stats:
        print(f"{time_str} {completed:<12} {success_rate:<12.1f} {stats['mean']:<12.2f} {stats['min']:<10.2f} {stats['p50']:<10.2f} {stats['p95']:<10.2f} {stats['p99']:<10.2f} {qps:<10.1f}")
    else:
        print(f"{time_str} {completed:<12} {success_rate:<12.1f} {'N/A':<12} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<10} {qps:<10.1f}")


def calculate_and_print_live_stats(latencies, elapsed_time, completed_queries, success_rate, qps):
    """Calculate and print live statistics during query execution."""
    stats = _calculate_stats(latencies)
    _print_row(elapsed_time, completed_queries, success_rate, stats, qps)


def calculate_and_print_final_stats(latencies, successful_queries, query_count, total_time):
    """Calculate and print final statistics after all queries complete."""
    stats = _calculate_stats(latencies)
    overall_qps = successful_queries / total_time if total_time > 0 else 0
    success_rate = (successful_queries / query_count) * 100
    
    _print_row(total_time, successful_queries, success_rate, stats, overall_qps)
    print_table_footer()
    
    if not stats:
        print("No successful queries to analyze!")


def print_benchmark_config(operation, redis_host, redis_port, index_name, dimension, 
                          algorithm, distance_metric, datatype, data_size=None, 
                          query_count=None, num_results=None, include_id=True, max_workers=1):
    """Print benchmark configuration in a succinct format."""
    print("\n" + "=" * 80)
    print("REDIS VECTOR SEARCH BENCHMARK CONFIGURATION")
    print("=" * 80)
    print(f"Operation:       {operation.upper()}")
    print(f"Redis Server:    {redis_host}:{redis_port}")
    print(f"Index Name:      {index_name}")
    print(f"Vector Config:   {dimension}D, {algorithm.upper()}, {distance_metric}, {datatype}")
    print(f"Include ID:      {'Yes' if include_id else 'No'}")
    
    if operation == "load" and data_size is not None:
        print(f"Data Size:       {data_size:,} embeddings")
        print(f"Workers:         {max_workers} ({'single-threaded' if max_workers == 1 else 'multi-threaded'})")
    elif operation == "query" and query_count is not None and num_results is not None:
        print(f"Query Config:    {query_count:,} queries, {num_results} results each")
    
    print("=" * 80) 