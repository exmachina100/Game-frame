"""GameFrame — lightweight native shot editor (Python standard library).

Edits measured-runtime Pong beats without requiring a web build system.
Use Export to write a shot plan consumable by gameframe.run_shot_plan.
"""
from __future__ import annotations
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .timeline import Beat, DEMO_BEATS


class ShotEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GameFrame — Shot Director")
        self.geometry("1100x660")
        self.minsize(800, 480)
        self.configure(bg="#11151e")
        self.beats = list(DEMO_BEATS)
        self.file: Path | None = None
        self.selected = tk.IntVar(value=0)
        self.label = tk.StringVar()
        self.frames = tk.StringVar()
        self.left = tk.IntVar()
        self.right = tk.IntVar()
        self._build()
        self._refresh(0)

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#11151e")
        style.configure("TLabel", background="#11151e", foreground="#e5eaf5", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10), padding=7)
        style.configure("Treeview", background="#1a2230", fieldbackground="#1a2230",
                        foreground="#e5eaf5", rowheight=34, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#293346", foreground="#f5f7ff")
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=22, pady=18)
        tk.Label(toolbar, text="GAMEFRAME  /  DIRECTOR", fg="#a8e8dc", bg="#11151e",
                 font=("Segoe UI Semibold", 17)).pack(side="left")
        for title, command in [("Open", self.open_plan), ("Export JSON", self.export),
                               ("Add Beat", self.add), ("Remove", self.remove)]:
            ttk.Button(toolbar, text=title, command=command).pack(side="right", padx=4)
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=22, pady=8)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)
        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        self.tree = ttk.Treeview(left, columns=("frames", "paddle0", "paddle1"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="SHOT / ACTION")
        self.tree.column("#0", width=260, minwidth=150)
        for key, title, width in [("frames", "Frames", 90), ("paddle0", "Paddle 1", 100),
                                  ("paddle1", "Paddle 2", 100)]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="center", minwidth=70)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        move = ttk.Frame(left)
        move.pack(fill="x", pady=10)
        ttk.Button(move, text="Move Up", command=lambda: self.move(-1)).pack(side="left", padx=(0, 6))
        ttk.Button(move, text="Move Down", command=lambda: self.move(1)).pack(side="left")
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text="SHOT PARAMETERS", fg="#9ab0cf", bg="#11151e",
                 font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(0, 18))
        for title, variable in [("Beat / shot name", self.label), ("Minimum frames", self.frames)]:
            ttk.Label(right, text=title).pack(anchor="w", pady=(10, 3))
            ttk.Entry(right, textvariable=variable, font=("Segoe UI", 11)).pack(fill="x")
        for title, variable in [("Left paddle · 0–255", self.left),
                                ("Right paddle · 0–255", self.right)]:
            ttk.Label(right, text=title).pack(anchor="w", pady=(18, 3))
            tk.Scale(right, from_=0, to=255, resolution=1, orient="horizontal",
                     variable=variable, bg="#11151e", fg="#f1f4fb", highlightthickness=0,
                     troughcolor="#354354", activebackground="#a8e8dc").pack(fill="x")
        ttk.Button(right, text="Apply Changes", command=self.apply).pack(fill="x", pady=(25, 8))
        tk.Label(right, text="Measured real-time playback. Frame-count overshoot is expected.\n"
                 "Export creates a portable shot-plan JSON; use the runtime script to play it.",
                 fg="#8999b2", bg="#11151e", justify="left", wraplength=320,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(12, 0))
        self.status = tk.StringVar(value="Ready — editing a four-beat Pong sequence.")
        tk.Label(self, textvariable=self.status, bg="#1a2230", fg="#aab8cc", anchor="w",
                 padx=22, pady=10, font=("Segoe UI", 10)).pack(fill="x", side="bottom")

    def _refresh(self, selection: int):
        self.tree.delete(*self.tree.get_children())
        for i, beat in enumerate(self.beats):
            self.tree.insert("", "end", iid=str(i), text=f"{i + 1:02d}   {beat.label}",
                             values=(beat.frames, beat.paddle0, beat.paddle1))
        if self.beats:
            index = max(0, min(selection, len(self.beats)-1))
            self.tree.selection_set(str(index))
            self.tree.see(str(index))
            self._populate(index)

    def _populate(self, index: int):
        beat = self.beats[index]
        self.label.set(beat.label)
        self.frames.set(str(beat.frames))
        self.left.set(beat.paddle0)
        self.right.set(beat.paddle1)

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if selected:
            self._populate(int(selected[0]))

    def _index(self) -> int | None:
        chosen = self.tree.selection()
        return int(chosen[0]) if chosen else None

    def apply(self):
        i = self._index()
        if i is None:
            return
        try:
            self.beats[i] = Beat(self.label.get().strip(), int(self.frames.get()),
                                 self.left.get(), self.right.get())
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Invalid shot settings", str(exc))
            return
        self._refresh(i)
        self.status.set(f"Updated shot {i + 1}.")

    def add(self):
        i = self._index()
        insert_at = (i + 1) if i is not None else len(self.beats)
        self.beats.insert(insert_at, Beat("new action", 24, 128, 128))
        self._refresh(insert_at)

    def remove(self):
        i = self._index()
        if i is not None and len(self.beats) > 1:
            del self.beats[i]
            self._refresh(max(0, i-1))

    def move(self, direction: int):
        i = self._index()
        if i is None or not 0 <= i + direction < len(self.beats):
            return
        self.beats[i], self.beats[i+direction] = self.beats[i+direction], self.beats[i]
        self._refresh(i+direction)

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("GameFrame shots", "*.json")],
                                            initialfile="pong_shot_plan.json")
        if not path:
            return
        try:
            self.apply()
            data = {"schema": "gameframe.pong.shots.v1", "system": "pong",
                    "frame_exact": False,
                    "beats": [{"label": b.label, "frames": b.frames, "paddle0": b.paddle0,
                               "paddle1": b.paddle1} for b in self.beats]}
            Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            self.status.set(f"Exported {len(self.beats)} beats to {path}")
        except (ValueError, OSError) as exc:
            messagebox.showerror("Cannot export", str(exc))

    def open_plan(self):
        path = filedialog.askopenfilename(filetypes=[("GameFrame shots", "*.json")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if data.get("schema") != "gameframe.pong.shots.v1" or data.get("system") != "pong":
                raise ValueError("Unsupported shot plan schema")
            beats = [Beat(**entry) for entry in data["beats"]]
            if not beats:
                raise ValueError("A shot plan needs at least one beat")
        except (ValueError, KeyError, TypeError, OSError) as exc:
            messagebox.showerror("Cannot open shot plan", str(exc))
            return
        self.beats = beats
        self.file = Path(path)
        self._refresh(0)
        self.status.set(f"Loaded {len(beats)} beats from {path}")


def main():
    ShotEditor().mainloop()


if __name__ == "__main__":
    main()
