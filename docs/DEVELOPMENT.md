# Development Guide

This guide explains how to set up a development environment, run the test suite,
and understand the plugin's extension points. It targets contributors and
maintainers of **OctoPrint-SpoolManager**.

> For a deep technical overview of modules, the database schema and the hard
> compatibility contracts, read [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Requirements

- **Python** `>= 3.7, < 3.14` (matching OctoPrint's supported range). The codebase
  still contains some legacy Python-2-compatible code and is being modernized —
  Python **3.11** is the CI baseline.
- **OctoPrint** for a live instance; unit tests run without OctoPrint using the
  stubs in `test_support/`.
- **Docker / docker-compose** (optional) to run PostgreSQL and MySQL for the
  full test matrix.

---

## Project layout (short)

```
octoprint_spoolmanager/
  __init__.py                 # plugin entry point, lifecycle, business logic
  DatabaseManager.py           # connections, CRUD, schema migrations
  newodometer.py               # G-code filament odometer parsing
  api/SpoolManagerAPI.py      # REST endpoints (BlueprintPlugin)
  common/                     # StringUtils, SettingsKeys, EventBusKeys, CSVExportImporter
  models/                     # peewee models (BaseModel, SpoolModel, ...)
  static/js/                  # legacy KnockoutJS frontend
  templates/                  # Jinja2 UI templates
octoprint_spoolmanager/test/  # backend unit tests (test_*.py numbering is important)
test_support/                 # OctoPrint/past stubs to run tests without OctoPrint
docs/
  ARCHITECTURE.md
  DEVELOPMENT.md
```

---

## Local development setup

```bash
# 1. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install the plugin in editable mode plus test/DB dependencies
pip install -e .
pip install flask
# optional: database drivers for the external-database tests
pip install pymysql psycopg2-binary
```

Additional runtime dependencies are declared in `setup.py`. The plugin needs
`peewee`, `flask`, `qrcode`, `pillow`, plus the optional database drivers
`psycopg2-binary` (PostgreSQL) and `pymysql` (MySQL) for external databases.

---

## Running the tests

The test suite lives in `octoprint_spoolmanager/test/` and is auto-discovered by
the pattern `test_*.py`.

### Fast local run (SQLite only)

```bash
PYTHONPATH=test_support python -m unittest discover -s octoprint_spoolmanager/test -p 'test_*.py'
```

> `pytest` is the target test runner once the suite is migrated; for now the
> suite uses Python's built-in `unittest`.

### Full matrix (SQLite + PostgreSQL + MySQL)

Start the databases with Docker:

```bash
docker-compose up -d          # starts postgres:16 and mysql:5.7
```

Then run:

```bash
PYTHONPATH=test_support \
SPOOLMANAGER_TEST_POSTGRES=1 \
SPOOLMANAGER_TEST_MYSQL=1 \
python -m unittest discover -s octoprint_spoolmanager/test -p 'test_*.py'
```

The test configuration is read from environment variables (defaults in
parentheses):

| Variable                        | Purpose                    | Default       |
| ------------------------------- | -------------------------- | ------------- |
| `SPOOLMANAGER_TEST_POSTGRES`     | Enable PostgreSQL testing  | *(unset)*     |
| `SPOOLMANAGER_TEST_MYSQL`        | Enable MySQL testing       | *(unset)*     |
| `SPOOLMANAGER_TEST_PG_HOST`      | PostgreSQL host            | `localhost`   |
| `SPOOLMANAGER_TEST_PG_PORT`      | PostgreSQL port            | `5432`        |
| `SPOOLMANAGER_TEST_PG_NAME`      | PostgreSQL database        | `spoolmanagerdb` |
| `SPOOLMANAGER_TEST_PG_USER`      | PostgreSQL user            | `Olli`        |
| `SPOOLMANAGER_TEST_PG_PASSWORD`  | PostgreSQL password        | `illO`        |
| `SPOOLMANAGER_TEST_MYSQL_HOST`   | MySQL host                 | `localhost`   |
| `SPOOLMANAGER_TEST_MYSQL_PORT`   | MySQL port                 | `3306`        |
| `SPOOLMANAGER_TEST_MYSQL_NAME`   | MySQL database             | `spoolmanagerdb` |
| `SPOOLMANAGER_TEST_MYSQL_USER`   | MySQL user                 | `Olli`        |
| `SPOOLMANAGER_TEST_MYSQL_PASSWORD` | MySQL password           | `illO`        |

> Database migration tests use a fixture database at
> `octoprint_spoolmanager/test/spoolmanager_scheme_v3.db`. Do not modify it
> without intent — it exercises the v3 → v7 migration path.

---

## Continuous Integration

- **GitHub Actions:** `.github/workflows/tests.yml` runs the full matrix
  (SQLite + PostgreSQL + MySQL) on GitHub. `.github/workflows/release.yml`
  builds the plugin archive and creates releases on tag/push.
- **GitLab CI:** `.gitlab-ci.yml` runs the same tests, using the service
  aliases `postgres` and `mysql` (hence custom `*_HOST` values there).

Always run the suite locally before opening a pull request.

---

## Code quality

The project is being modernized. Target tooling (used as available):

- **Backend:** `ruff` for linting, `mypy` for type checking, `pytest` for tests.
- **Frontend:** `eslint` / `prettier`, TypeScript (`tsc`) as JavaScript is
  migrated to TypeScript.

Keep commits small and logical. See [CONTRIBUTING.md](../CONTRIBUTING.md).
Note that the majority of `.py` files still use **TAB** indentation — unify
whitespace deliberately as part of a migration, not as unrelated churn.

---

## Database

- Current schema version: **`CURRENT_DATABASE_SCHEME_VERSION = 7`**.
- Migrations (`_upgradeFromXToY`) are plain **SQLite** SQL. For external
  (PostgreSQL/MySQL) databases, migrations are skipped and the schema is
  created directly at the latest version.
- Never call `_createDatabaseTables()` on a database that contains user data
  without explicit approval — it drops and recreates tables.
- Any schema change requires a migration plan **and** a test.

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

---

## Events exposed to other plugins

SpoolManager fires custom events on the OctoPrint event bus. Events are emitted
with the `plugin_spoolmanager_` prefix (i.e. `plugin_spoolmanager_<key>`).

| Event name                                        | Payload                                                             |
| ------------------------------------------------- | ------------------------------------------------------------------- |
| `plugin_spoolmanager_spool_selected`              | `toolId`, `databaseId`, `spoolName`, `material`, `colorName`, `remainingWeight` |
| `plugin_spoolmanager_spool_deselected`            | `toolId`, `databaseId` (plus the spool fields above in most paths)  |
| `plugin_spoolmanager_spool_added`                 | `databaseId`, `spoolName`, `material`, `colorName`, `remainingWeight` |
| `plugin_spoolmanager_spool_deleted`               | `databaseId`                                                        |
| `plugin_spoolmanager_spool_weight_updated_after_print` | `toolId`, `databaseId`, `spoolName`, `material`, `colorName`, `remainingWeight` |

Example subscription (in another OctoPrint plugin):

```python
def on_event(self, event, payload):
    if event == "plugin_spoolmanager_spool_selected":
        self._logger.info("Spoool %s selected for tool %s",
                          payload.get("spoolName"), payload.get("toolId"))
```

> These event payloads are part of the API contract (consumed by MQTT and other
> plugins). Do not change them without checking `static/js` consumers and the
> README.
