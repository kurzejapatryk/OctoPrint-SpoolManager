# Architektura — OctoPrint-SpoolManager (fork)

Dokument opisuje **rzeczywisty stan** repozytorium (wynik audytu technicznego).
Jest punktem wyjścia do modernizacji: Python 3.11+, TypeScript, Vue 3.
Uwaga: w tym dokumencie opisany jest stan **przed** modernizacją; kontrakt zachowania
(rozdział 15) obowiązuje również w trakcie i po modernizacji.

## 1. Przegląd

**Czym jest projekt:** wtyczka OctoPrint do zarządzania szpulami filamentu.
Przechowuje dane szpul w bazie, śledzi zużycie filamentu przez analizę G-code,
pozwala przypisać szpule do narzędzi (multi-tool), ostrzega przed brakiem filamentu,
oferuje eksport/import CSV, kody QR, szablony i zewnętrzną bazę danych (wiele drukarek).

**Rozmiar:** ~10,6 tys. linii własnego kodu (Python ~4,5k + JS ~4,2k + Jinja2 ~1,9k)
+ vendored biblioteki JS.

**Główne przypadki użycia:**
1. CRUD szpul (nazwa, materiał, kolor, producent, waga, długość, średnica, gęstość, temperatury, notatki).
2. Wybór szpuli per narzędzie (sidebar + dialog) przed i w trakcie druku.
3. Śledzenie zużycia filamentu (długość/waga) przez analizę G-code (`E`-ruchy).
4. Ostrzeżenie o zbyt małej ilości filamentu (na podstawie metadanych G-code).
5. Eksport/import CSV (backup, migracja, próbka `sampleCSV`).
6. Kody QR — generowanie (obraz z logo) i skanowanie → wybór szpuli.
7. Szablony (template spool) i kopiowanie.
8. Multi-tool (przypisanie szpuli do każdego ekstrudera).
9. Offsety temperatur per szpula (aplikowane do drukarki).
10. Zewnętrzna baza danych (PostgreSQL/MySQL) — jedna baza dla wielu drukarek.

## 2. Mapa architektury

```
[OctoPrint host]
  ├─ SpoolmanagerPlugin (octoprint_SpoolManager/__init__.py)  ← lifecycle, eventy, business logic
  │    ├─ SpoolManagerAPI (api/SpoolManagerAPI.py, mixin)     ← endpointy REST
  │    ├─ DatabaseManager (DatabaseManager.py)                ← połączenia + CRUD + migracje (peewee)
  │    │    └─ models (BaseModel, SpoolModel, PluginMetaDataModel)
  │    ├─ NewFilamentOdometer (newodometer.py)                ← analiza G-code
  │    ├─ common (StringUtils, SettingsKeys, EventBusKeys, CSVExportImporter)
  │    └─ api/Transformer (Transformer.py)                    ← model → dict (JSON)
  │
  └─ [frontend, KnockoutJS]
       ├─ SpoolManager.js (root viewmodel) → TableItemHelper, FilterSorter, dialogs, APIClient
       ├─ templates/*.jinja2 (DOM)
       └─ static/js/* (logika UI + logika biznesowa w UI)
```

## 3. Przepływ danych (główna pętla)

1. **G-code → drukarka:** hook `octoprint.comm.protocol.gcode.sent` → `SpoolmanagerPlugin.on_sentGCodeHook`
   → `NewFilamentOdometer.processGCodeLine()` → akumulacja ekstruzji per narzędzie →
   `_extrusionValuesChanged` → push do klienta (socket).
2. **Start druku:** event `PRINT_STARTED` → `_on_printJobStarted` → reset odometru, odczyt metadanych
   filamentu, ustawienie `firstUse` na szpuli.
3. **Koniec druku:** `PRINT_DONE/FAILED/CANCELLED/PAUSED` → `_on_printJobFinished` →
   `commitOdometerData()` → zapis `usedLength`/`usedWeight` do wybranych szpul → event bus →
   push `reloadTable and sidebarSpools`.
4. **Frontend ↔ backend:** REST (BlueprintPlugin) + push przez socket (`_sendDataToClient`).

