## Summary

<!-- What does this PR change, and why? -->

## Checklist

- [ ] `pytest -q` passes locally
- [ ] Ran the app manually (`./run.sh` or the two-terminal steps) and exercised the changed flow
- [ ] Views only talk to the server through `AccountManager`/`ClassManager`, never `ApiClient` directly
- [ ] Shared constants/rules (email/password validation, etc.) reused from `shared/validation.py` instead of redefined
- [ ] Docs updated if behavior, setup, or architecture changed (`README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`)
