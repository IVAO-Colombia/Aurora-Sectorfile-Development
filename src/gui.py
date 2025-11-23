#!/usr/bin/env python3
"""
Tkinter GUI that imports installer.run and calls it in a thread.

This version includes defensive checks and clearer diagnostics for the
"bool object has no attribute '_root'" error that occurs when a boolean
is passed where a Tk root is expected.
"""
import os
import sys
import threading
import queue
import tkinter as tk
from tkinter import StringVar, BooleanVar, END, filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

# Try to import installer.run (module should be next to this file or bundled)
try:
    from installer import run as installer_run
except Exception:
    # Adjust sys.path to allow running from repo layout where this file sits in Development/
    this_dir = os.path.dirname(__file__)
    if this_dir not in sys.path:
        sys.path.insert(0, this_dir)
    from installer import run as installer_run  # may still raise, that's fine

class GUI:
    def __init__(self, root):
        # Defensive check: ensure 'root' is a Tk instance (or at least a tkinter widget)
        if not hasattr(root, "tk"):
            # helpful diagnostic to users/packagers
            raise TypeError(f"Expected tkinter root (Tk instance), but got {type(root)!r}. "
                            "Ensure you call GUI with root = tk.Tk() and not a boolean.")
        self.root = root
        root.title("Aurora Sectorfile Link Installer")
        root.geometry("760x520")

        self.aurora = StringVar()
        self.repo = StringVar()
        self.force = BooleanVar(value=False)
        self.dry_run = BooleanVar(value=False)
        self.debug = BooleanVar(value=False)

        frame = ttk.Frame(root, padding=8)
        frame.pack(fill='both', expand=True)

        # Aurora selector
        row = ttk.Frame(frame); row.pack(fill='x', pady=4)
        ttk.Label(row, text="Aurora (.exe or folder or SectorFiles):").pack(side='left')
        self.aurora_entry = ttk.Entry(row, textvariable=self.aurora, width=60); self.aurora_entry.pack(side='left', padx=6)
        ttk.Button(row, text="Browse...", command=self.browse_aurora).pack(side='left')

        # Repo selector
        row = ttk.Frame(frame); row.pack(fill='x', pady=4)
        ttk.Label(row, text="Repo (SectorFile-MAIN or repo root):").pack(side='left')
        self.repo_entry = ttk.Entry(row, textvariable=self.repo, width=60); self.repo_entry.pack(side='left', padx=6)
        ttk.Button(row, text="Browse...", command=self.browse_repo).pack(side='left')

        # Options
        opts = ttk.Frame(frame); opts.pack(fill='x', pady=6)
        ttk.Checkbutton(opts, text="Force", variable=self.force).pack(side='left', padx=6)
        ttk.Checkbutton(opts, text="Dry run", variable=self.dry_run).pack(side='left', padx=6)
        ttk.Checkbutton(opts, text="Debug", variable=self.debug).pack(side='left', padx=6)

        # Execute buttons
        row = ttk.Frame(frame); row.pack(fill='x', pady=8)
        self.exec_btn = ttk.Button(row, text="Execute", command=self.execute); self.exec_btn.pack(side='left', padx=6)
        ttk.Button(row, text="Clear", command=self.clear_log).pack(side='left', padx=6)

        # Progress
        self.progress = ttk.Progressbar(frame, mode='determinate')
        self.progress.pack(fill='x', pady=4)
        self.progress['value'] = 0

        # Output
        ttk.Label(frame, text="Output:").pack(anchor='w')
        self.log = ScrolledText(frame, height=20, wrap='none')
        self.log.pack(fill='both', expand=True)

        self._queue = queue.Queue()
        self._thread = None

    def browse_aurora(self):
        p = filedialog.askopenfilename(filetypes=[("exe","*.exe"),("All","*.*")])
        if p:
            self.aurora.set(p); return
        d = filedialog.askdirectory()
        if d: self.aurora.set(d)

    def browse_repo(self):
        d = filedialog.askdirectory()
        if d: self.repo.set(d)

    def append_log(self, text):
        self.log.insert(END, text); self.log.see('end')

    def clear_log(self):
        self.log.delete(1.0, END)

    def disable_ui(self):
        self.exec_btn.configure(state='disabled')

    def enable_ui(self):
        self.exec_btn.configure(state='normal')

    def execute(self):
        aurora = self.aurora.get().strip()
        repo = self.repo.get().strip()
        if not aurora or not repo:
            messagebox.showerror("Missing", "Please provide Aurora path and Repo path")
            return
        self.clear_log(); self.disable_ui()
        self.progress.config(mode='indeterminate'); self.progress.start(20)

        def log_cb(msg):
            self._queue.put(("log", msg))
        def prog_cb(pct):
            self._queue.put(("prog", pct))

        def worker():
            try:
                rc = installer_run(aurora, repo, force=self.force.get(), dry_run=self.dry_run.get(), debug=self.debug.get(),
                                   progress=prog_cb, log=log_cb)
                self._queue.put(("done", rc))
            except Exception as e:
                self._queue.put(("error", str(e)))

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()
        self.root.after(100, self._poll)

    def _poll(self):
        try:
            while True:
                t, payload = self._queue.get_nowait()
                if t == "log":
                    self.append_log(payload)
                elif t == "prog":
                    if payload == -1:
                        self.progress.config(mode='indeterminate')
                        self.progress.start(20)
                    else:
                        self.progress.config(mode='determinate')
                        self.progress.stop()
                        self.progress['value'] = int(payload)
                elif t == "done":
                    self.append_log(f"\n[Done] return code: {payload}\n")
                    self.progress.stop(); self.enable_ui()
                elif t == "error":
                    self.append_log(f"\n[ERROR] {payload}\n")
                    self.progress.stop(); self.enable_ui()
        except queue.Empty:
            pass
        if self._thread and self._thread.is_alive():
            self.root.after(200, self._poll)
        else:
            self.progress.stop(); self.enable_ui()

def main():
    # Ensure we create a real Tk instance here
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()