# CI

`ci.yml` runs on every push / PR:

- **Backend**: `ruff` lint → `mypy` (advisory) → `pytest`.
- **Frontend**: `tsc --noEmit` type-check → `next build`.

The backend job forces the in-memory SQLite fallback so no database service is
needed in CI. The mock-detector fallback means tests run without a GPU or the
heavy `[ai]` extra.
