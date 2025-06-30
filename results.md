redis_version:8.0.0
multipass on local Mac : os:Linux 5.15.0-142-generic aarch64
NOTE: NO Concurrency on Client, Single Thread, Client and Redis on same VM

## Load

960D,cosine, float32, 1,000,000 embeddings

|      | Time (seconds) |
| ---- | -------------- |
| FLAT | 47.4016*       |
| HNSW | 3400.6833      |

*Redis VL takes about 28 seconds to pre-process before pipelining data to redis, Redis ops per second are ~50K



##  Query

Latency mean time in ms

| # of Results | 3     | 10    | 100   |
| ------------ | ----- | ----- | ----- |
| FLAT         | 96.24 | 97.00 | 97.05 |
| HNSW         | 0.56  | 0.73  | 5.05  |

QPS

| # of Results | 3       | 10      | 100   |
| ------------ | -----   | -----   | ----- |
| FLAT         | 10.4    | 10.3    | 10.3  |
| HNSW         | 1773.7  | 1372.8  | 197.5 |


```
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py load --algorithm hnsw

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       LOAD
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, HNSW, cosine, float32
Include ID:      Yes
Data Size:       1,000,000 embeddings
================================================================================
15:57:23 __main__ INFO   === LOAD OPERATION ===
15:57:23 __main__ INFO   Index creation took: 0.0017 seconds
15:57:28 __main__ INFO   Generating fake embeddings took: 4.3870 seconds
15:57:29 __main__ INFO   Data preparation  took: 1.1171 seconds
15:57:29 __main__ INFO   Starting data loading into index.
16:54:10 __main__ INFO   Data Loading into index took: 3400.6833 seconds
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query --algorithm hnsw

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, HNSW, cosine, float32
Include ID:      Yes
Query Config:    100 queries, 3 results each
================================================================================
16:54:27 __main__ INFO   Running 100 queries, returning 3 results each
16:54:27 __main__ INFO   Generated 100 query embeddings.
16:54:27 __main__ INFO   Generating query embeddings took: 0.0039 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
0.1        100          100.0        0.56         0.40       0.51       0.69       1.14       1795.9
0.1        100          100.0        0.56         0.40       0.51       0.69       1.14       1773.7
==============================================================================================================
16:54:27 __main__ INFO   Query operation completed successfully!
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query --algorithm hnsw --query-count 1000

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, HNSW, cosine, float32
Include ID:      Yes
Query Config:    1,000 queries, 3 results each
================================================================================
16:55:57 __main__ INFO   Running 1000 queries, returning 3 results each
16:55:57 __main__ INFO   Generated 1000 query embeddings.
16:55:57 __main__ INFO   Generating query embeddings took: 0.0085 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
0.5        1000         100.0        0.52         0.39       0.51       0.63       0.75       1921.4
0.5        1000         100.0        0.52         0.39       0.51       0.63       0.75       1919.4
==============================================================================================================
16:55:57 __main__ INFO   Query operation completed successfully!
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query --algorithm hnsw --query-count 10000

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, HNSW, cosine, float32
Include ID:      Yes
Query Config:    10,000 queries, 3 results each
================================================================================
16:56:01 __main__ INFO   Running 10000 queries, returning 3 results each
16:56:01 __main__ INFO   Generated 10000 query embeddings.
16:56:01 __main__ INFO   Generating query embeddings took: 0.0511 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
1.0        1979         100.0        0.50         0.36       0.49       0.61       0.71       1978.2
2.0        3949         100.0        0.51         0.36       0.50       0.61       0.70       1974.0
3.0        5948         100.0        0.50         0.36       0.49       0.61       0.70       1982.2
4.0        7908         100.0        0.51         0.36       0.50       0.61       0.70       1976.5
5.0        9879         100.0        0.51         0.36       0.50       0.61       0.70       1975.3
5.1        10000        100.0        0.51         0.36       0.50       0.61       0.70       1974.2
5.1        10000        100.0        0.51         0.36       0.50       0.61       0.70       1973.7
==============================================================================================================
16:56:06 __main__ INFO   Query operation completed successfully!
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query --algorithm hnsw --query-count 10000 --num-results 10

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, HNSW, cosine, float32
Include ID:      Yes
Query Config:    10,000 queries, 10 results each
================================================================================
16:56:49 __main__ INFO   Running 10000 queries, returning 10 results each
16:56:49 __main__ INFO   Generated 10000 query embeddings.
16:56:49 __main__ INFO   Generating query embeddings took: 0.0513 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
1.0        1371         100.0        0.73         0.60       0.72       0.85       0.95       1370.2
2.0        2759         100.0        0.72         0.60       0.71       0.84       0.93       1378.7
3.0        4140         100.0        0.72         0.60       0.71       0.84       0.93       1379.1
4.0        5513         100.0        0.73         0.58       0.71       0.84       0.94       1377.5
5.0        6858         100.0        0.73         0.58       0.72       0.85       0.94       1370.9
6.0        8217         100.0        0.73         0.58       0.72       0.85       0.94       1368.8
7.0        9578         100.0        0.73         0.58       0.72       0.85       0.95       1367.5
7.3        10000        100.0        0.73         0.58       0.72       0.85       0.95       1366.5
7.3        10000        100.0        0.73         0.58       0.72       0.85       0.95       1366.3
==============================================================================================================
16:56:57 __main__ INFO   Query operation completed successfully!
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query --algorithm hnsw --query-count 10000 --num-results 100

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, HNSW, cosine, float32
Include ID:      Yes
Query Config:    10,000 queries, 100 results each
================================================================================
16:57:02 __main__ INFO   Running 10000 queries, returning 100 results each
16:57:02 __main__ INFO   Generated 10000 query embeddings.
16:57:02 __main__ INFO   Generating query embeddings took: 0.0508 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
1.0        198          100.0        5.06         4.74       5.01       5.48       5.68       197.4
2.0        398          100.0        5.03         4.68       4.99       5.43       5.68       198.6
3.0        597          100.0        5.04         4.68       4.99       5.47       5.74       198.5
4.0        797          100.0        5.03         4.68       4.98       5.39       5.68       198.8
5.0        997          100.0        5.02         4.68       4.98       5.39       5.68       198.9
6.0        1196         100.0        5.03         4.68       4.99       5.38       5.68       198.9
7.0        1396         100.0        5.02         4.68       4.99       5.38       5.68       198.9
8.0        1595         100.0        5.02         4.68       4.99       5.37       5.67       198.9
9.0        1796         100.0        5.02         4.67       4.98       5.37       5.64       199.1
10.0       1992         100.0        5.03         4.67       4.99       5.39       5.69       198.7
11.0       2189         100.0        5.03         4.67       4.99       5.42       5.69       198.5
12.0       2386         100.0        5.04         4.67       5.00       5.45       5.71       198.3
13.0       2587         100.0        5.04         4.67       4.99       5.43       5.71       198.5
14.0       2785         100.0        5.04         4.67       5.00       5.43       5.71       198.4
15.0       2978         100.0        5.05         4.67       5.00       5.47       5.76       198.0
16.0       3173         100.0        5.05         4.67       5.01       5.48       5.76       197.8
17.0       3373         100.0        5.05         4.67       5.00       5.47       5.76       198.0
18.0       3574         100.0        5.04         4.67       5.00       5.46       5.76       198.1
19.0       3774         100.0        5.04         4.67       5.00       5.46       5.75       198.2
20.0       3975         100.0        5.04         4.67       5.00       5.45       5.75       198.3
21.0       4175         100.0        5.04         4.67       5.00       5.44       5.75       198.3
22.1       4373         100.0        5.04         4.67       5.00       5.45       5.75       198.3
23.1       4572         100.0        5.04         4.67       4.99       5.44       5.75       198.3
24.1       4768         100.0        5.04         4.67       5.00       5.45       5.76       198.2
25.1       4968         100.0        5.04         4.67       4.99       5.45       5.76       198.3
26.1       5163         100.0        5.04         4.67       5.00       5.46       5.77       198.1
27.1       5349         100.0        5.05         4.67       5.00       5.50       5.85       197.7
28.1       5535         100.0        5.07         4.67       5.01       5.55       5.89       197.3
29.1       5728         100.0        5.07         4.67       5.01       5.56       5.89       197.1
30.1       5925         100.0        5.07         4.67       5.01       5.56       5.89       197.1
31.1       6120         100.0        5.07         4.67       5.02       5.57       5.88       197.0
32.1       6309         100.0        5.08         4.67       5.02       5.59       5.98       196.7
33.1       6499         100.0        5.09         4.67       5.02       5.58       6.01       196.5
34.1       6699         100.0        5.08         4.67       5.02       5.58       6.00       196.5
35.1       6901         100.0        5.08         4.67       5.02       5.57       5.98       196.7
36.1       7098         100.0        5.08         4.67       5.02       5.57       5.97       196.7
37.1       7299         100.0        5.08         4.67       5.01       5.57       5.96       196.8
38.1       7499         100.0        5.08         4.67       5.01       5.56       5.96       196.9
39.1       7700         100.0        5.07         4.67       5.01       5.55       5.95       197.0
40.1       7900         100.0        5.07         4.67       5.01       5.54       5.94       197.0
41.1       8101         100.0        5.07         4.67       5.01       5.54       5.93       197.1
42.1       8301         100.0        5.07         4.67       5.01       5.54       5.93       197.1
43.1       8498         100.0        5.07         4.67       5.01       5.54       5.93       197.1
44.1       8697         100.0        5.07         4.67       5.01       5.53       5.93       197.2
45.1       8898         100.0        5.07         4.67       5.01       5.53       5.91       197.2
46.1       9100         100.0        5.06         4.67       5.00       5.52       5.89       197.3
47.1       9298         100.0        5.06         4.67       5.00       5.52       5.89       197.3
48.1       9498         100.0        5.06         4.67       5.00       5.51       5.89       197.4
49.1       9697         100.0        5.06         4.67       5.00       5.51       5.88       197.4
50.1       9897         100.0        5.06         4.67       5.00       5.51       5.88       197.4
50.6       10000        100.0        5.06         4.67       5.00       5.51       5.88       197.5
50.6       10000        100.0        5.06         4.67       5.00       5.51       5.88       197.5
==============================================================================================================
16:57:53 __main__ INFO   Query operation completed successfully!
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query --algorithm hnsw --query-count 1000 --num-results 100

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, HNSW, cosine, float32
Include ID:      Yes
Query Config:    1,000 queries, 100 results each
================================================================================
16:59:37 __main__ INFO   Running 1000 queries, returning 100 results each
16:59:37 __main__ INFO   Generated 1000 query embeddings.
16:59:37 __main__ INFO   Generating query embeddings took: 0.0091 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
1.0        198          100.0        5.05         4.75       5.01       5.42       5.83       197.9
2.0        399          100.0        5.02         4.73       4.99       5.39       5.58       199.0
3.0        598          100.0        5.02         4.73       4.99       5.35       5.58       198.9
4.0        798          100.0        5.02         4.73       4.99       5.35       5.54       199.2
5.0        997          100.0        5.02         4.73       4.99       5.36       5.61       198.9
5.0        1000         100.0        5.02         4.73       4.99       5.36       5.61       198.9
5.0        1000         100.0        5.02         4.73       4.99       5.36       5.61       198.9
==============================================================================================================
16:59:42 __main__ INFO   Query operation completed successfully!
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query --algorithm hnsw --query-count 1000 --num-results 10

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, HNSW, cosine, float32
Include ID:      Yes
Query Config:    1,000 queries, 10 results each
================================================================================
16:59:48 __main__ INFO   Running 1000 queries, returning 10 results each
16:59:48 __main__ INFO   Generated 1000 query embeddings.
16:59:48 __main__ INFO   Generating query embeddings took: 0.0088 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
0.7        1000         100.0        0.73         0.61       0.72       0.84       0.95       1373.8
0.7        1000         100.0        0.73         0.61       0.72       0.84       0.95       1372.8
==============================================================================================================
16:59:49 __main__ INFO   Query operation completed successfully!
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query --algorithm hnsw --query-count 1000 --num-results 3

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, HNSW, cosine, float32
Include ID:      Yes
Query Config:    1,000 queries, 3 results each
================================================================================
16:59:53 __main__ INFO   Running 1000 queries, returning 3 results each
16:59:53 __main__ INFO   Generated 1000 query embeddings.
16:59:53 __main__ INFO   Generating query embeddings took: 0.0085 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
0.5        1000         100.0        0.52         0.37       0.50       0.64       0.73       1934.3
0.5        1000         100.0        0.52         0.37       0.50       0.64       0.73       1932.2
==============================================================================================================
16:59:54 __main__ INFO   Query operation completed successfully!


=====
venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py load

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       LOAD
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, FLAT, cosine, float32
Include ID:      Yes
Data Size:       1,000,000 embeddings
================================================================================
06:51:18 __main__ INFO   === LOAD OPERATION ===
06:51:18 __main__ INFO   Index creation took: 0.0007 seconds
06:51:22 __main__ INFO   Generating fake embeddings took: 4.3753 seconds
06:51:23 __main__ INFO   Data preparation  took: 0.9043 seconds
06:51:23 __main__ INFO   Starting data loading into index.
06:52:10 __main__ INFO   Data Loading into index took: 47.4016 seconds
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query  --query-count 100 --num-results 3

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, FLAT, cosine, float32
Include ID:      Yes
Query Config:    100 queries, 3 results each
================================================================================
06:53:27 __main__ INFO   Running 100 queries, returning 3 results each
06:53:27 __main__ INFO   Generated 100 query embeddings.
06:53:27 __main__ INFO   Generating query embeddings took: 0.0029 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
1.1        11           100.0        96.53        92.53      93.91      102.99     104.54     10.4
2.1        22           100.0        95.73        92.53      93.73      101.05     104.12     10.4
3.2        33           100.0        95.89        92.53      93.91      101.03     103.69     10.4
4.2        44           100.0        95.90        92.53      93.90      101.05     103.33     10.4
5.3        55           100.0        96.01        92.53      93.89      101.34     103.31     10.4
6.4        66           100.0        96.28        92.53      93.97      101.33     102.97     10.4
7.4        77           100.0        96.18        92.53      93.89      101.31     102.64     10.4
8.5        88           100.0        96.23        92.53      93.90      101.32     102.31     10.4
9.5        99           100.0        96.26        92.53      93.91      101.36     101.98     10.4
9.6        100          100.0        96.24        92.53      93.91      101.35     101.95     10.4
9.6        100          100.0        96.24        92.53      93.91      101.35     101.95     10.4
==============================================================================================================
06:53:37 __main__ INFO   Query operation completed successfully!
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query  --query-count 100 --num-results 10

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, FLAT, cosine, float32
Include ID:      Yes
Query Config:    100 queries, 10 results each
================================================================================
06:53:43 __main__ INFO   Running 100 queries, returning 10 results each
06:53:43 __main__ INFO   Generated 100 query embeddings.
06:53:43 __main__ INFO   Generating query embeddings took: 0.0030 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
1.1        11           100.0        97.43        92.93      99.65      102.47     103.33     10.3
2.1        22           100.0        96.95        92.77      97.12      101.39     103.09     10.3
3.2        33           100.0        97.01        92.77      99.65      101.17     102.86     10.3
4.3        44           100.0        96.89        92.70      97.12      101.12     102.62     10.3
5.3        55           100.0        96.95        92.59      99.65      101.22     102.57     10.3
6.4        66           100.0        96.92        92.59      97.80      101.34     102.53     10.3
7.5        77           100.0        96.97        92.59      99.65      101.46     102.36     10.3
8.5        88           100.0        97.00        92.59      98.15      101.57     102.19     10.3
9.6        99           100.0        97.03        92.59      99.59      101.70     102.63     10.3
9.7        100          100.0        97.00        92.59      98.11      101.70     102.62     10.3
9.7        100          100.0        97.00        92.59      98.11      101.70     102.62     10.3
==============================================================================================================
06:53:53 __main__ INFO   Query operation completed successfully!
(venv) ubuntu@primary:~/redisvls$ python benchmarkvl.py query  --query-count 100 --num-results 100

================================================================================
REDIS VECTOR SEARCH BENCHMARK CONFIGURATION
================================================================================
Operation:       QUERY
Redis Server:    localhost:6379
Index Name:      redisvl
Vector Config:   960D, FLAT, cosine, float32
Include ID:      Yes
Query Config:    100 queries, 100 results each
================================================================================
06:53:58 __main__ INFO   Running 100 queries, returning 100 results each
06:53:58 __main__ INFO   Generated 100 query embeddings.
06:53:58 __main__ INFO   Generating query embeddings took: 0.0029 seconds

==============================================================================================================
Time (s)   Completed    Success Rate Mean (ms)    Min (ms)   P50 (ms)   P95 (ms)   P99 (ms)   QPS
==============================================================================================================
1.1        11           100.0        97.68        95.79      96.77      102.52     106.12     10.2
2.1        22           100.0        97.31        95.79      96.84      98.02      105.13     10.3
3.2        33           100.0        97.87        95.79      96.87      105.03     108.57     10.2
4.3        44           100.0        97.71        95.79      96.94      103.03     108.32     10.2
5.4        55           100.0        97.54        95.79      96.94      100.56     108.07     10.2
6.4        66           100.0        97.32        95.61      96.80      99.15      107.82     10.3
7.5        77           100.0        97.16        95.51      96.70      99.01      107.57     10.3
8.5        88           100.0        97.06        95.51      96.57      98.91      107.31     10.3
9.6        99           100.0        97.05        95.51      96.58      98.98      107.06     10.3
9.7        100          100.0        97.05        95.51      96.58      98.97      107.04     10.3
9.7        100          100.0        97.05        95.51      96.58      98.97      107.04     10.3
==============================================================================================================
06:54:08 __main__ INFO   Query operation completed successfully!
```