## 4. Backend (Python)

### 4.1 Moduły

| Moduł | Odpowiedzialność | Zależności | Linie | Sprzężenie |
|---|---|---|---|---|
| `octoprint_SpoolManager/__init__.py` — `SpoolmanagerPlugin` | lifecycle, eventy, logika biznesowa, ustawienia, socket | DatabaseManager, NewFilamentOdometer, SpoolManagerAPI, Transformer, common | 959 | BARDZO WYSOKIE (god-object) |
| `DatabaseManager.py` — `DatabaseManager` | połączenia (SQLite/PG/MySQL), schemat, migracje, CRUD, katalogi, backup | peewee (star import), models, Transformer, StringUtils | 1180 | WYSOKIE (god-object) |
| `api/SpoolManagerAPI.py` — `SpoolManagerAPI` | wszystkie endpointy REST, mapowanie JSON↔model, import CSV (async), QR | BlueprintPlugin, DatabaseManager, models, Transformer, CSVExportImporter, SettingsKeys, EventBusKeys | 1009 | WYSOKIE (mixin zależny od `SpoolmanagerPlugin`) |
| `models/BaseModel.py` | baza modeli: `databaseId`, `created`, `updated`, `version`, `originator`; `table_function` → prefiks `spo_` | peewee | 32 | Niskie |
| `models/SpoolModel.py` | ~40 pól szpuli | BaseModel | 82 | Niskie |
| `models/PluginMetaDataModel.py` | `key`/`value` (wersja schematu, wersja pluginu) | BaseModel | 17 | Niskie |
| `api/Transformer.py` | `transformSpoolModelToDict` — model→dict, daty/wagi/procenty | SpoolModel, StringUtils | 101 | Średnie (mutuje `__data__`) |
| `common/StringUtils.py` | formatowanie (float/int/datetime), `to_bytes/to_unicode/to_native_str` (Py2) | `past` | 266 | Niskie |
| `common/SettingsKeys.py` | stałe kluczy ustawień (płaskie) | — | 51 | Niskie |
| `common/EventBusKeys.py` | 5 stałych eventów | — | 13 | Niskie |
| `common/CSVExportImporter.py` | CSV: `CSVColumn` + formattery/parsery per pole, import/eksport, sample | SpoolModel, StringUtils | 410 | Średnie |
| `newodometer.py` — `NewFilamentOdometer` | AKTYWNY odometer G-code (G0-G3, G90/91/92, M82/83, M605, T…) | — (skopiowany z OctoPrint 1.5.2) | 234 | Niskie |
| `Odometer.py` — `FilamentOdometer` | **DEPRECATED** odometer regex (nieużywany; tylko testOdometer) | — | 136 | Niskie |
| `Usecases.py` | **szkielet/dead code** (`saveSpool` = `pass`, `logging` niezaimportowane) | — | 20 | Niskie |
| `WrappedLoggingHandler.py` | przekierowanie logów SQL peewee | logging | 16 | Niskie |

### 4.2 Lifecycle i eventy

- **Start:** `initialize()` (StartupPlugin) → tworzy `DatabaseManager`, buduje ustawienia bazy
  (`_buildDatabaseSettingsFromPluginSettings`), `initDatabase`, tworzy `NewFilamentOdometer`.
- **Eventy** (`on_event`): `PRINT_STARTED`, `PRINT_PAUSED`, `PRINT_DONE`, `PRINT_FAILED`,
  `PRINT_CANCELLED`, `FILE_SELECTED`, `FILE_DESELECTED`, `UPDATED_FILES`.
- **Hooki** (`__plugin_load__`): `softwareupdate.check_config`, `comm.protocol.gcode.sent`,
  `events.register_custom_events`.
- **Custom events** (`register_custom_events` + `EventBusKeys`): `spool_weight_updated_after_print`,
  `spool_selected`, `spool_deselected`, `spool_added`, `spool_deleted`.

### 4.3 Konfiguracja

