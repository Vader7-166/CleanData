## Why

Currently, if a user navigates away from the AI Dictionary Generation wizard while a task (e.g., DeepSeek LLM labeling) is running, the frontend loses the progress state even though the backend process continues. This leaves the user without visibility into the completion status of their long-running tasks. Furthermore, users lack a visual progress indicator during generation, and the dictionary management interface does not allow selecting or activating multiple dictionaries simultaneously. Solving these issues will dramatically improve the user experience and reliability of the data preparation pipeline.

## What Changes

- Implement background task tracking (polling or Server-Sent Events) for dictionary generation so the frontend can recover the state of active jobs.
- Add a progress indicator (progress bar and status messages) to the UI to show real-time updates of the LLM labeling batch progress.
- Update the Dictionary Management page to support multi-selection, allowing users to activate or manage multiple dictionaries at the same time.

## Capabilities

### New Capabilities
- `background-job-tracking`: A mechanism for tracking long-running jobs (like LLM clustering/labeling) persistently across page navigations.
- `realtime-progress-ui`: Real-time frontend updates indicating the precise progress of backend processes.

### Modified Capabilities
- `multi-dictionary-management`: Expanding the existing dictionary management to handle bulk selections and multi-activation.

## Impact

- **Frontend**: Significant updates to `DictionaryGeneratorWizard.tsx` (progress UI and job recovery) and `Dictionary.tsx` (multi-select capabilities).
- **Backend**: API enhancements in `main.py` and `dict_generator.py` to report granular progress (e.g., batch completion status) and handle multi-dictionary activation.
- **Database/State**: May require persisting the generation job state either in memory, Context, or Database so it can be resumed by the client.
