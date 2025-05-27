# Buchloe Veranstaltungskalender

Buchloe Veranstaltungskalender als iCal Export.

## Funktionen

- Automatisches Scraping von Veranstaltungsdaten aus dem [Buchloer Veranstaltungskalender](https://www.buchloe.de/freizeit-tourismus/veranstaltungen/)
- Export der Veranstaltungen als Kalender-Import im iCal-Format
- Automatische Bereitstellung über GitHub Pages mit 6-stündlichen Updates
- Professionelle Webseite für einfaches Kalender-Abonnement

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

## GitHub Pages Bereitstellung

Der Buchloe Veranstaltungskalender wird automatisch über GitHub Pages bereitgestellt und alle 6 Stunden aktualisiert.

### 🌐 Zugriff auf den Kalender

**Webseite:** `https://croesnick.github.io/buchloe-veranstaltungskalender/`
**Kalender-URL:** `https://croesnick.github.io/buchloe-veranstaltungskalender/events.ics`

### 📅 Kalender abonnieren

#### Google Calendar

1. Öffnen Sie Google Calendar
2. Klicken Sie auf "Andere Kalender hinzufügen" (+ Symbol)
3. Wählen Sie "Über URL"
4. Fügen Sie die Kalender-URL ein: `https://croesnick.github.io/buchloe-veranstaltungskalender/events.ics`

#### Apple Calendar (macOS/iOS)

1. Öffnen Sie die Kalender-App
2. Gehen Sie zu "Datei" → "Neues Kalender-Abonnement"
3. Fügen Sie die Kalender-URL ein
4. Bestätigen Sie das Abonnement

#### Microsoft Outlook

1. Öffnen Sie Outlook
2. Gehen Sie zu "Kalender hinzufügen" → "Aus dem Internet"
3. Fügen Sie die Kalender-URL ein
4. Folgen Sie den Anweisungen zum Abonnieren

### ⏰ Automatische Updates

- **Aktualisierungsintervall:** Alle 6 Stunden (00:00, 06:00, 12:00, 18:00 UTC)
- **Zeitzone:** Europe/Berlin (MEZ/MESZ)
- **Automatische Bereitstellung:** GitHub Actions Workflow

### 🔧 Manuelle Aktualisierung

Entwickler können den Workflow manuell auslösen:

1. Gehen Sie zum GitHub Repository
2. Klicken Sie auf den "Actions" Tab
3. Wählen Sie "Scrape Events and Deploy to GitHub Pages"
4. Klicken Sie auf "Run workflow"

### 📊 Workflow-Status

Der aktuelle Status der automatischen Aktualisierungen kann im GitHub Actions Tab eingesehen werden. Jeder Workflow-Lauf erstellt eine Zusammenfassung mit:

- Scraping-Ergebnissen
- Anzahl der gefundenen Veranstaltungen
- Bereitstellungsstatus
- Nächster geplanter Lauf

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