- `get_settings_defaults()` — **płaskie** ustawienia (komentarz autora: zagnieżdżone nie działają).
- `on_settings_save()` — czyści offsety temperatur, ponownie aplikuje offsety.
- `on_api_get()` (SimpleApiPlugin) — `resetSettings`, `isResetSettingsEnabled`, `additionalSettingsValues`.
- `get_update_information()` — kanały release (master / pre-release / development) + pip z release zip.
- `__plugin_pythoncompat__ = ">=2.7,<4"` — deklaracja Py2 (do usunięcia w modernizacji).

## 5. Frontend (JavaScript, KnockoutJS)

### 5.1 Moduły

| Plik | Rola | Linie |
|---|---|---|
| `static/js/SpoolManager.js` | Root viewmodel `SpoolManagerViewModel` — spinacz wszystkiego | 1213 |
| `static/js/SpoolManager-EditSpoolDialog.js` | Dialog edycji + `SpoolItem` (model ~40 observable) + konwersje jednostek | 967 |
| `static/js/SpoolManager-SpoolSelectionTableComp.js` | KO component tabeli wyboru + filtr kliencki | 438 |
| `static/js/SpoolManager-FilterSorter.js` | Filtr/sort listy szpul w sidebarze (klient) | 434 |
| `static/js/TableItemHelper.js` | Paginacja/sort/filtr serwerowy + katalogi | 424 |
| `static/js/ComponentFactory.js` | Fabryki widgetów jQuery (datetime, color picker, Quill) | 339 |
| `static/js/SpoolManager-APIClient.js` | Klient API (jQuery `$.ajax`) | 224 |
| `static/js/SpoolManager-ImportDialog.js` | Modal statusu importu CSV | 99 |
| `static/js/ResetSettingsUtilV3.js` | Wstrzyknięcie „Reset Settings" do dialogu OctoPrint | 99 |
| `static/js/SpoolManager-DatabaseConnectionProblemDialog.js` | Modal problemu z bazą | 65 |

### 5.2 Podział logiki (A–G)

- **A. Business logic:** `EditSpoolDialog.js` (`densityMap`, konwersja waga↔długość, procenty,
  `stateValues` initial/used/remaining, `scopeValues` filament/spool/combined, `amIRootChange`);
  `TableItemHelper._evalFilter`; filtrowanie w `FilterSorter`/`SpoolSelectionTableComp`.
- **B. API / data access:** `SpoolManager-APIClient.js` (1:1 opakowanie endpointów).
- **C. State management:** root VM (`SpoolManager.js`): `spoolItemTableHelper`, `sidebarFilterSorter`,
  `spoolDialog`, `apiClient`, `selectedSpoolsForSidebar`, `allSpoolsForSidebar`, `pluginSettings`,
  `databaseMetaData`, `tableAttributeVisibility`; persystencja `localStorage` (widoczność kolumn,
  rozmiar strony, filtry).
- **D. UI logic:** `SpoolManager.js` (okablowanie, `onDataUpdaterPluginMessage`, `closeDialogHandler`,
  `selectSpoolForSidebar`, override `settingsViewModel.saveData` i `printerStateViewModel.print`).
- **E. DOM manipulation:** `ComponentFactory.js` (widgety jQuery), `ResetSettingsUtilV3.js` (DOM OctoPrint),
  `EditSpoolDialog._reColorFilamentIcon` (SVG), `SpoolSelectionTableComp` (czyta `$("#spm-select-spool-table").html()`).
- **F. OctoPrint integration:** `SpoolManager.js` (parametry VM, `UI_API_KEY`, `BASEURL`, socket push),
  `ResetSettingsUtilV3.js` (dialog ustawień).
- **G. Third-party:** `quill`, `jquery.datetimepicker`, `pick-a-color`, `tinycolor`, `select2` (+ jQuery/moment z rdzenia OctoPrint).

### 5.3 Stan aplikacji (współdzielony)

`selectedSpoolsForSidebar`, `allSpoolsForSidebar`, katalogi (material/vendor/color), `databaseMetaData` —
współdzielone między sidebar, dialogiem i tabelą. Naturalny kandydat na Pinia store.

## 6. API — kontrakt frontend↔backend

Wszystkie endpointy to **publiczny kontrakt**. Baza: `/plugin/SpoolManager/...`.

