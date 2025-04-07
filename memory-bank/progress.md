# Fortschrittsdokumentation

## Aktueller Stand (v0.1.0)

### Implementiert
- **Scraping**
  - Basis-Implementierung für Veranstaltungskalender der Stadt Buchloe
  - Event-Datenerfassung in JSON
  - Automatisiertes Scraping in Python

- **iCal-Generierung**
  - Grundlegende Kalendererstellung
  - Wiederkehrende Events Unterstützung
  - UTF-8 Kodierung

- **Datenverarbeitung**
  - Vergleichsalgorithmus für Änderungen
  - Delta-Erkennung zwischen Scrapes

### In Arbeit
- **Testabdeckung**
  - Unit-Tests für Vergleichslogik
  - Integrationstests für Scraping

- **Dokumentation**
  - Memory-Bank Aufbau
  - API-Dokumentation

### Bekannte Probleme
- Zeitumrechnung bei Sommer/Winterzeit
- Fehlende Retry-Logik bei HTTP-Fehlern

## Roadmap

### Nächste Schritte
1. Reine Python-Implementierung des Scrapings
2. Generierung des *.iCal Exports
3. GitHub Actions CI/CD Pipeline

## Versionierung

### v0.1.0 (2025-04-07)
- Initiale Implementierung
- Grundlegende Scraping-Funktionalität
- iCal-Generierung
