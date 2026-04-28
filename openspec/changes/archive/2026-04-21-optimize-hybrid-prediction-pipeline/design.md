## Context

The backend data cleaning API recently implemented a Hybrid Prediction mechanism (Dictionary scoring followed by a PhoBERT AI fallback). However, performance profiling revealed that predicting a small 500-row chunk takes several minutes. This bottleneck stems from iterating through the dataframe row-by-row, running dynamic regex searches against the dictionary, and calling the PhoBERT model for each individual text (batch size 1). To process a typical 30k-row Excel file, this pipeline would take hours.

## Goals / Non-Goals

**Goals:**
- Decouple the Dictionary (`dictv3`) prediction step from the AI prediction step so they can run sequentially on the entire dataset.
- Optimize the Dictionary prediction step by pre-compiling regular expressions.
- Optimize the AI prediction step by running inference on batches (e.g., size 32) instead of individual rows, utilizing the hardware efficiently.
- Keep the progress logging via SSE functional, adjusting the chunks to report progress on the new batched architecture.

**Non-Goals:**
- Completely rewriting the dictionary logic to use Aho-Corasick or FlashText (though this is an option, pre-compiling regex is a sufficient first step to see immediate gains without over-engineering).
- Retraining the AI model.

## Decisions

- **Two-Pass Architecture:** The `process_async` method will be refactored to first run the `predict_dictionary` logic on all rows. It will then identify which rows failed the dictionary check (score < threshold) and extract them into a separate subset.
- **Batch Processing for AI:** The subset of rows that failed the dictionary check will be passed to a new `predict_ai_batch` method. This method will tokenize texts in batches and pass them through `self.model(**inputs)`, extracting the predicted labels in bulk.
- **Re-merging Results:** The labels from the Dictionary pass and the AI pass will be merged back into the main DataFrame using pandas indexing.
- **Pre-compiled Regex:** During the initialization of the `DataCleaner` (`_load_dict`), the dictionary keywords will be parsed and pre-compiled using `re.compile(r'\b' + re.escape(kw) + r'\b')`. This avoids parsing the regex string repeatedly during the prediction loop.

## Risks / Trade-offs

- **Memory Spikes during Batching:** Running the AI model on batches increases memory usage. Mitigation: The batch size will be configurable, starting at a conservative default (e.g., 32 or 64) to prevent Out-Of-Memory (OOM) errors on machines with limited RAM/VRAM.
- **Progress Reporting Granularity:** Because the AI and Dictionary passes are now decoupled, the progress log might look different (e.g., "Dictionary Pass...", then "AI Pass (Batch 1/10)..."). Mitigation: Update the SSE progress messages to reflect the new architecture accurately so the user knows what is happening.