| Metoda | Ścieżka | Request | Response | Użycie w FE |
|---|---|---|---|---|
| GET | `/sampleCSV` | — | plik CSV | `getSampleCSVUrl` |
| GET | `/allowedToPrint` | — | JSON (result, noSpoolSelected…) | `allowedToPrint` |
| GET | `/startPrintConfirmed` | — | JSON | `startPrintConfirmed` |
| PUT | `/selectSpool` | {databaseId, toolIndex, commitCurrentSpoolValues?} | {selectedSpool} | `callSelectSpool` |
| GET | `/selectSpoolByQRCode/<id>` | — | redirect 307 | QR link |
| GET | `/generateQRCode/<id>` | ?fillColor,backgroundColor,urlPrefix | image/jpeg | QR |
| GET | `/generateQRCodeView/<id>` | — | — | — |
| POST | `/importCSV` | multipart (importCSVMode) | async push | `performCSVImportFromUpload` |
| GET | `/downloadDatabase` | — | plik .db | `getDownloadDatabaseUrl` |
| POST | `/deleteDatabase/<type>` | JSON databaseSettings | {result} | `callDeleteDatabase` |
| GET | `/loadDatabaseMetaData` | — | {metadata} | `loadDatabaseMetaData` |
| PUT | `/testDatabaseConnection` | JSON databaseSettings | {metadata} | `testDatabaseConnection` |
| PUT | `/confirmDatabaseProblemMessage` | — | — | `confirmDatabaseProblemMessage` |
| GET | `/exportSpools/<type>` | — | CSV | `getExportUrl` |
| GET | `/loadSpoolsByQuery` | query params | {templateSpools, catalogs, totalItemCount, allSpools, selectedSpools} | `callLoadSpoolsByQuery` |
| PUT | `/saveSpool` | JSON spool (wszystkie pola) | JSON() | `callSaveSpool` |
| DELETE | `/deleteSpool/<id>` | — | JSON() | `callDeleteSpool` |
| GET | `api/plugin/SpoolManager?action=…` | resetSettings / isResetSettingsEnabled / additionalSettingsValues | JSON | `callAdditionalSettings`, `ResetSettingsUtilV3` |

**Niezmienialne bez zachowania kompatybilności:** `/loadSpoolsByQuery`, `/saveSpool`, `/selectSpool`,
`/allowedToPrint`, payloady event bus (`spool_added`, `spool_selected`, …).

## 7. Baza danych

- **Tabele:** `spo_spoolmodel` (~40 kolumn: identyfikatory, waga/długość, temperatury, kolory,
  notatki, daty, indeksy na `material`/`vendor`/`materialCharacteristic`), `spo_pluginmetadatamodel`
  (`key`/`value` — `databaseSchemeVersion`, `pluginVersion`). **Brak relacji FK.**
- **Wersjonowanie:** `CURRENT_DATABASE_SCHEME_VERSION = 7`. Migracje `_upgradeFrom1To2`…`_upgradeFrom9To10`
  to surowy SQL **SQLite**; dla zewnętrznej bazy pomijane (tworzenie od razu w v7 przez peewee `create_tables`).
- **CRUD:** lokalnie `spoolmanager.db`; zewnętrznie PG/MySQL. `saveSpool` przelicza `remainingWeight`
  i stosuje optymistyczną blokadę (`version`).
- **Ryzyko dla danych:** patrz rozdział 11 i `AGENTS.md` (TWARDE KONTRAKTY → Baza danych).

## 8. Testy — stan i luki

**Jest:** `test/test_DatabaseManager.py` (połączenie + CRUD na SQLite/PG/MySQL, gated env-varami),
`test_CSVExporterImporter.py`, `testOdometer.py`, `test_Scratchpad.py`, fixture `test/spoolmanager_scheme_v3.db`.

**Brak:** testy API (zero HTTP), lifecycle/eventy (`commitOdometerData`, `_on_printJobFinished`),
frontend (zero), migracje schematu, Transformer, konwersje jednostek z `EditSpoolDialog`.

