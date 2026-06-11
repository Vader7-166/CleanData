## 1. Modify DBSCAN implementation

- [x] 1.1 Replace `cosine_distances` generation in `cluster_products` with directly passing sparse matrix `m` to `DBSCAN`
- [x] 1.2 Update the `eps` parameter to `np.sqrt(2 * eps)` to match euclidean distance mapping for L2 normalized vectors
- [x] 1.3 Update the `metric` to `'euclidean'` and `algorithm` to `'brute'` in `DBSCAN` initialization

## 2. Testing and Validation

- [x] 2.1 Verify clustering on a small dataset to ensure output labels are unchanged
- [x] 2.2 Rebuild the backend and run against the large test file (e.g. `850440-NK-Th1.2026`) to ensure OOM no longer occurs
