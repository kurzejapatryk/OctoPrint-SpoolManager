# OctoPrint-SpoolManager

[![CI](https://github.com/kurzejapatryk/OctoPrint-SpoolManager/actions/workflows/tests.yml/badge.svg)](https://github.com/kurzejapatryk/OctoPrint-SpoolManager/actions/workflows/tests.yml)
[![Latest Release](https://img.shields.io/github/v/release/kurzejapatryk/OctoPrint-SpoolManager)](https://github.com/kurzejapatryk/OctoPrint-SpoolManager/releases)
[![License](https://img.shields.io/github/license/kurzejapatryk/OctoPrint-SpoolManager)](LICENSE)

> Advanced spool and filament management for OctoPrint.

OctoPrint-SpoolManager manages filament spools and their usage directly inside OctoPrint.

The plugin keeps track of spool information, remaining material, filament consumption and spool selection during printing.

---

## 🚧 Project Status

This project is a **community-maintained fork** of [OllisGit/OctoPrint-SpoolManager](https://github.com/OllisGit/OctoPrint-SpoolManager).

The original project was created and maintained by **OllisGit**.

This fork exists to continue development and modernize the plugin while preserving compatibility with existing installations and user data.

### Current focus

- Stabilizing the existing codebase
- Improving test coverage
- Maintaining compatibility with OctoPrint
- Modernizing the frontend
- Migrating the legacy JavaScript frontend to TypeScript
- Improving the development and release workflow
- Fixing long-standing bugs and technical debt

> The project is currently under active development. Some planned features and migrations are not yet complete.

---

## ✨ Features

### Spool management

- Create and edit spools
- Copy existing spools
- Create template spools
- Track material type
- Track manufacturer/vendor
- Track color
- Track remaining weight
- Track used filament
- Add notes
- Import and export spool data
- Import legacy FilamentManager data
- CSV import/export

### Printing

- Select a spool before printing
- Multi-tool support
- Check whether enough filament remains
- Track filament consumption after printing
- Support manual mid-print filament changes

### User interface

- Search and filter spools
- Sort spool lists
- Configure visible table columns
- QR/barcode scanning
- Detailed spool management dialogs
- Improved error handling

---

## 🖨️ OctoPrint Integration

SpoolManager integrates directly with OctoPrint and can react to printing-related events.

The plugin exposes custom events that other OctoPrint plugins can subscribe to.

Current events include:

- `plugin_spoolmanager_spool_weight_updated_after_print`
- `plugin_spoolmanager_spool_selected`
- `plugin_spoolmanager_spool_deselected`
- `plugin_spoolmanager_spool_added`
- `plugin_spoolmanager_spool_deleted`

See the [Developer Documentation](docs/DEVELOPMENT.md) for the event payloads and integration details.

---

## 🔌 Integrations

SpoolManager is designed to work together with other OctoPrint plugins.

Known integrations include:

- PrintJobHistory
- MQTT
- Other plugins consuming SpoolManager events

Integration compatibility is considered part of the project's API stability.

---

## 📦 Installation

### OctoPrint Plugin Manager

The recommended installation method is the OctoPrint Plugin Manager.

Open:

**Settings → Plugin Manager → Get More**

and search for:

**SpoolManager**

### Manual installation

Stable releases can also be installed from a release archive:

https://github.com/kurzejapatryk/OctoPrint-SpoolManager/releases/latest/download/master.zip

> Development versions should not be installed on production OctoPrint instances unless you understand the risks.

---

## 🧪 Development

This project uses automated tests and GitHub Actions to validate changes.

Before submitting a pull request, run the test suite locally:

```bash
pytest
```

Additional development commands and environment setup are documented in:

- [Development Guide](docs/DEVELOPMENT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Contributing](CONTRIBUTING.md)

Every pull request is expected to pass the project's CI checks.

---

## 🛣️ Roadmap

The project is being modernized incrementally.

### Phase 1 — Stabilization

- [x] Document existing architecture
- [x] Improve backend test coverage
- [x] Add database migration tests
- [x] Add API regression tests
- [x] Establish GitHub Actions CI
- [x] Establish automated plugin builds

### Phase 2 — Frontend modernization

- [ ] Migrate legacy JavaScript to TypeScript
- [ ] Introduce typed API contracts
- [ ] Separate business logic from UI logic
- [ ] Improve frontend test coverage

### Phase 3 — Modern frontend

- [ ] Introduce Vue 3
- [ ] Convert existing UI into reusable components
- [ ] Improve state management
- [ ] Modernize frontend build tooling

### Phase 4 — Continued modernization

- [ ] Improve database migration system
- [ ] Improve external database support
- [ ] Review and modernize integrations
- [ ] Improve documentation

The roadmap is intentionally incremental. Existing functionality and user data should remain protected during the migration.

---

## 🤝 Contributing

Contributions are welcome.

Before making significant changes, please open an issue to discuss the proposed change.

For development guidelines, see:

[CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🐛 Bug Reports

If you encounter a problem, please open a [GitHub Issue](https://github.com/kurzejapatryk/OctoPrint-SpoolManager/issues).

When reporting a bug, please include:

- OctoPrint version
- SpoolManager version
- Python version
- operating system
- relevant logs
- steps to reproduce the problem

---

## 📜 Original Project

This project is a fork of:

**OctoPrint-SpoolManager by OllisGit**

Original repository:

https://github.com/OllisGit/OctoPrint-SpoolManager

The original project and its contributors are credited and preserved according to its license.

This fork is independently maintained and developed.

---

## ❤️ Support

If you find this project useful, the best way to support it is by:

- reporting bugs
- improving documentation
- submitting pull requests
- testing development releases
- sharing the project with other OctoPrint users

If financial support is added in the future, it will be listed here.

---

## 📄 License

This project remains under the license of the original project.

See [LICENSE](LICENSE) for details.

---

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Development](docs/DEVELOPMENT.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Releases](https://github.com/kurzejapatryk/OctoPrint-SpoolManager/releases)