**Testy do stworzenia PRZED migracją:** Transformer, `loadAllSpoolsByQuery` (sort/filtr/paginacja),
migracje v1→v7 (jest fixture v3), `NewFilamentOdometer`, konwersje jednostek (po wydzieleniu),
kontrakt JSON API (snapshoty), `commitOdometerData`.

## 9. Third-party i legacy

- **Vendored (nie ruszać):** `3rdPartySoftware/` — quill (11,5k), datetimepicker-2.5.20, pick-a-color,
  select2-4.0.10/4.0.13, tinycolor, bootstrap-datepicker; kopie w `static/js|css`. Licencje w
  `THIRD_PARTY_NOTICES.md`.
- **Legacy/potencjalnie martwe (zweryfikować grep-em przed usunięciem):** `Odometer.py` (DEPRECATED),
  `Usecases.py` (stub), `ComponentFactory.createHelloWorldComponent`/`createDatePicker`,
  `.travis.yml.notusedanymore`, zakomentowane bloki (`StringUtils` TEST-ZONE, `DatabaseManager`, JS).

## 10. Problemy architektoniczne / technical debt

1. **God-objects:** `DatabaseManager.py` (1180), `SpoolManagerAPI.py` (1009), `__init__.py` (959),
   `SpoolManager.js` (1213), `EditSpoolDialog.js` (967).
2. **Business logic w UI:** konwersje jednostek/procenty/`densityMap` w `EditSpoolDialog.js`.
3. **3× zduplikowane filtrowanie:** `TableItemHelper.js`, `FilterSorter.js`, `SpoolSelectionTableComp.js`.
4. **Ukryta globalna zależność DB:** `DatabaseManager.db` (atrybut klasowy).
5. **Circular import:** `SpoolManagerAPI.py:21` ↔ `__init__.py:21`.
6. **Mixin zależny od konkretnej klasy:** `SpoolManagerAPI` używa `self._databaseManager`,
   `self.loadSelectedSpools`, `self.commitOdometerData`… zdefiniowanych w `SpoolmanagerPlugin`.
7. **Ręczne mapowanie JSON** (~40 pól) bez walidacji/schematu (pydantic do rozważenia).
8. **Star import peewee** (`from peewee import *`).
9. **Python 2 legacy:** `past`, `from __future__`, `__plugin_pythoncompat__=">=2.7,<4"`, `print` w `newodometer.py:162`.
10. **Gołe `except`/`alert`/`confirm`** — cicha utrata błędów.
11. **Zależność od wewnętrznego DOM OctoPrint:** `ResetSettingsUtilV3.js`.
12. **`moment` bez deklaracji** w `get_assets` (opiera się na rdzeniu OctoPrint).

## 11. Ryzyka migracji

| Obszar | Ryzyko | Dlaczego | Co może się zepsuć | Priorytet |
|---|---|---|---|---|
| Istniejące instalacje | Wysokie | upgrade nadpisuje kod, nie dane | rozjazd schematu, utrata ustawień | P1 |
| Baza danych | Wysokie | migracje SQLite nieodwracalne, brak testów | utrata szpul | P1 |
| API (kontrakt) | Wysokie | FE + MQTT zależą od JSON/eventów | zepsuty FE | P1 |
| OctoPrint API | Średnie | wersje OctoPrint, `past`, `moment`, socket | niespójność wersji | P1 |
| JS→TS | Średnie | typy przy braku testów | regresje | P2 |
| Knockout→Vue | Wysokie | pełna wymiana UI + build | utrata zachowania | P2 |
| DOM/jQuery | Średnie | widgety i hacki DOM | zepsute pickery/Quill/reset | P2 |
| Packaging/build | Średnie | dodanie Vite | zły artefakt release | P2 |
| Third-party | Niskie | nie ruszać | — | P3 |
| Kompatybilność wsteczna | Wysokie | suma powyższych | — | P1 |

## 12. Migracja JS → TypeScript (ocena)

