# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- feat: enable external database configuration section in settings UI (c3c9e4c)
- feat: enable PostgreSQL/MySQL drivers and validate database type (f848e7e)

### Fixed
- fix: restore scheme detection on old (pre-v4) databases (273b91f)
- fix: portable scheme check via ORM, close leaked connections, pin postgres:16 (623265e)
- fix: fail explicitly on external database scheme mismatch and surface it in settings UI (2af54d7)
- fix: show newly added spools on refresh by merging new filter catalog items (83462d3)
- fix: resolve pre-existing TabError (mixed tabs/spaces) in testOdometer.py (523e374)

### Documentation
- docs: add architecture documentation (audit-based) (acc0ef1)
- docs: document external database setup for multi-printer use (a3c6717)
- docs: add AGPL-3.0 LICENSE and third-party notices (ae1d32a)

### Testing
- test: remove dead/non-functional legacy test scripts (7d8f177)
- test: cover commitOdometerData (filament commit after print) (a211c8e)
- test: cover loadAllSpoolsByQuery (sort/filter/pagination) (0be4f61)
- test: cover NewFilamentOdometer G-code parsing (cc82ea5)
- test: cover v3 to v7 schema migration path (eff4b68)
- test: add unit tests for api/Transformer (b6242bc)
- test: rewrite DatabaseManager tests to run against SQLite/PostgreSQL/MySQL (fe47eee)

### Other
- ci: automatic releases with auto-versioning (master/pre-release/development); drop broken release workflow (fbb5ab7)
- chore: point plugin metadata and release channels to the fork (v1.7.1) (7136762)
- ci: add SPDX headers, disable auto-release on push (0c61095)
- ci: run tests on GitHub Actions and GitLab CI (SQLite+PostgreSQL+MySQL) (25d65c8)
- chore: add test stubs (test_support) so unit tests run without OctoPrint (6197c48)
- chore: remove deprecated unused FilamentOdometer module (a973ece)
- chore: ignore agent tooling artifacts (.agents/, skills-lock.json) (84b5df0)
- chore: add SPDX license headers to Python sources (24abcd6)
- chore: normalize license to AGPL-3.0-only and add maintained-fork note (e439518)
- chore: ignore local AGENTS.md (agent rules) (e8d937b)

---

## [1.7.0] - 2022-03-18

- Version 1.7.0 of the plugin. For the detailed history before the fork, see
  the upstream project's release notes: <https://github.com/OllisGit/OctoPrint-SpoolManager/releases>.

## [1.6.1] - 2022-01-31

## [1.6.0] - 2022-01-12

## [1.5.0] - 2021-10-24

## [1.4.3] - 2021-05-25

## [1.3.4] - 2021-04-17

## [1.2.0] - 2020-09-03

## [1.1.0]

## [1.0.0] - 2020-08-20

---

For releases prior to the 1.6.0 tag, refer to the Git history and the upstream
release notes. Dates above are derived from the repository tags.