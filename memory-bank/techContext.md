# Technischer Kontext

## Kern-Technologien

### Programmiersprache
- Python 3.12 (siehe .python-version)
- Strikte Typisierung mit Typehints
- Moderne Python-Features (Pattern Matching, Generatoren)

### Hauptbibliotheken
- **BeautifulSoup4**: Web Scraping
- **icalendar**: iCal-Generierung
- **Pydantic**: Datenvalidierung
- **pytest**: Unit-Tests
- **requests**: HTTP-Requests

## Entwicklungsumgebung

### Paketmanagement
- **uv**: Schneller Paketmanager (uv.lock)
- **pyproject.toml**: PEP 621-konforme Konfiguration

### Build-System
- Statische Typüberprüfung mit mypy

### Skripte
- scrape.sh: Automatisiertes Scraping
- main.py: Hauptentrypoint

## Code-Qualität

### Linting
- ruff für Code-Formatierung
- mypy für Code-Analyse

### Testing
- Unit-Tests mit pytest
- Testabdeckung via coverage.py
- Integrationstests für Scraping-Logik

## Infrastruktur

### Datenhaltung
- JSON-Dateien unter data/
- Versionierung der Rohdaten
- iCal-Dateien für Abonnements

### Logging
- Strukturierte Logs im JSON-Format
- Sentry-Integration für Produktion

## CI/CD
- GitHub Actions für:
  - Automatisiertes Testing
  - Code-Qualitätschecks
  - Export der *.ical Daten in den Branch `gh-pages`
