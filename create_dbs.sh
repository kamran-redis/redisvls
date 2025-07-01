#!/bin/bash

# Default values for Redis Enterprise parameters
RS_URL=${RS_URL:-"https://localhost:9443"}
RS_USER=${RS_USER:-"admin@example.com"}
RS_PASSWORD=${RS_PASSWORD:-"password"}
MEMORY_SIZE=${MEMORY_SIZE:-12884901888}


curl -vvv -k -X "POST" "$RS_URL/v1/bdbs" \
     -H 'Content-Type: application/json' \
     -u $RS_USER:$RS_PASSWORD \
     -d @- <<EOF
{
  "shards_count": 1,
  "module_list": [
    {
      "module_name": "search"
      "module_args": ""
    }
  ],
  "type": "redis",
  "replication": false,
  "memory_size": $MEMORY_SIZE,
  "name": "search1",
  "port": 12000
}
EOF


curl -vvv -k -X "POST" "$RS_URL/v1/bdbs" \
     -H 'Content-Type: application/json' \
     -u $RS_USER:$RS_PASSWORD \
     -d @- <<EOF
{
  "sched_policy": "mnp",
  "conns": 32,
  "shards_count": 1,
  "module_list": [
    {
      "module_name": "search",
      "module_args": "WORKERS 4"
    }
  ],
  "type": "redis",
  "replication": false,
  "memory_size": $MEMORY_SIZE,
  "name": "search1qbf4",
  "port": 13000
}
EOF


curl -vvv -k -X "POST" "$RS_URL/v1/bdbs" \
     -H 'Content-Type: application/json' \
     -u $RS_USER:$RS_PASSWORD \
     -d @- <<EOF
{
  "sched_policy": "mnp",
  "conns": 32,
  "shards_count": 2,
  "module_list": [
    {
      "module_name": "search",
      "module_args": "WORKERS 4"
    }
  ],
  "type": "redis",
  "shard_key_regex": [
    {
      "regex": ".*\\\\{(?<tag>.*)\\\\}.*"
    },
    {
      "regex": "(?<tag>.*)"
    }
  ],
  "sharding": true,
  "replication": false,
  "memory_size": $MEMORY_SIZE,
  "name": "search2qbf4",
  "port": 14000
}
EOF

curl -vvv -k -X "POST" "$RS_URL/v1/bdbs" \
     -H 'Content-Type: application/json' \
     -u $RS_USER:$RS_PASSWORD \
     -d @- <<EOF
{
  "sched_policy": "mnp",
  "conns": 32,
  "shards_count": 8,
  "module_list": [
    {
      "module_name": "search",
      "module_args": "WORKERS 4"
    }
  ],
  "type": "redis",
  "shard_key_regex": [
    {
      "regex": ".*\\\\{(?<tag>.*)\\\\}.*"
    },
    {
      "regex": "(?<tag>.*)"
    }
  ],
  "sharding": true,
  "replication": false,
  "memory_size": $MEMORY_SIZE,
  "shards_placement": "sparse",
  "name": "search8qbf4",
  "port": 15000
}
EOF

curl -vvv -k -X "POST" "$RS_URL/v1/bdbs" \
     -H 'Content-Type: application/json' \
     -u $RS_USER:$RS_PASSWORD \
     -d @- <<EOF
{
  "sched_policy": "mnp",
  "conns": 32,
  "shards_count": 16,
  "module_list": [
    {
      "module_name": "search",
      "module_args": "WORKERS 4"
    }
  ],
  "type": "redis",
  "shard_key_regex": [
    {
      "regex": ".*\\\\{(?<tag>.*)\\\\}.*"
    },
    {
      "regex": "(?<tag>.*)"
    }
  ],
  "sharding": true,
  "replication": false,
  "memory_size": $MEMORY_SIZE,
  "shards_placement": "sparse",
  "name": "search16qbf4",
  "port": 16000
}
EOF