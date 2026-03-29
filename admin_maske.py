#!/usr/bin/env python3
"""
Café Firmen-Datenbank – Admin-Maske (GUI)
Nutzung: python3 admin_maske.py
"""

import json
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

DATEN_DATEI = Path(__file__).parent / "daten.json"
REPO_DIR = Path(__file__).parent


def lade_daten() -> list:
    if DATEN_DATEI.exists():
        with open(DATEN_DATEI, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def speichere_daten(eintraege: list) -> None:
    with open(DATEN_DATEI, "w", encoding="utf-8") as f:
        json.dump(eintraege, f, ensure_ascii=False, indent=2)


def git_befehl(args: list) -> tuple[bool, str]:
    result = subprocess.run(
        args, cwd=REPO_DIR, capture_output=True, text=True
    )
    ausgabe = result.stdout.strip() or result.stderr.strip()
    return result.returncode == 0, ausgabe


class AdminMaske:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Café Datenbank – Admin")
        self.root.resizable(False, False)

        self._baue_ui()
        self._git_pull_beim_start()
        self._aktualisiere_liste()

    def _baue_ui(self):
        pad = {"padx": 10, "pady": 5}

        # ── Eingabebereich ──
        frame_eingabe = tk.LabelFrame(self.root, text="Neuer Eintrag", padx=10, pady=10)
        frame_eingabe.pack(fill="x", padx=12, pady=(12, 6))

        labels = [("Was:", "was"), ("Wo / Info:", "wo"), ("Wer:", "wer")]
        self.felder: dict[str, tk.Entry] = {}

        for i, (label_text, key) in enumerate(labels):
            tk.Label(frame_eingabe, text=label_text, anchor="w", width=10).grid(
                row=i, column=0, sticky="w", pady=3
            )
            entry = tk.Entry(frame_eingabe, width=40, font=("Helvetica", 13))
            entry.grid(row=i, column=1, sticky="ew", pady=3)
            self.felder[key] = entry

        frame_eingabe.columnconfigure(1, weight=1)

        tk.Button(
            frame_eingabe,
            text="Hinzufügen",
            command=self._hinzufuegen,
            bg="#34c759",
            fg="white",
            font=("Helvetica", 13, "bold"),
            relief="flat",
            padx=10,
            pady=6,
        ).grid(row=len(labels), column=0, columnspan=2, sticky="ew", pady=(10, 0))

        # ── Listen-Bereich ──
        frame_liste = tk.LabelFrame(self.root, text="Alle Einträge", padx=10, pady=10)
        frame_liste.pack(fill="both", expand=True, padx=12, pady=6)

        scrollbar = tk.Scrollbar(frame_liste, orient="vertical")
        self.listbox = tk.Listbox(
            frame_liste,
            yscrollcommand=scrollbar.set,
            font=("Helvetica", 13),
            selectbackground="#007aff",
            selectforeground="white",
            activestyle="none",
            height=10,
        )
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(fill="both", expand=True)

        tk.Button(
            frame_liste,
            text="Ausgewählten Eintrag löschen",
            command=self._loeschen,
            bg="#ff3b30",
            fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat",
            padx=10,
            pady=6,
        ).pack(fill="x", pady=(8, 0))

        # ── Veröffentlichen ──
        tk.Button(
            self.root,
            text="☁  Änderungen auf iPhone veröffentlichen",
            command=self._veroeffentlichen,
            bg="#007aff",
            fg="white",
            font=("Helvetica", 14, "bold"),
            relief="flat",
            padx=10,
            pady=14,
        ).pack(fill="x", padx=12, pady=(6, 12))

    def _aktualisiere_liste(self):
        self.eintraege = lade_daten()
        self.listbox.delete(0, tk.END)
        for e in self.eintraege:
            self.listbox.insert(tk.END, f"  {e['was']}  –  {e['wer']}")

    def _git_pull_beim_start(self):
        ok, ausgabe = git_befehl(["git", "pull"])
        if not ok:
            messagebox.showwarning(
                "Git Pull fehlgeschlagen",
                f"Konnte nicht aktualisieren:\n\n{ausgabe}",
            )

    def _hinzufuegen(self):
        was = self.felder["was"].get().strip()
        wo  = self.felder["wo"].get().strip()
        wer = self.felder["wer"].get().strip()

        if not was or not wo:
            messagebox.showwarning("Fehlende Eingabe", "Bitte Was und Wo ausfüllen.")
            return

        self.eintraege.append({"was": was, "wo": wo, "wer": wer})
        speichere_daten(self.eintraege)

        for entry in self.felder.values():
            entry.delete(0, tk.END)

        self._aktualisiere_liste()

    def _loeschen(self):
        auswahl = self.listbox.curselection()
        if not auswahl:
            messagebox.showwarning("Kein Eintrag gewählt", "Bitte zuerst einen Eintrag in der Liste markieren.")
            return

        index = auswahl[0]
        name = self.eintraege[index]["was"]

        bestaetigt = messagebox.askyesno(
            "Eintrag löschen",
            f'"{name}" wirklich löschen?',
        )
        if not bestaetigt:
            return

        del self.eintraege[index]
        speichere_daten(self.eintraege)
        self._aktualisiere_liste()

    def _veroeffentlichen(self):
        schritte = [
            (["git", "add", "."],                                   "git add"),
            (["git", "commit", "-m", "Update via Admin-Maske"],     "git commit"),
            (["git", "push"],                                        "git push"),
        ]
        for cmd, name in schritte:
            ok, ausgabe = git_befehl(cmd)
            if not ok and name != "git commit":
                messagebox.showerror(
                    "Fehler beim Hochladen",
                    f"Fehler bei '{name}':\n\n{ausgabe}",
                )
                return

        messagebox.showinfo(
            "Fertig!",
            "Änderungen erfolgreich veröffentlicht.\nDas iPhone sieht die Daten sofort.",
        )


if __name__ == "__main__":
    root = tk.Tk()
    AdminMaske(root)
    root.mainloop()