| Moduł | Trudność | Ryzyko | Uwagi |
|---|---|---|---|
| `SpoolManager-APIClient.js` | EASY | Niskie | czysty 1:1, kandydat na `fetch`/typowany klient |
| `SpoolManager-DatabaseConnectionProblemDialog.js` | EASY | Niskie | |
| `SpoolManager-ImportDialog.js` | EASY | Niskie | |
| `TableItemHelper.js` | MEDIUM | Średnie | stan + logika filtrów |
| `SpoolManager-FilterSorter.js` | MEDIUM | Średnie | zduplikowana logika filtrowania |
| `SpoolManager-SpoolSelectionTableComp.js` | MEDIUM/HARD | Wyższe | KO component + duplikacja logiki |
| `ComponentFactory.js` | HARD | Wysokie | sprzężenie z pluginami jQuery |
| `SpoolManager.js` | VERY HARD | Bardzo wysokie | god-object + integracja OctoPrint |
| `SpoolManager-EditSpoolDialog.js` | VERY HARD | Bardzo wysokie | business logic + UI + cykliczne subskrypcje |
| `ResetSettingsUtilV3.js` | VERY HARD | Bardzo wysokie | wewnętrzne API jQuery + DOM OctoPrint |
| 3rd-party (quill, tinycolor, pick-a-color, select2, datetimepicker) | THIRD-PARTY | — | nie migrować |

**Miejsca, gdzie TS ujawni problemy:** globalne `BASEURL`/`UI_API_KEY`/`PLUGIN_ID`, niejawne typy
`parameters[]`, cykliczne subskrypcje (`amIRootChange`), duplikacja filtrowania, `moment` bez deklaracji.

## 13. Migracja do Vue (ocena)

**Naturalne komponenty:** `SpoolTable` (tabela+paginacja), `SpoolEditDialog`, `SpoolSelectDialog`,
`SpoolSidebar`, `SpoolFilters` (współdzielony — dziś zduplikowany), `DatabaseSettings`,
`SpoolImportStatusDialog`, `DatabaseConnectionProblemDialog`.

**Stan:** dziś w root VM → Pinia store (spools, selection, catalogs, settings).

**Silne sprzężenie z DOM/OctoPrint:** `ComponentFactory`, `ResetSettingsUtilV3`, `_reColorFilamentIcon`,
`$("#spm-select-spool-table").html()`, parametry VM/socket.

**Co oddzielić od frameworka:** konwersje jednostek/procenty, budowanie query filtrów, `densityMap` —
czysta logika testowalna bez DOM.

**Wniosek:** Vue pasuje do większości UI. **Nie** do: `ResetSettingsUtilV3` (hack DOM OctoPrint) i
integracji socket/VM (zostaje jako cienki adapter).

## 14. Roadmap (rekomendowana kolejność)

1. Poznanie i dokumentacja (ten dokument, mapa API/schematu).
2. Zabezpieczenie krytycznej funkcjonalności testami (rozdział 8).
3. Toolchain: `ruff`/`mypy`/`pytest`, ESLint/Prettier/`tsc`+Vite, CI.
4. Python → 3.11+ (drop 2.7): `past`, `from __future__`, `__plugin_pythoncompat__`, typy, docstringi.
5. Wydzielenie logiki niezależnej od UI (czyste moduły TS: konwersje, procenty, query filtrów).
6. Migracja JS→TS bez zmiany zachowania (EASY→MEDIUM najpierw, root VM na końcu). **Nie mieszać z Vue.**
7. Migracja wybranych części do Vue (tabela, dialogi, filtry; adapter OctoPrint poza Vue).
8. Dalsza modernizacja architektury (rozbicie god-objectów, pydantic, repozytoria).

## 15. Kontrakt zachowania

- Nie zmieniaj zachowania bez powodu; każda zmiana zachowania = test.
- Nie usuwaj funkcji tylko dlatego, że wyglądają staro.
- Nie zmieniaj API bez sprawdzenia klientów.
- Nie zmieniaj schematu bazy bez planu migracji.
- Nie mieszaj JS→TS z redesignem UI ani z migracją do Vue.
- Nie modernizuj third-party.
- Nie rób dużych refaktorów bez testów regresyjnych.

> Pełne zasady pracy dla agentów: `AGENTS.md`.
