---
layout: plugin

id: spoolmanager
title: SpoolManager
description: Advanced spool and filament management for OctoPrint.
author: Patryk Kurzeja
license: AGPL-3.0-only

homepage: https://github.com/kurzejapatryk/OctoPrint-SpoolManager
source: https://github.com/kurzejapatryk/OctoPrint-SpoolManager
archive: https://github.com/kurzejapatryk/OctoPrint-SpoolManager/releases/latest/download/spoolmanager.zip

tags:
- spool
- filament
- filament management
- spool management
- multi-tool
- filament usage
- weight
- length
- qr code
- csv

screenshots:
- url: /assets/img/plugins/spoolmanager/tab.png
  alt: Spool overview tab
  caption: Manage spools in a dedicated tab
- url: /assets/img/plugins/spoolmanager/sidebar.png
  alt: Spool selection in sidebar
  caption: Select and track spools from the sidebar

compatibility:

  octoprint:
  - 1.8.0

  python: ">=3.8,<4"

  os:
  - linux
  - windows
  - macos
  - freebsd

---

# SpoolManager

Advanced spool and filament management for OctoPrint.

SpoolManager keeps track of your filament spools inside OctoPrint. You can create
and edit spools, track remaining material, filament consumption and spool
selection directly in the OctoPrint UI.

## Features

- Create, edit and copy spools
- Template spools
- Track material, vendor, color, weight, length and notes
- Select a spool per tool (multi-tool support)
- Check whether enough filament remains before/during a print
- Track filament consumption after printing
- QR/barcode scanning
- Import/export spool data (CSV), including legacy FilamentManager data
- Custom events for other plugins (e.g. `plugin_spoolmanager_spool_selected`)

## Installation

Install via the OctoPrint Plugin Manager (search for **SpoolManager**) or download
the latest release archive:

https://github.com/kurzejapatryk/OctoPrint-SpoolManager/releases/latest

## Support

Report bugs and feature requests at:

https://github.com/kurzejapatryk/OctoPrint-SpoolManager/issues

## License

AGPL-3.0-only — see [LICENSE](https://github.com/kurzejapatryk/OctoPrint-SpoolManager/blob/master/LICENSE).