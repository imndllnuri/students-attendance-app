# Contributing

## Reporting bugs / requesting features

Open a GitHub issue using the bug report or feature request template. For
feature ideas, check `ROADMAP.md` first — it may already be scoped into a
phase.

## Submitting changes

1. Keep PRs focused — one bug fix or one feature per PR, not a mix.
2. Run `pytest -q` before opening the PR (see `TESTING.md`).
3. If you touched a `.ui` file, launch the app once manually and exercise
   the changed screen — the test suite doesn't render real windows.
4. Follow the code style below.
5. Update `CHANGELOG.md` under `## [Unreleased]`.
6. Update `ARCHITECTURE.md` if you changed the client/server boundary, the
   data model, or added a new module.
7. Fill out the PR template checklist.

## Code style

- **Never instantiate `ApiClient()` directly in a view.** Go through
  `AccountManager`/`ClassManager` (`models/accounts.py`, `models/classes.py`),
  adding a proxy method there if the one you need doesn't exist yet. This
  keeps the server boundary in one place and testable with a fake client
  (see `tests/test_models_managers.py`).
- **Reuse `shared/validation.py`** for email/password/security-question
  rules instead of redefining them per-view — they drifted out of sync once
  already (`reset_password_window.py` used to skip the letter+digit rule the
  other two forms enforced).
- **Use `logging`, not `print()`,** for anything that isn't a user-facing
  `QMessageBox`. `logging_config.setup_logging()` is called once in
  `main.py`; just do `logger = logging.getLogger(__name__)` in new modules.
