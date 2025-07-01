#!/bin/bash

# Simple bash script to iterate over algorithms, operations, and worker counts
# for Redis Vector Library benchmarking

set -e  # Exit on any error

# Define arrays for iteration
algorithms=("flat" "hnsw")
operations=("load" "query")
workers=(1 16)

REDIS_HOST="localhost"
REDIS_PORT=6379

# Calculate total number of operations
total_ops=$((${#algorithms[@]} * ${#operations[@]} * ${#workers[@]}))
current_op=0

echo "=== Starting Benchmark Suite ==="
echo "Total operations to run: $total_ops"
echo ""

for algorithm in "${algorithms[@]}"; do
    for operation in "${operations[@]}"; do
        for worker_count in "${workers[@]}"; do
            current_op=$((current_op + 1))
            echo "=== Operation $current_op/$total_ops ==="
            echo "Running: algorithm=$algorithm, operation=$operation, workers=$worker_count"
            echo ""
            
            if python benchmarkvl.py "$operation" \
                --algorithm "$algorithm" \
                --max-workers "$worker_count" \
                --redis-host "$REDIS_HOST" \
                --redis-port "$REDIS_PORT"; then
                echo "✓ Operation $current_op completed successfully"
            else
                echo "✗ Operation $current_op failed"
            fi
            echo ""
            sleep 1
        done
    done
done

echo "=== Benchmark Complete ==="
