#!/usr/bin/env python3
"""
Café Firmen-Datenbank – Eintrag-Tool
Nutzung: python3 eintragen.py
"""

import json
import subprocess
import sys
from pathlib import Path

DATEN_DATEI = Path(__file__).parent / "daten.json"


def lade_daten() -> list:
    if DATEN_DATEI.exists():
        with open(DATEN_DATEI, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def speichere_daten(eintraege: list) -> None:
    with open(DATEN_DATEI, "w", encoding="utf-8") as f:
        json.dump(eintraege, f, ensure_ascii=False, indent=2)


def frage(prompt: str) -> str:
    antwort = input(prompt).strip()
    if not antwort:
        print("  ⚠️  Eingabe darf nicht leer sein.")
        return frage(prompt)
    return antwort


def git_push() -> bool:
    """Führt git add, commit und push aus. Gibt True bei Erfolg zurück."""
    schritte = [
        (["git", "add", "."],                        "git add"),
        (["git", "commit", "-m", "Update Datenbank"], "git commit"),
        (["git", "push"],                             "git push"),
    ]
    for cmd, name in schritte:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"\n  ❌ Fehler bei '{name}':")
            print(f"     {result.stderr.strip() or result.stdout.strip()}")
            return False
        print(f"  ✅ {name} erfolgreich")
    return True


def main():
    print("\n╔══════════════════════════════════╗")
    print("║   Café Firmen-Datenbank – Neu    ║")
    print("╚══════════════════════════════════╝\n")

    was = frage("  Was?         (Firmenname / Tätigkeit): ")
    wo  = frage("  Wo / Info?   (Link oder Adresse):      ")
    wer = frage("  Wer?         (Ansprechpartner):         ")

    neuer_eintrag = {"was": was, "wo": wo, "wer": wer}

    eintraege = lade_daten()
    eintraege.append(neuer_eintrag)
    speichere_daten(eintraege)

    print(f"\n  💾 Gespeichert: \"{was}\" ({len(eintraege)} Einträge gesamt)\n")

    print("  📤 Lade hoch zu GitHub ...\n")
    erfolg = git_push()

    if erfolg:
        print("\n  🎉 Fertig! Deine Eltern sehen den neuen Eintrag sofort.\n")
    else:
        print("\n  ⚠️  Eintrag lokal gespeichert, aber Upload fehlgeschlagen.")
        print("     Bitte manuell pushen oder NEUER_EINTRAG.sh erneut starten.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
