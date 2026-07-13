# SpikePrime – Reversi-Roboter

Studienarbeit **T3200** – 6. Semester Elektrotechnik, DHBW Friedrichshafen.
Aufbauend auf der vorangegangenen Projektarbeit aus dem 5. Semester realisiert dieses
Repository die Software eines Roboters auf Basis des **LEGO® Education SPIKE Prime**,
der das Spiel **Reversi (Othello)** vollständig autonom gegen einen menschlichen Gegner
auf einem Tablet spielt.

Der Roboter erfasst dazu den Spielfeldzustand mit einem Farbsensor, berechnet den
optimalen Zug per **Minimax-Algorithmus mit Alpha-Beta-Pruning** und führt den Zug über
einen an einer XYZ-Kinematik befestigten **Eingabestift** auf dem Touchscreen aus.

---

## Repository-Struktur

```
SpikePrime/
├── Reversi_main.py   # Hauptprogramm für den SPIKE Prime Hub (Pybricks/MicroPython)
├── test.py           # Debug-Variante mit PC-Simulation (ohne Hardware lauffähig)
└── axis_test.py      # Kalibrier-Hilfsprogramm für den Farbsensor
```

### `Reversi_main.py`

Produktivcode, der direkt auf dem SPIKE-Prime-Hub ausgeführt wird. Das Programm ist in
folgende logische Blöcke gegliedert:

| Bereich | Funktionen (Auswahl) | Aufgabe |
|---|---|---|
| Motorsteuerung | `default_position`, `X2_relative`, `Y2_relative`, `move_sensor_to`, `Z2_tap` | Ansteuerung der XYZ-Achsen und des Stift-Aktuators |
| Boarderfassung | `field_scan`, `center_on_field`, `calibrate_colors` | Zeilenweises Abscannen des 8×8-Spielfeldes über den Farbsensor |
| Spiellogik | `get_valid_moves`, `get_flippable_tokens`, `apply_move`, `evaluate_board` | Regelwerk und Bewertungsfunktion für Reversi |
| KI | `minimax`, `get_best_move` | Zugauswahl per Minimax mit Alpha-Beta-Pruning |
| Zug-Ausführung | `move_to_position`, `indices_to_position` | Übersetzung der Zugkoordinaten in Motorbewegungen und Stift-Tap |
| Rundenerkennung | `goto_turn_indicator`, `is_indicator_red`, `wait_for_robot_turn` | Auswertung der Zug-Anzeige der Tablet-App |
| Kalibrierung | `calibration`, `calibrate_indicator`, `validate_start_position` | Nullpunkt- und Farbkalibrierung vor Spielbeginn |
| Einstieg | `main`, `select_robot_color` | Ablaufsteuerung und Auswahl der eigenen Farbe |

### `test.py`

Enthält denselben Programmablauf wie `Reversi_main.py`, ist aber um eine
**Auto-Detect-Schicht** ergänzt: Fehlen die `pybricks`-Module (z. B. bei Ausführung auf
einem PC), werden Sensorik und Motorik durch Mock-Objekte und ein simuliertes
Spielbrett ersetzt. So lässt sich die Spiellogik ohne Hardware testen und debuggen.

### `axis_test.py`

Kleines Hilfsprogramm zum Auslesen von HSV- und Umgebungslicht-Werten des Farbsensors.
Über die Hub-Buttons können Messungen ausgelöst und die Sensor-LED-Helligkeit
umgeschaltet werden. Dient zur **Ermittlung der Schwellwerte** für die Farberkennung
der Spielsteine.

---

## Hardware-Belegung (SPIKE Prime Hub)

| Port | Komponente | Funktion |
|---|---|---|
| A | Motor X1 | Antrieb der X-Hauptachse (Portal) |
| C | Motor X2 | Feinpositionierung X |
| F | Motor Y2 | Positionierung Y |
| B | Motor Z2 | Stift-Hub-Achse (Tap) |
| D | Color Sensor | Erfassung der Spielfeldfarben |

Die Motorwinkel für Feldabstände (`move_distance_x`, `move_distance_y`) sowie die
Offsets zwischen Farbsensor und Eingabestift (`pen_offset_x`, `pen_offset_y`) sind zu
Beginn der `Reversi_main.py` als Konstanten definiert und im Rahmen der Kalibrierung
anzupassen.

---

## Ausführung auf dem SPIKE Prime

1. Pybricks-Firmware auf dem SPIKE-Prime-Hub installieren (siehe Ausarbeitung, Kap. 3).
2. `Reversi_main.py` über die Pybricks-Weboberfläche auf den Hub übertragen.
3. Roboter in Grundposition bringen und `main()` starten.
4. Über die Hub-Buttons eigene Farbe (Schwarz/Weiß) auswählen.
5. Anschließend läuft die Partie autonom bis zum Spielende.

## Ausführung im PC-Debugmodus

```bash
python3 test.py
```

Ohne installierte `pybricks`-Module wird automatisch der Simulationsmodus aktiviert.

---

## Entwicklungsumgebung

- **Sprache:** MicroPython (Pybricks-Dialekt)
- **Runtime:** Pybricks-Firmware auf LEGO SPIKE Prime Hub
- **Toolchain:** Pybricks Code (Web-IDE) bzw. beliebiger Editor + Pybricks-CLI

---
