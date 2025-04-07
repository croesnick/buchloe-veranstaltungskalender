# Buchloe Veranstaltungskalender

Buchloe Veranstaltungskalender als iCal Export.

## Funktionen

- Automatisches Scraping von Veranstaltungsdaten aus dem [Buchloer Veranstaltungskalender](https://www.buchloe.de/freizeit-tourismus/veranstaltungen/)
- Export der Veranstaltungen als Kalender-Import im iCal-Format

## Installation

1. Python 3.12+ installieren
2. Projekt klonen:

   ```shell
   git clone https://github.com/croesnick/buchloe-veranstaltungskalender.git
   cd buchloe-veranstaltungskalender
   ```

3. Abhängigkeiten installieren:

   ```shell
   uv sync
   ```

## Verwendung

### Scraping ausführen

```bash
uv run python -m buchloe_veranstaltungskalender.scraper
```

### Veranstaltungen vergleichen

```python
from buchloe_veranstaltungskalender.compare import compare_events

# Beispielaufruf
results = compare_events(source_a, source_b)
```

## Entwicklung

### Setup

1. Umgebung erstellen:

   ```bash
   uv sync
   ```

### Tests

```bash
uv run pytest
```

### Coding Style

- Typ-Annotationen für alle Funktionen und Variablen
- Pydantic-Modelle für Datenstrukturen

## Lizenz

MIT
