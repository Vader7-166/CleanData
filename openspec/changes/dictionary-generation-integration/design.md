## Context

The system currently relies on manually created dictionary files for product classification. An external Python project (`Create_Dictionary`) has been developed that provides clustering (TF-IDF/DBSCAN) and LLM-based labeling (Groq) to automate this process. We need to port this logic into the main FastAPI backend and provide a user-friendly wizard in the React frontend.

## Goals / Non-Goals

**Goals:**
- Port clustering and keyword extraction logic to `backend/core/dict_generator.py`.
- Integrate Groq LLM for automatic cluster labeling.
- Create a 2-step UI wizard for dictionary generation.
- Support Excel (XLSX) processing for both raw and draft taxonomy files.

**Non-Goals:**
- Moving away from the current CSV-based dictionary format.
- Real-time training of classification models (this is a static generation tool).
- Replacing the existing manual upload feature.

## Decisions

### 1. Porting Strategy: Modular Service
- **Rationale**: Instead of running external scripts via subprocess, we will port the core logic into a reusable `DictionaryGenerator` class in `backend/core/`. This allows for better error handling, logging, and performance within the FastAPI event loop.
- **Alternatives**: Keeping the code in a separate folder and using `subprocess.run` (harder to manage dependencies and state).

### 2. Intermediate Storage: Temporary Files
- **Rationale**: Since the process is 2-step (Step 1 generates a draft, Step 2 uses the reviewed draft), we will use `backend/storage/processed` (or a dedicated `tmp` folder) to store the uploaded raw files during the session.
- **Alternatives**: Database storage for raw data (too heavy for this ephemeral task).

### 3. LLM Integration: Groq API & Configuration
- **Rationale**: Groq provides extremely low latency for Llama 3 models, making the interactive experience much better for users. We will use a batching strategy (already present in the source code) to minimize API calls.
- **Configuration**: The `GROQ_API_KEY` will be managed via a `.env` file using the `python-dotenv` library. This ensures the key is kept out of the source code and aligns with common security practices.
- **Alternatives**: OpenAI (slower/costlier), local LLM (requires significant server resources).

## Risks / Trade-offs

- **[Risk] LLM Hallucinations** → Mitigation: Step 1 output is a "Draft" that the user MUST review manually before Step 2.
- **[Risk] Rate Limits (Groq)** → Mitigation: Implement batching and retries with exponential backoff in the backend logic.
- **[Risk] Large File Performance** → Mitigation: Use `asyncio.to_thread` for heavy CPU tasks (clustering) to avoid blocking the API.
