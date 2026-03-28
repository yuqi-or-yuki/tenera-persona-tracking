# Clustering Research & Implementation Plan

## Research Sources

- [Comprehensive investigation of clustering algorithms for UEBA (Frontiers, 2024)](https://www.frontiersin.org/journals/big-data/articles/10.3389/fdata.2024.1375818/full)
- [Data-driven Persona with B2B Software (IEEE/ACM CHASE, 2024)](https://dl.acm.org/doi/10.1145/3641822.3641870)
- [Comparison of K-Means and HDBSCAN for Marketing Strategies (2025)](https://www.researchgate.net/publication/387934161)
- [15-Year Survey of Data-Driven Persona Development](https://www.tandfonline.com/doi/full/10.1080/10447318.2021.1908670)
- [Pipedrive: Behavioral Personas with Cluster Analysis](https://medium.com/pipedrive-engineering/identifying-behavioral-personas-with-cluster-analysis-86b724ad0365)
- [K-Prototypes for mixed data clustering](https://juandelacalle.medium.com/k-prototypes-other-statistical-techniques-to-cluster-with-categorical-and-numerical-features-a-ac809a000316)

## Algorithm Selection

We implement three algorithms, each suited for different scenarios:

### 1. K-Means (default)
- **When:** Clean numerical data, roughly spherical clusters, you know K
- **Pros:** Fast, simple, well-understood, works with MiniBatch for real-time
- **Cons:** Must specify K, assumes equal-size spherical clusters, numerical only
- **Our use:** Default for entity-based persona clustering after encoding

### 2. HDBSCAN
- **When:** Unknown number of clusters, irregular densities, noisy data
- **Pros:** Discovers K automatically, handles noise (labels outliers), density-aware
- **Cons:** Slower on large datasets, can be sensitive to min_cluster_size
- **Our use:** Discovery mode — "show me what clusters exist"

### 3. K-Prototypes
- **When:** Mixed numerical + categorical entity data
- **Pros:** Handles mixed types natively (Euclidean + Hamming distance)
- **Cons:** Must specify K, slower than K-Means
- **Our use:** When entities contain both categorical and numerical values

## Feature Engineering

Personas are clustered based on their **entities** (key-value properties).

### Preprocessing Pipeline
1. Pivot entities into a feature matrix: rows = personas, columns = entity keys
2. Detect column types:
   - Numeric values → standardize (z-score)
   - Categorical values → one-hot encode (for K-Means/HDBSCAN) or leave as-is (K-Prototypes)
3. Handle missing values: fill with column mode (categorical) or median (numerical)
4. Optional: dimensionality reduction with PCA if > 20 features

### Example
```
Persona     | plan       | company_size | industry  | monthly_spend
------------|------------|--------------|-----------|---------------
user_123    | enterprise | 500          | tech      | 2000
user_456    | free       | 5            | education | 0
user_789    | pro        | 50           | tech      | 500
```

## Cluster Evaluation

### Automatic metrics (returned with results)
- **Silhouette score** (primary): -1 to 1, higher = better separation. > 0.5 is good.
- **Calinski-Harabasz index**: Higher = better. Ratio of between-cluster to within-cluster variance.
- **Davies-Bouldin index**: Lower = better. Average similarity between clusters.

### Optimal K selection
- Run K-Means for K = 2..10
- Pick K with best silhouette score
- Cap at 7 for actionability (per research consensus)

## Implementation

### Clustering runs are stored
Each clustering run produces:
- `ClusterRun`: metadata (algorithm, params, metrics, timestamp)
- `ClusterAssignment`: which persona belongs to which cluster
- Cluster labels are auto-generated from dominant entity values

### Cron scheduling
- Users configure a cron schedule (e.g. daily at 2am)
- The scheduler triggers a re-clustering run
- Results are stored; old runs are kept for comparison

### API
```
POST   /api/v1/clusters/run          — trigger a clustering run
GET    /api/v1/clusters/runs         — list past runs
GET    /api/v1/clusters/runs/{id}    — get run details + assignments
GET    /api/v1/clusters/latest       — get latest run results
```

### CLI
```
tpt cluster run                      — trigger clustering
tpt cluster run --algo hdbscan       — use HDBSCAN
tpt cluster results                  — show latest results
tpt cluster history                  — list past runs
```
