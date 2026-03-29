#!/bin/bash
# Café Datenbank – Neuen Eintrag hinzufügen
# Doppelklick oder: bash NEUER_EINTRAG.sh

cd "$(dirname "$0")"
python3 eintragen.py
echo ""
read -rp "  Drücke Enter zum Schließen..."
