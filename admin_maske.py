#!/usr/bin/env python3
"""
Café Firmen-Datenbank – Admin-Maske (GUI)
Nutzung: python3 admin_maske.py
"""

import json
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

DATEN_DATEI = Path(__file__).parent / "daten.json"
REPO_DIR = Path(__file__).parent


def lade_daten() -> dict:
    if DATEN_DATEI.exists():
        with open(DATEN_DATEI, "r", encoding="utf-8") as f:
            daten = json.load(f)
            if isinstance(daten, list):
                return {"partner": daten, "wartung": []}
            return daten
    return {"partner": [], "wartung": []}


def speichere_daten(daten: dict) -> None:
    with open(DATEN_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)


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
        self._zeige_letzten_push()
        self._aktualisiere_partner_liste()
        self._aktualisiere_wartung_liste()

    def _baue_ui(self):
        # ── Tabs ──
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=12, pady=(12, 6))

        self.tab_partner = tk.Frame(notebook)
        notebook.add(self.tab_partner, text="  Partner  ")

        self.tab_wartung = tk.Frame(notebook)
        notebook.add(self.tab_wartung, text="  Wartung  ")

        self._baue_partner_tab()
        self._baue_wartung_tab()

        # ── Zuletzt aktualisiert ──
        self.label_letzter_push = tk.Label(
            self.root,
            text="Zuletzt aktualisiert: …",
            font=("Helvetica", 11),
            fg="#8e8e93",
        )
        self.label_letzter_push.pack(padx=12, pady=(4, 0))

        # ── Veröffentlichen ──
        tk.Button(
            self.root,
            text="☁  Änderungen veröffentlichen",
            command=self._veroeffentlichen,
            bg="#007aff",
            fg="white",
            font=("Helvetica", 14, "bold"),
            relief="flat",
            padx=10,
            pady=14,
        ).pack(fill="x", padx=12, pady=(4, 12))

    def _baue_partner_tab(self):
        self.partner_bearbeitungs_index = None

        # ── Eingabebereich ──
        self.partner_frame_eingabe = tk.LabelFrame(
            self.tab_partner, text="Neuer Eintrag", padx=10, pady=10
        )
        self.partner_frame_eingabe.pack(fill="x", padx=12, pady=(12, 6))

        labels = [("Was:", "was"), ("Wo / Info:", "wo"), ("Wer:", "wer")]
        self.partner_felder: dict[str, tk.Entry] = {}

        for i, (label_text, key) in enumerate(labels):
            tk.Label(self.partner_frame_eingabe, text=label_text, anchor="w", width=10).grid(
                row=i, column=0, sticky="w", pady=3
            )
            entry = tk.Entry(self.partner_frame_eingabe, width=40, font=("Helvetica", 13))
            entry.grid(row=i, column=1, sticky="ew", pady=3)
            self.partner_felder[key] = entry

        self.partner_frame_eingabe.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self.partner_frame_eingabe)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.partner_btn_aktion = tk.Button(
            btn_frame,
            text="Hinzufügen",
            command=self._partner_speichern,
            bg="#34c759",
            fg="white",
            font=("Helvetica", 13, "bold"),
            relief="flat",
            padx=10,
            pady=6,
        )
        self.partner_btn_aktion.pack(side="left", fill="x", expand=True)

        self.partner_btn_abbrechen = tk.Button(
            btn_frame,
            text="Abbrechen",
            command=self._partner_abbrechen,
            bg="#8e8e93",
            fg="white",
            font=("Helvetica", 13, "bold"),
            relief="flat",
            padx=10,
            pady=6,
        )
        # Wird erst bei Bearbeitung eingeblendet

        # ── Listen-Bereich ──
        frame_liste = tk.LabelFrame(self.tab_partner, text="Alle Einträge", padx=10, pady=10)
        frame_liste.pack(fill="both", expand=True, padx=12, pady=6)

        scrollbar = tk.Scrollbar(frame_liste, orient="vertical")
        self.partner_listbox = tk.Listbox(
            frame_liste,
            yscrollcommand=scrollbar.set,
            font=("Helvetica", 13),
            selectbackground="#007aff",
            selectforeground="white",
            activestyle="none",
            height=10,
        )
        scrollbar.config(command=self.partner_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.partner_listbox.pack(fill="both", expand=True)
        self.partner_listbox.bind("<Double-Button-1>", self._partner_bearbeiten_laden)

        tk.Button(
            frame_liste,
            text="Ausgewählten Eintrag löschen",
            command=self._partner_loeschen,
            bg="#ff3b30",
            fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat",
            padx=10,
            pady=6,
        ).pack(fill="x", pady=(8, 0))

    def _baue_wartung_tab(self):
        self.wartung_bearbeitungs_index = None

        # ── Eingabebereich ──
        self.wartung_frame_eingabe = tk.LabelFrame(
            self.tab_wartung, text="Neue Wartung", padx=10, pady=10
        )
        self.wartung_frame_eingabe.pack(fill="x", padx=12, pady=(12, 6))

        labels = [("Datum:", "datum"), ("Objekt:", "objekt"), ("Maßnahme:", "massnahme")]
        self.wartung_felder: dict[str, tk.Entry] = {}

        for i, (label_text, key) in enumerate(labels):
            tk.Label(self.wartung_frame_eingabe, text=label_text, anchor="w", width=10).grid(
                row=i, column=0, sticky="w", pady=3
            )
            entry = tk.Entry(self.wartung_frame_eingabe, width=40, font=("Helvetica", 13))
            entry.grid(row=i, column=1, sticky="ew", pady=3)
            self.wartung_felder[key] = entry

        self.wartung_frame_eingabe.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self.wartung_frame_eingabe)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.wartung_btn_aktion = tk.Button(
            btn_frame,
            text="Hinzufügen",
            command=self._wartung_speichern,
            bg="#34c759",
            fg="white",
            font=("Helvetica", 13, "bold"),
            relief="flat",
            padx=10,
            pady=6,
        )
        self.wartung_btn_aktion.pack(side="left", fill="x", expand=True)

        self.wartung_btn_abbrechen = tk.Button(
            btn_frame,
            text="Abbrechen",
            command=self._wartung_abbrechen,
            bg="#8e8e93",
            fg="white",
            font=("Helvetica", 13, "bold"),
            relief="flat",
            padx=10,
            pady=6,
        )
        # Wird erst bei Bearbeitung eingeblendet

        # ── Listen-Bereich ──
        frame_liste = tk.LabelFrame(self.tab_wartung, text="Alle Wartungen", padx=10, pady=10)
        frame_liste.pack(fill="both", expand=True, padx=12, pady=6)

        scrollbar = tk.Scrollbar(frame_liste, orient="vertical")
        self.wartung_listbox = tk.Listbox(
            frame_liste,
            yscrollcommand=scrollbar.set,
            font=("Helvetica", 13),
            selectbackground="#007aff",
            selectforeground="white",
            activestyle="none",
            height=10,
        )
        scrollbar.config(command=self.wartung_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.wartung_listbox.pack(fill="both", expand=True)
        self.wartung_listbox.bind("<Double-Button-1>", self._wartung_bearbeiten_laden)

        tk.Button(
            frame_liste,
            text="Ausgewählten Eintrag löschen",
            command=self._wartung_loeschen,
            bg="#ff3b30",
            fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat",
            padx=10,
            pady=6,
        ).pack(fill="x", pady=(8, 0))

    # ── Listen aktualisieren ──

    def _aktualisiere_partner_liste(self):
        daten = lade_daten()
        self.partner_eintraege = daten.get("partner", [])
        self.partner_listbox.delete(0, tk.END)
        for e in self.partner_eintraege:
            self.partner_listbox.insert(tk.END, f"  {e['was']}  –  {e['wer']}")

    def _aktualisiere_wartung_liste(self):
        daten = lade_daten()
        self.wartung_eintraege = daten.get("wartung", [])
        self.wartung_listbox.delete(0, tk.END)
        for e in self.wartung_eintraege:
            self.wartung_listbox.insert(
                tk.END, f"  {e['datum']}  –  {e['objekt']}  –  {e['massnahme']}"
            )

    # ── Git ──

    def _git_pull_beim_start(self):
        ok, ausgabe = git_befehl(["git", "pull"])
        if not ok:
            messagebox.showwarning(
                "Git Pull fehlgeschlagen",
                f"Konnte nicht aktualisieren:\n\n{ausgabe}",
            )

    def _zeige_letzten_push(self):
        ok, ausgabe = git_befehl(
            ["git", "log", "-1", "--format=%cd", "--date=format:%d.%m.%Y %H:%M"]
        )
        text = ausgabe if (ok and ausgabe) else "–"
        self.label_letzter_push.configure(text=f"Zuletzt aktualisiert: {text}")

    # ── Partner: Bearbeiten ──

    def _partner_bearbeiten_laden(self, event=None):
        auswahl = self.partner_listbox.curselection()
        if not auswahl:
            return
        self.partner_bearbeitungs_index = auswahl[0]
        e = self.partner_eintraege[self.partner_bearbeitungs_index]
        for key, entry in self.partner_felder.items():
            entry.delete(0, tk.END)
            entry.insert(0, e[key])
        self.partner_frame_eingabe.configure(text="Eintrag bearbeiten")
        self.partner_btn_aktion.configure(text="Speichern", bg="#ff9500")
        self.partner_btn_abbrechen.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _partner_speichern(self):
        was = self.partner_felder["was"].get().strip()
        wo  = self.partner_felder["wo"].get().strip()
        wer = self.partner_felder["wer"].get().strip()

        if not was or not wo:
            messagebox.showwarning("Fehlende Eingabe", "Bitte Was und Wo ausfüllen.")
            return

        daten = lade_daten()
        if self.partner_bearbeitungs_index is not None:
            daten["partner"][self.partner_bearbeitungs_index] = {"was": was, "wo": wo, "wer": wer}
        else:
            daten["partner"].append({"was": was, "wo": wo, "wer": wer})
        speichere_daten(daten)

        self._partner_abbrechen()
        self._aktualisiere_partner_liste()

    def _partner_abbrechen(self):
        self.partner_bearbeitungs_index = None
        for entry in self.partner_felder.values():
            entry.delete(0, tk.END)
        self.partner_frame_eingabe.configure(text="Neuer Eintrag")
        self.partner_btn_aktion.configure(text="Hinzufügen", bg="#34c759")
        self.partner_btn_abbrechen.pack_forget()

    def _partner_loeschen(self):
        auswahl = self.partner_listbox.curselection()
        if not auswahl:
            messagebox.showwarning("Kein Eintrag gewählt", "Bitte zuerst einen Eintrag in der Liste markieren.")
            return

        index = auswahl[0]
        name = self.partner_eintraege[index]["was"]

        bestaetigt = messagebox.askyesno("Eintrag löschen", f'"{name}" wirklich löschen?')
        if not bestaetigt:
            return

        daten = lade_daten()
        del daten["partner"][index]
        speichere_daten(daten)
        self._partner_abbrechen()
        self._aktualisiere_partner_liste()

    # ── Wartung: Bearbeiten ──

    def _wartung_bearbeiten_laden(self, event=None):
        auswahl = self.wartung_listbox.curselection()
        if not auswahl:
            return
        self.wartung_bearbeitungs_index = auswahl[0]
        e = self.wartung_eintraege[self.wartung_bearbeitungs_index]
        for key, entry in self.wartung_felder.items():
            entry.delete(0, tk.END)
            entry.insert(0, e[key])
        self.wartung_frame_eingabe.configure(text="Wartung bearbeiten")
        self.wartung_btn_aktion.configure(text="Speichern", bg="#ff9500")
        self.wartung_btn_abbrechen.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _wartung_speichern(self):
        datum     = self.wartung_felder["datum"].get().strip()
        objekt    = self.wartung_felder["objekt"].get().strip()
        massnahme = self.wartung_felder["massnahme"].get().strip()

        if not datum or not objekt or not massnahme:
            messagebox.showwarning("Fehlende Eingabe", "Bitte alle drei Felder ausfüllen.")
            return

        daten = lade_daten()
        if self.wartung_bearbeitungs_index is not None:
            daten["wartung"][self.wartung_bearbeitungs_index] = {
                "datum": datum, "objekt": objekt, "massnahme": massnahme
            }
        else:
            daten["wartung"].append({"datum": datum, "objekt": objekt, "massnahme": massnahme})
        speichere_daten(daten)

        self._wartung_abbrechen()
        self._aktualisiere_wartung_liste()

    def _wartung_abbrechen(self):
        self.wartung_bearbeitungs_index = None
        for entry in self.wartung_felder.values():
            entry.delete(0, tk.END)
        self.wartung_frame_eingabe.configure(text="Neue Wartung")
        self.wartung_btn_aktion.configure(text="Hinzufügen", bg="#34c759")
        self.wartung_btn_abbrechen.pack_forget()

    def _wartung_loeschen(self):
        auswahl = self.wartung_listbox.curselection()
        if not auswahl:
            messagebox.showwarning("Kein Eintrag gewählt", "Bitte zuerst einen Eintrag in der Liste markieren.")
            return

        index = auswahl[0]
        e = self.wartung_eintraege[index]
        name = f"{e['datum']} – {e['objekt']}"

        bestaetigt = messagebox.askyesno("Eintrag löschen", f'"{name}" wirklich löschen?')
        if not bestaetigt:
            return

        daten = lade_daten()
        del daten["wartung"][index]
        speichere_daten(daten)
        self._wartung_abbrechen()
        self._aktualisiere_wartung_liste()

    # ── Veröffentlichen ──

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

        self._zeige_letzten_push()
        messagebox.showinfo("Fertig!", "Änderungen erfolgreich veröffentlicht.")


if __name__ == "__main__":
    root = tk.Tk()
    AdminMaske(root)
    root.mainloop()
