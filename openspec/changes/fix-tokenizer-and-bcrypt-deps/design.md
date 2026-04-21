## Context

The PhoBERT model's `AutoTokenizer` requires specific backend libraries (`protobuf` and `sentencepiece`) that were missing from the `slim` Python image. Furthermore, `passlib` has a known incompatibility with `bcrypt >= 4.0.0`, causing the `AttributeError: module 'bcrypt' has no attribute '__about__'`.

## Goals / Non-Goals

**Goals:**
- Fix the `ImportError` for `protobuf`.
- Fix the `ValueError` for `sentencepiece` when loading the tokenizer.
- Resolve the `bcrypt` crash to re-enable database initialization.

## Decisions

- **Pinned Dependencies**: Pin `bcrypt==3.2.2` in `requirements.txt` to ensure long-term stability with `passlib`.
- **Additional Backend Packages**: Explicitly add `protobuf` and `sentencepiece` to `requirements.txt` so the Docker build includes them.
- **Re-enable Startup Logic**: Uncomment the admin user creation in `main.py` now that the underlying hashing library is stable.

## Risks / Trade-offs

- **[Risk]** Pinned versions might become outdated.
  - **Mitigation**: Standard practice for production/stable environments; can be reviewed if `passlib` is updated to support newer `bcrypt`.
