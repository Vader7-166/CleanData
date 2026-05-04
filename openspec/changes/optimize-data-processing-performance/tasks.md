## 1. Setup and Dependencies

- [x] 1.1 Add `pyahocorasick` to `backend/requirements.txt`
- [x] 1.2 Verify dependency installation and Aho-Corasick availability

## 2. Core Logic Refactoring

- [ ] 2.1 Refactor `DataCleaner` to extract `DictionaryMatcher` logic into a separate class or standalone functions compatible with multiprocessing
- [ ] 2.2 Implement Aho-Corasick automaton construction in `DictionaryMatcher`
- [ ] 2.3 Implement "consumption" matching logic in `DictionaryMatcher` to handle overlapping keywords correctly
- [ ] 2.4 Update scoring logic in `DictionaryMatcher` to use the new Aho-Corasick matches while maintaining High Value/Junk weighting

## 3. Multiprocessing Implementation

- [ ] 3.1 Create a multiprocessing initializer function that prepares the `DictionaryMatcher` in each worker process
- [ ] 3.2 Update `DataCleaner.process_async` to use `concurrent.futures.ProcessPoolExecutor` for Pass 1 (Dictionary Matching)
- [ ] 3.3 Refactor Information Extraction (`trich_xuat_thong_tin`) to execute in parallel within the same process pool
- [ ] 3.4 Implement efficient data chunking (e.g., 5000-10000 rows per chunk) to minimize IPC overhead

## 4. Pipeline Optimization

- [ ] 4.1 Increase AI inference batch size (e.g., to 64 or 128) and tune `MAX_CONCURRENT_CHUNKS`
- [ ] 4.2 Ensure the `ProcessPoolExecutor` is properly shut down after processing to free system resources
- [ ] 4.3 Update progress reporting to reflect the parallel processing stages

## 5. Validation and Testing

- [ ] 5.1 Verify that the output of the optimized pipeline matches the previous version for a sample dataset
- [ ] 5.2 Benchmark the new pipeline on a large dataset to confirm the performance improvement (> 5x target)
- [ ] 5.3 Monitor memory usage to ensure multiple worker processes don't exceed available RAM
