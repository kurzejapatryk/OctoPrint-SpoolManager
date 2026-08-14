# Contributing

Thanks for your interest in contributing to **OctoPrint-SpoolManager** — a
community-maintained fork of [OllisGit/OctoPrint-SpoolManager](https://github.com/OllisGit/OctoPrint-SpoolManager).

This document outlines how to contribute in a way that keeps the plugin stable,
backwards compatible, and safe for existing user data.

---

## Code of conduct

Be respectful and constructive. The project is maintained by volunteers and
reviews are a collaborative process.

---

## Ways to contribute

- Reporting bugs (see **Bug reports** below).
- Improving documentation.
- Submitting pull requests with bug fixes or small, well-scoped features.
- Testing development releases.
- Opening issues to propose larger changes before writing code.

---

## Before you start

- Read [AGENTS.md](AGENTS.md) — it documents the hard contracts (behavior,
  database, API, OctoPrint compatibility) that **must not be broken**.
- Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the technical overview.
- For non-trivial changes, [open an issue](https://github.com/kurzejapatryk/OctoPrint-SpoolManager/issues)
  first to discuss the approach before spending time on an implementation.

---

## Bug reports

Please open a [GitHub Issue](https://github.com/kurzejapatryk/OctoPrint-SpoolManager/issues)
and include:

- OctoPrint version
- SpoolManager version
- Python version
- Operating system
- Relevant logs
- Steps to reproduce the problem

---

## Development workflow

1. Fork the repository and create a feature branch from `development`.
2. Make small, logical commits.
3. Add or update **tests** for any behavior change.
4. Run the test suite locally (see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)).
   Tests must pass on **SQLite**, **PostgreSQL** and **MySQL** where applicable.
5. Open a pull request against the `development` branch.

Every pull request is expected to pass the CI checks
(`.github/workflows/tests.yml`).

---

## Testing

Tests live in `octoprint_spoolmanager/test/` and are discovered via the
`test_*.py` pattern. Quick local run (SQLite only):

```bash
PYTHONPATH=test_support python -m unittest discover -s octoprint_spoolmanager/test -p 'test_*.py'
```

For the full database matrix (SQLite + PostgreSQL + MySQL) and environment
variable details, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

---

## Hard contracts — please respect

- **Behavior is a contract.** Existing behavior is the spec; don't remove
  features just because they look old (QR scanning, templates, temperature
  offsets, multi-tool).
- **Protect user data.** Schema is **v7**. Migrations are SQLite SQL; external
  databases are created directly at the latest version. Never drop/recreate
  tables on a database with data.
- **Do not break the API.** Keep response shapes (e.g. `/loadSpoolsByQuery`:
  `allSpools`, `catalogs`, `templateSpools`, `selectedSpools`) and event-bus
  payloads stable.
- **Maintain OctoPrint compatibility.** Keep the `SpoolManager` identifier,
  mixins, hooks in `__plugin_load__`, and the supported Python range.

See [AGENTS.md](AGENTS.md) for the full list of rules and candidates for
cleanup that must be verified before removal.

---

## Code style

- **Backend:** Python with types and docstrings (target 3.11+). Use `ruff` /
  `mypy` / `pytest`. Many existing `.py` files use TAB indentation — unify it
  deliberately as part of a migration, not ad hoc churn.
- **Frontend:** assets in `3rdPartySoftware/` and vendored `static/js|css` are
  **out of scope** — do not modify them. Use ESLint/Prettier/`tsc` for frontend
  work.
- Commit messages should be concise and descriptive.

---

## License

This project is licensed under the **GNU Affero General Public License v3.0**
(SPDX: `AGPL-3.0-only`). By contributing, you agree that your contributions are
licensed under the same license. See [LICENSE](LICENSE) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
