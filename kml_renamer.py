"""
KML Polygon Renamer & Exporter — Commercial Edition
Premium GUI tool for batch-renaming and exporting KML polygons.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
import os
import copy
import datetime
import math

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Design Tokens
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C = {
    "bg":            "#f5f6fa",
    "bg_sidebar":    "#ffffff",
    "bg_card":       "#ffffff",
    "bg_input":      "#f0f1f6",
    "bg_hover":      "#e8eaf2",
    "bg_titlebar":   "#ffffff",
    "accent":        "#6c5ce7",
    "accent_glow":   "#7f70f0",
    "accent_dark":   "#5a4bd1",
    "accent_subtle": "#ede9ff",
    "success":       "#00b894",
    "warning":       "#f0932b",
    "error":         "#e55039",
    "text":          "#1e2039",
    "text_dim":      "#5f6280",
    "text_muted":    "#a0a3b8",
    "border":        "#e2e4ed",
    "border_accent": "#c5bffa",
    "separator":     "#e8eaf2",
}

FONT      = "Segoe UI"
FONT_MONO = "Cascadia Code"
KML_NS    = "http://www.opengis.net/kml/2.2"
APP_VER   = "2.0"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Custom Widgets
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class PillButton(tk.Label):
    """Hover-animated pill-shaped button using Label widget."""

    def __init__(self, parent, text="", command=None,
                 bg_color=None, fg_color="#ffffff",
                 hover_color=None, font_cfg=None, padx=24, pady=10):
        self._bg = bg_color or C["accent"]
        self._hover = hover_color or C["accent_glow"]
        self._fg = fg_color
        self._cmd = command

        super().__init__(parent, text=text, bg=self._bg, fg=self._fg,
                         font=font_cfg or (FONT, 10, "bold"),
                         padx=padx, pady=pady, cursor="hand2")

        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg))
        self.bind("<ButtonRelease-1>", lambda e: self._cmd() if self._cmd else None)

    def set_enabled(self, on: bool):
        if on:
            self.config(bg=self._bg, fg=self._fg, cursor="hand2")
            self.bind("<ButtonRelease-1>", lambda e: self._cmd() if self._cmd else None)
        else:
            self.config(bg=C["bg_hover"], fg=C["text_muted"], cursor="arrow")
            self.unbind("<ButtonRelease-1>")


class SmallBtn(tk.Label):
    """Small secondary button."""

    def __init__(self, parent, text="", command=None):
        super().__init__(parent, text=text, bg=C["bg_hover"], fg=C["text_dim"],
                         font=(FONT, 9), padx=14, pady=6, cursor="hand2")
        self.bind("<Enter>", lambda e: self.config(bg=C["accent_subtle"],
                                                    fg=C["text"]))
        self.bind("<Leave>", lambda e: self.config(bg=C["bg_hover"],
                                                    fg=C["text_dim"]))
        self.bind("<ButtonRelease-1>", lambda e: command() if command else None)


class ToggleSwitch(tk.Canvas):
    """Animated toggle switch."""

    def __init__(self, parent, variable=None, command=None):
        super().__init__(parent, width=48, height=24,
                         bg=C["bg_card"], highlightthickness=0, cursor="hand2")
        self._var = variable or tk.BooleanVar(value=False)
        self._cmd = command
        self._draw()
        self.bind("<ButtonRelease-1>", self._toggle)

    def _draw(self):
        self.delete("all")
        on = self._var.get()
        track_color = C["accent"] if on else C["bg_hover"]
        # Track
        self.create_oval(0, 0, 24, 24, fill=track_color, outline="")
        self.create_oval(24, 0, 48, 24, fill=track_color, outline="")
        self.create_rectangle(12, 0, 36, 24, fill=track_color, outline="")
        # Thumb
        cx = 35 if on else 13
        self.create_oval(cx - 9, 3, cx + 9, 21, fill="#ffffff", outline=C["border"])

    def _toggle(self, event=None):
        self._var.set(not self._var.get())
        self._draw()
        if self._cmd:
            self._cmd()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Separator
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def h_sep(parent, color=None):
    tk.Frame(parent, bg=color or C["separator"], height=1).pack(fill="x", pady=16)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Application
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class KMLRenamerApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("KML Polygon Tool")
        self.root.configure(bg=C["bg"])
        self.root.minsize(960, 680)

        # State
        self.input_path            = tk.StringVar()
        self.output_path           = tk.StringVar()
        self.prefix_var            = tk.StringVar()
        self.folder_var            = tk.StringVar()
        self.export_enabled        = tk.BooleanVar(value=False)
        self.export_dir_var        = tk.StringVar()
        self.add_area_var          = tk.BooleanVar(value=True)
        self.export_only_var       = tk.BooleanVar(value=False)
        self.folder_list: list[str] = []
        self._log_count = 0
        self._current_step = 0

        self._build()

    # ──────────────────────────────────────────
    # Root Layout
    # ──────────────────────────────────────────
    def _build(self):
        # Title bar
        self._build_titlebar()

        # Body
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_main_area(body)

    def _build_titlebar(self):
        tb = tk.Frame(self.root, bg=C["bg_titlebar"], height=40)
        tb.pack(fill="x")
        tb.pack_propagate(False)

        tk.Label(tb, text="◆", bg=C["bg_titlebar"], fg=C["accent"],
                 font=(FONT, 15)).pack(side="left", padx=(16, 6))
        tk.Label(tb, text="KML Polygon Tool", bg=C["bg_titlebar"], fg=C["text"],
                 font=(FONT, 10, "bold")).pack(side="left")
        tk.Label(tb, text=f"v{APP_VER}", bg=C["bg_titlebar"], fg=C["text_muted"],
                 font=(FONT, 8)).pack(side="left", padx=(8, 0))

    # ──────────────────────────────────────────
    # Sidebar
    # ──────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C["bg_sidebar"], width=260)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        pad = 24

        # Brand
        tk.Label(sb, text="KML Polygon", bg=C["bg_sidebar"], fg=C["text"],
                 font=(FONT, 18, "bold"), anchor="w").pack(fill="x", padx=pad, pady=(30, 0))
        tk.Label(sb, text="Renamer & Exporter", bg=C["bg_sidebar"], fg=C["accent"],
                 font=(FONT, 18, "bold"), anchor="w").pack(fill="x", padx=pad)

        tk.Frame(sb, bg=C["separator"], height=1).pack(fill="x", padx=pad, pady=(22, 16))

        tk.Label(sb, text="Công cụ đổi tên & xuất polygon\nhàng loạt từ file KML Google Earth",
                 bg=C["bg_sidebar"], fg=C["text_dim"], font=(FONT, 9),
                 anchor="w", justify="left").pack(fill="x", padx=pad)

        tk.Frame(sb, bg=C["separator"], height=1).pack(fill="x", padx=pad, pady=(16, 16))

        tk.Label(sb, text="QUY TRÌNH", bg=C["bg_sidebar"], fg=C["text_muted"],
                 font=(FONT, 8, "bold"), anchor="w").pack(fill="x", padx=pad, pady=(0, 12))

        # Step indicators
        self.step_labels = []
        step_names = ["Chọn file KML", "Cấu hình đổi tên", "Xuất file (tuỳ chọn)", "Chạy & hoàn tất"]
        for i, name in enumerate(step_names):
            row = tk.Frame(sb, bg=C["bg_sidebar"])
            row.pack(fill="x", padx=pad, pady=3)

            num_color = C["accent"] if i == 0 else C["text_muted"]
            num_bg    = C["accent_subtle"] if i == 0 else C["bg_sidebar"]
            txt_color = C["accent"] if i == 0 else C["text_muted"]

            num_lbl = tk.Label(row, text=f" {i+1} ", bg=num_bg, fg=num_color,
                               font=(FONT, 10, "bold"), width=3)
            num_lbl.pack(side="left", padx=(0, 10))

            txt_lbl = tk.Label(row, text=name, bg=C["bg_sidebar"], fg=txt_color,
                               font=(FONT, 10), anchor="w")
            txt_lbl.pack(side="left", fill="x")

            self.step_labels.append((num_lbl, txt_lbl))

        # Footer
        tk.Frame(sb, bg=C["bg_sidebar"]).pack(fill="both", expand=True)
        tk.Label(sb, text="Made with ♥ for GIS workflows",
                 bg=C["bg_sidebar"], fg=C["text_muted"],
                 font=(FONT, 8)).pack(pady=(0, 18))

    def _set_step(self, idx: int):
        """Update sidebar step indicators (0-based)."""
        self._current_step = idx
        for i, (num_lbl, txt_lbl) in enumerate(self.step_labels):
            if i < idx:  # completed
                num_lbl.config(text=" ✓ ", bg=C["accent_subtle"], fg=C["success"])
                txt_lbl.config(fg=C["success"])
            elif i == idx:  # current
                num_lbl.config(text=f" {i+1} ", bg=C["accent_subtle"], fg=C["accent"])
                txt_lbl.config(fg=C["accent"])
            else:  # future
                num_lbl.config(text=f" {i+1} ", bg=C["bg_sidebar"], fg=C["text_muted"])
                txt_lbl.config(fg=C["text_muted"])

    # ──────────────────────────────────────────
    # Main Area
    # ──────────────────────────────────────────
    def _build_main_area(self, parent):
        style = ttk.Style()
        style.theme_use("clam")

        content = tk.Frame(parent, bg=C["bg"])
        content.pack(side="left", fill="both", expand=True, padx=28, pady=16)

        self._section_file(content)
        self._section_rename(content)
        self._section_export(content)
        self._section_action(content)
        self._section_log(content)

    # ──────────────────────────────────────────
    # Section: File Input
    # ──────────────────────────────────────────
    def _section_file(self, parent):
        card = tk.Frame(parent, bg=C["bg_card"], padx=20, pady=14)
        card.pack(fill="x", pady=(0, 8))

        # Header row
        hdr = tk.Frame(card, bg=C["bg_card"])
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text="📁  File KML đầu vào", bg=C["bg_card"], fg=C["text"],
                 font=(FONT, 11, "bold")).pack(side="left")
        self.file_info_label = tk.Label(hdr, text="", bg=C["bg_card"], fg=C["success"],
                                         font=(FONT_MONO, 9))
        self.file_info_label.pack(side="right")

        # Input row
        row = tk.Frame(card, bg=C["bg_card"])
        row.pack(fill="x")

        inp_wrap = tk.Frame(row, bg=C["bg_input"], padx=12, pady=7)
        inp_wrap.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry = tk.Entry(inp_wrap, textvariable=self.input_path,
                                     bg=C["bg_input"], fg=C["text"], font=(FONT, 10),
                                     insertbackground=C["text"], relief="flat", border=0)
        self.input_entry.pack(fill="x")

        SmallBtn(row, text="  Chọn file…  ", command=self._browse_input).pack(side="right")

    # ──────────────────────────────────────────
    # Section: Rename Settings
    # ──────────────────────────────────────────
    def _section_rename(self, parent):
        card = tk.Frame(parent, bg=C["bg_card"], padx=20, pady=14)
        card.pack(fill="x", pady=(0, 8))

        tk.Label(card, text="⚙️  Cấu hình đổi tên", bg=C["bg_card"], fg=C["text"],
                 font=(FONT, 11, "bold")).pack(anchor="w", pady=(0, 8))

        grid = tk.Frame(card, bg=C["bg_card"])
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)

        def _lbl(r, t):
            tk.Label(grid, text=t, bg=C["bg_card"], fg=C["text_dim"],
                     font=(FONT, 10), anchor="e").grid(row=r, column=0,
                     sticky="e", padx=(0, 14), pady=4)

        # Folder combo
        _lbl(0, "Thư mục")
        style = ttk.Style()
        style.configure("Dark.TCombobox",
                         fieldbackground=C["bg_input"], background=C["bg_input"],
                         foreground=C["text"], selectbackground=C["accent"],
                         padding=(12, 7), borderwidth=0)
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", C["bg_input"])],
                  selectbackground=[("readonly", C["accent"])])
        self.folder_combo = ttk.Combobox(grid, textvariable=self.folder_var,
                                          style="Dark.TCombobox", state="readonly")
        self.folder_combo.grid(row=0, column=1, sticky="ew", pady=4)
        self.folder_combo.bind("<<ComboboxSelected>>", self._on_folder_selected)

        # Prefix
        _lbl(1, "Prefix")
        pf = tk.Frame(grid, bg=C["bg_input"], padx=12, pady=7)
        pf.grid(row=1, column=1, sticky="ew", pady=4)
        self.prefix_entry = tk.Entry(pf, textvariable=self.prefix_var,
                                      bg=C["bg_input"], fg=C["text"], font=(FONT, 10),
                                      insertbackground=C["text"], relief="flat", border=0)
        self.prefix_entry.pack(fill="x")

        # Output file
        _lbl(2, "File đầu ra")
        out_row = tk.Frame(grid, bg=C["bg_card"])
        out_row.grid(row=2, column=1, sticky="ew", pady=4)
        out_row.columnconfigure(0, weight=1)

        of = tk.Frame(out_row, bg=C["bg_input"], padx=12, pady=7)
        of.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.output_entry = tk.Entry(of, textvariable=self.output_path,
                                      bg=C["bg_input"], fg=C["text"], font=(FONT, 10),
                                      insertbackground=C["text"], relief="flat", border=0)
        self.output_entry.pack(fill="x")
        SmallBtn(out_row, text="  Chọn…  ", command=self._browse_output).grid(row=0, column=1)

        # Area option
        opt_row = tk.Frame(grid, bg=C["bg_card"])
        opt_row.grid(row=3, column=1, sticky="w", pady=(6, 2))

        cb_area = tk.Checkbutton(
            opt_row, text="📏  Kèm diện tích vào tên (VD: XaYaMa17 - 3ha)",
            variable=self.add_area_var, bg=C["bg_card"], fg=C["text"],
            selectcolor=C["bg_input"], activebackground=C["bg_card"],
            activeforeground=C["text"], font=(FONT, 9, "bold"),
            cursor="hand2"
        )
        cb_area.pack(side="left")

    # ──────────────────────────────────────────
    # Section: Export Options
    # ──────────────────────────────────────────
    def _section_export(self, parent):
        card = tk.Frame(parent, bg=C["bg_card"], padx=20, pady=14)
        card.pack(fill="x", pady=(0, 8))

        # Header with toggle
        hdr = tk.Frame(card, bg=C["bg_card"])
        hdr.pack(fill="x")

        tk.Label(hdr, text="📤  Xuất file KML riêng lẻ", bg=C["bg_card"], fg=C["text"],
                 font=(FONT, 11, "bold")).pack(side="left")
        tk.Label(hdr, text="  (mỗi polygon → 1 file outline)",
                 bg=C["bg_card"], fg=C["text_dim"], font=(FONT, 9)).pack(side="left")

        self.toggle = ToggleSwitch(hdr, variable=self.export_enabled,
                                    command=self._on_toggle_export)
        self.toggle.pack(side="right")

        # Expandable options
        self.export_frame = tk.Frame(card, bg=C["bg_card"])

        exp_row = tk.Frame(self.export_frame, bg=C["bg_card"])
        exp_row.pack(fill="x", pady=(6, 0))
        exp_row.columnconfigure(1, weight=1)

        tk.Label(exp_row, text="Thư mục xuất", bg=C["bg_card"], fg=C["text_dim"],
                 font=(FONT, 10), anchor="e").grid(row=0, column=0, sticky="e", padx=(0, 14))

        dir_row = tk.Frame(exp_row, bg=C["bg_card"])
        dir_row.grid(row=0, column=1, sticky="ew")
        dir_row.columnconfigure(0, weight=1)

        df = tk.Frame(dir_row, bg=C["bg_input"], padx=12, pady=7)
        df.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.export_dir_entry = tk.Entry(df, textvariable=self.export_dir_var,
                                          bg=C["bg_input"], fg=C["text"], font=(FONT, 10),
                                          insertbackground=C["text"], relief="flat", border=0)
        self.export_dir_entry.pack(fill="x")
        SmallBtn(dir_row, text="  Chọn…  ", command=self._browse_export_dir).grid(row=0, column=1)

        # Option: Export only, do not rename
        opt_export_only_row = tk.Frame(self.export_frame, bg=C["bg_card"])
        opt_export_only_row.pack(fill="x", pady=(8, 2))

        cb_no_rename = tk.Checkbutton(
            opt_export_only_row,
            text="⚡  Chỉ xuất file riêng lẻ chứ không đổi tên (giữ nguyên tên gốc)",
            variable=self.export_only_var,
            command=self._on_toggle_export_only,
            bg=C["bg_card"], fg=C["text"],
            selectcolor=C["bg_input"], activebackground=C["bg_card"],
            activeforeground=C["text"], font=(FONT, 9, "bold"),
            cursor="hand2"
        )
        cb_no_rename.pack(side="left")

    def _on_toggle_export(self):
        if self.export_enabled.get():
            self.export_frame.pack(fill="x")
            if not self.export_dir_var.get() and self.input_path.get():
                parent_dir = os.path.dirname(self.input_path.get())
                folder = self.folder_var.get()
                d = folder if folder and folder != "(Toàn bộ file)" else "polygon_export"
                self.export_dir_var.set(os.path.join(parent_dir, d))
            self._set_step(2)
            self._update_run_btn_text()
        else:
            self.export_frame.pack_forget()
            self.export_only_var.set(False)
            self._on_toggle_export_only()

    def _on_toggle_export_only(self):
        is_only = self.export_only_var.get()
        if is_only:
            self.prefix_entry.config(state="disabled")
            self.output_entry.config(state="disabled")
        else:
            self.prefix_entry.config(state="normal")
            self.output_entry.config(state="normal")
        self._update_run_btn_text()

    def _update_run_btn_text(self):
        if hasattr(self, "run_btn"):
            if self.export_only_var.get():
                self.run_btn.config(text="  ▶  Xuất file KML riêng lẻ  ")
            elif self.export_enabled.get():
                self.run_btn.config(text="  ▶  Chạy đổi tên & Xuất file  ")
            else:
                self.run_btn.config(text="  ▶  Chạy đổi tên  ")

    # ──────────────────────────────────────────
    # Section: Action Bar
    # ──────────────────────────────────────────
    def _section_action(self, parent):
        bar = tk.Frame(parent, bg=C["bg"])
        bar.pack(fill="x", pady=(4, 8))

        self.run_btn = PillButton(bar, text="  ▶  Chạy đổi tên  ",
                                   command=self._run_rename,
                                   bg_color=C["accent"], hover_color=C["accent_glow"],
                                   font_cfg=(FONT, 11, "bold"), padx=24, pady=10)
        self.run_btn.pack(side="left")

        prog_col = tk.Frame(bar, bg=C["bg"])
        prog_col.pack(side="left", fill="x", expand=True, padx=(20, 0))

        self.status_label = tk.Label(prog_col, text="Sẵn sàng", bg=C["bg"],
                                      fg=C["text_muted"], font=(FONT, 9), anchor="w")
        self.status_label.pack(fill="x")

        self.prog_track = tk.Frame(prog_col, bg=C["bg_input"], height=4)
        self.prog_track.pack(fill="x", pady=(4, 0))
        self.prog_track.pack_propagate(False)
        self.prog_fill = tk.Frame(self.prog_track, bg=C["accent"], height=4, width=0)
        self.prog_fill.place(x=0, y=0, relheight=1, relwidth=0)

    def _set_progress(self, pct: float):
        self.prog_fill.place(x=0, y=0, relheight=1, relwidth=pct / 100)
        self.root.update_idletasks()

    # ──────────────────────────────────────────
    # Section: Log Panel
    # ──────────────────────────────────────────
    def _section_log(self, parent):
        card = tk.Frame(parent, bg=C["bg_card"], padx=20, pady=12)
        card.pack(fill="both", expand=True, pady=(0, 4))

        hdr = tk.Frame(card, bg=C["bg_card"])
        hdr.pack(fill="x", pady=(0, 6))
        tk.Label(hdr, text="📋  Nhật ký", bg=C["bg_card"], fg=C["text"],
                 font=(FONT, 10, "bold")).pack(side="left")
        self.log_count_lbl = tk.Label(hdr, text="0 dòng", bg=C["bg_card"],
                                       fg=C["text_muted"], font=(FONT, 8))
        self.log_count_lbl.pack(side="right")

        txt_frame = tk.Frame(card, bg=C["bg_input"])
        txt_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            txt_frame, bg=C["bg_input"], fg=C["text_dim"],
            insertbackground=C["text"], font=(FONT_MONO, 9),
            relief="flat", borderwidth=0, padx=12, pady=8,
            wrap="word", state="disabled", height=6,
            selectbackground=C["accent"], selectforeground="#ffffff",
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(txt_frame, orient="vertical", command=self.log_text.yview)
        sb.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=sb.set)

        self.log_text.tag_configure("info",    foreground=C["text_dim"])
        self.log_text.tag_configure("success", foreground=C["success"])
        self.log_text.tag_configure("warning", foreground=C["warning"])
        self.log_text.tag_configure("error",   foreground=C["error"])
        self.log_text.tag_configure("accent",  foreground=C["accent_glow"])
        self.log_text.tag_configure("ts",      foreground=C["text_muted"])

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────
    def _log(self, msg: str, tag: str = "info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f" {ts}  ", "ts")
        self.log_text.insert("end", f"{msg}\n", tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self._log_count += 1
        self.log_count_lbl.config(text=f"{self._log_count} dòng")

    def _set_status(self, text: str):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    # ──────────────────────────────────────────
    # Callbacks
    # ──────────────────────────────────────────
    def _on_folder_selected(self, event=None):
        sel = self.folder_var.get()
        if sel and sel != "(Toàn bộ file)":
            self.prefix_var.set(f"{sel}_Ca")
            self._log(f"Prefix tự động → {sel}_Ca")
            if self.input_path.get():
                parent_dir = os.path.dirname(self.input_path.get())
                self.export_dir_var.set(os.path.join(parent_dir, sel))
            self._set_step(1)
        else:
            self.prefix_var.set("")

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Chọn file KML đầu vào",
            filetypes=[("KML Files", "*.kml"), ("All Files", "*.*")]
        )
        if path:
            self.input_path.set(path)
            size = os.path.getsize(path) / 1024
            self.file_info_label.config(
                text=f"✓  {os.path.basename(path)}  •  {size:.1f} KB",
                fg=C["success"])
            self._log(f"Đã chọn file: {os.path.basename(path)}", "success")
            self._load_kml_folders(path)

            base, ext = os.path.splitext(path)
            self.output_path.set(f"{base}_Updated{ext}")

            parent_dir = os.path.dirname(path)
            folder = self.folder_var.get()
            d = folder if folder and folder != "(Toàn bộ file)" else "polygon_export"
            self.export_dir_var.set(os.path.join(parent_dir, d))
            self._set_step(1)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Lưu file KML đầu ra", defaultextension=".kml",
            filetypes=[("KML Files", "*.kml"), ("All Files", "*.*")]
        )
        if path:
            self.output_path.set(path)

    def _browse_export_dir(self):
        path = filedialog.askdirectory(title="Chọn thư mục xuất file riêng lẻ")
        if path:
            self.export_dir_var.set(path)

    # ──────────────────────────────────────────
    # KML Parsing
    # ──────────────────────────────────────────
    def _load_kml_folders(self, filepath: str):
        try:
            ET.register_namespace("", KML_NS)
            tree = ET.parse(filepath)
            root = tree.getroot()
            ns = {"kml": KML_NS}

            self.folder_list = []
            for folder in root.findall(".//kml:Folder", ns):
                nt = folder.find("kml:name", ns)
                if nt is not None and nt.text:
                    self.folder_list.append(nt.text)

            if self.folder_list:
                self.folder_combo["values"] = ["(Toàn bộ file)"] + self.folder_list
                self.folder_combo.current(0)
                self._log(f"Tìm thấy {len(self.folder_list)} thư mục:", "success")
                for f in self.folder_list:
                    self._log(f"  ├─ {f}")
            else:
                self.folder_combo["values"] = ["(Toàn bộ file)"]
                self.folder_combo.current(0)
                self._log("Không tìm thấy thư mục, quét toàn bộ file", "warning")
        except ET.ParseError as e:
            self._log(f"Lỗi parse KML: {e}", "error")
        except Exception as e:
            self._log(f"Lỗi: {e}", "error")

    # ──────────────────────────────────────────
    # Core: Rename + Export
    # ──────────────────────────────────────────
    def _run_rename(self):
        export_only = self.export_only_var.get()
        do_export = self.export_enabled.get() or export_only

        if not self.input_path.get():
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file KML đầu vào.")
            return

        if export_only:
            if not self.export_dir_var.get().strip():
                messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn thư mục xuất file riêng lẻ.")
                return
        else:
            if not self.prefix_var.get().strip():
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập prefix tên mới.")
                return
            if not self.output_path.get():
                messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn nơi lưu file đầu ra.")
                return
            if do_export and not self.export_dir_var.get().strip():
                messagebox.showwarning("Thiếu thông tin",
                                       "Đã bật xuất file riêng lẻ nhưng chưa chọn thư mục.")
                return

        self._set_step(3)
        self.run_btn.set_enabled(False)
        self._set_progress(0)
        self._set_status("Đang xử lý…")

        try:
            input_file  = self.input_path.get()
            output_file = self.output_path.get()
            prefix      = self.prefix_var.get().strip()
            target_name = self.folder_var.get()
            export_dir  = self.export_dir_var.get().strip() if do_export else None

            ET.register_namespace("", KML_NS)
            tree = ET.parse(input_file)
            root = tree.getroot()
            ns = {"kml": KML_NS}

            self._log("━" * 44, "accent")
            if export_only:
                self._log("▶  Bắt đầu xuất file KML riêng lẻ (Giữ nguyên tên gốc)", "accent")
            else:
                self._log(f"▶  Bắt đầu đổi tên & xuất  |  Prefix: {prefix}", "accent")

            if do_export:
                os.makedirs(export_dir, exist_ok=True)
                self._log(f"📤  Thư mục xuất → {export_dir}", "success")

            search_root = root
            if target_name and target_name != "(Toàn bộ file)":
                for folder in root.findall(".//kml:Folder", ns):
                    nt = folder.find("kml:name", ns)
                    if nt is not None and nt.text == target_name:
                        search_root = folder
                        self._log(f"📂  Thư mục: {target_name}", "success")
                        break
                else:
                    self._log(f"⚠  Không tìm thấy '{target_name}', quét toàn bộ", "warning")

            placemarks = search_root.findall(".//kml:Placemark", ns)
            total = len(placemarks)
            self._log(f"Tổng Placemark: {total}")

            add_area = self.add_area_var.get()
            count = 0
            exported = 0

            for i, pm in enumerate(placemarks):
                name_tag = pm.find("kml:name", ns)

                # Calculate area
                area_ha = self._get_placemark_area_ha(pm, ns) if add_area else 0.0
                area_str = self._format_area_ha(area_ha) if add_area else ""

                if export_only:
                    orig_name = (name_tag.text if (name_tag is not None and name_tag.text) else f"Polygon_{i+1}").strip()
                    if add_area and area_ha > 0 and not orig_name.endswith("ha"):
                        target_export_name = f"{orig_name} - {area_str}"
                    else:
                        target_export_name = orig_name
                    self._log(f"  📤  {orig_name}  →  {target_export_name}.kml" + (f" ({area_ha:.2f} ha → {area_str})" if add_area else ""))
                else:
                    count += 1
                    base_name = f"{prefix}{count}"
                    if add_area and area_ha > 0:
                        new_name = f"{base_name} - {area_str}"
                    else:
                        new_name = base_name

                    if name_tag is not None:
                        old = name_tag.text or "(không tên)"
                        name_tag.text = new_name
                    else:
                        old = "(không tên)"
                        name_tag = ET.SubElement(pm, f"{{{KML_NS}}}name")
                        name_tag.text = new_name

                    self._log(f"  ✏️  {old}  →  {new_name}" + (f" ({area_ha:.2f} ha → {area_str})" if add_area else ""))
                    target_export_name = new_name

                if do_export:
                    # Sanitize filename for individual export
                    safe_name = "".join(c for c in target_export_name if c not in r'/\:*?"<>|').strip()
                    if not safe_name:
                        safe_name = f"Polygon_{i+1}"
                    self._export_single(pm, safe_name, export_dir)
                    exported += 1

                if total > 0:
                    pct = ((i + 1) / total) * 100
                    self._set_progress(pct)
                    self._set_status(f"Đang xử lý… {int(pct)}%")

            if not export_only and output_file:
                tree.write(output_file, encoding="utf-8", xml_declaration=True)

            self._log("━" * 44, "accent")
            if export_only:
                self._log(f"✅  Hoàn tất! Đã xuất {exported} file KML riêng lẻ (giữ nguyên tên gốc)", "success")
                self._log(f"   Thư mục: {os.path.basename(export_dir)}/")
                self._set_progress(100)
                self._set_status(f"✅ Hoàn tất — {exported} file KML riêng lẻ đã xuất")
                messagebox.showinfo("Thành công", f"Đã xuất thành công {exported} file KML riêng lẻ (Outline)\nvào thư mục: {export_dir}")
            else:
                self._log(f"✅  Hoàn tất! Đã đổi tên toàn bộ {count} polygon", "success")
                self._log(f"   File tổng hợp: {os.path.basename(output_file)}")
                if do_export and exported:
                    self._log(f"   📤 Đã xuất tất cả {exported} file KML riêng lẻ → {os.path.basename(export_dir)}/", "success")

                self._set_progress(100)
                self._set_status(f"✅ Hoàn tất — {count} polygon đã đổi tên" +
                                 (f", {exported} file xuất" if exported else ""))

                if count > 0 or exported > 0:
                    msg = f"Đã đổi tên toàn bộ {count} polygon thành công!\n({prefix}1 → {prefix}{count})\n\nFile tổng hợp: {output_file}"
                    if exported:
                        msg += f"\n\nĐã xuất tất cả {exported} file KML riêng lẻ (Outline)\nvào: {export_dir}"
                    messagebox.showinfo("Thành công", msg)
                else:
                    messagebox.showinfo("Thông báo",
                                        "Không tìm thấy polygon nào để xử lý.")
        except Exception as e:
            self._log(f"❌  Lỗi: {e}", "error")
            self._set_status("❌ Lỗi xử lý")
            messagebox.showerror("Lỗi", str(e))
        finally:
            self.run_btn.set_enabled(True)

    # ──────────────────────────────────────────
    # Geometry & Area Calculation (WGS84)
    # ──────────────────────────────────────────
    @staticmethod
    def _parse_kml_coordinates(coord_text: str):
        coords = []
        if not coord_text:
            return coords
        for t in coord_text.strip().split():
            parts = t.split(",")
            if len(parts) >= 2:
                try:
                    lon = float(parts[0].strip())
                    lat = float(parts[1].strip())
                    coords.append((lon, lat))
                except ValueError:
                    continue
        return coords

    @staticmethod
    def _calculate_ring_area(coords):
        """Calculates area of spherical polygon ring in square meters using WGS84 ellipsoid mean radius."""
        if len(coords) < 3:
            return 0.0
        R = 6378137.0  # Earth radius in meters
        total = 0.0
        rad = math.pi / 180.0
        n = len(coords)
        for i in range(n):
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[(i + 1) % n]
            d_lon = (lon2 - lon1) * rad
            if d_lon > math.pi:
                d_lon -= 2 * math.pi
            elif d_lon < -math.pi:
                d_lon += 2 * math.pi
            total += d_lon * (math.sin(lat1 * rad) + math.sin(lat2 * rad))
        return abs(total) * (R * R) / 2.0

    def _get_placemark_area_ha(self, placemark, ns: dict) -> float:
        """Returns total area in hectares for a placemark."""
        total_area_m2 = 0.0
        polygons = placemark.findall(".//kml:Polygon", ns)
        if not polygons:
            polygons = [elem for elem in placemark.iter() if elem.tag.endswith("Polygon")]

        for poly in polygons:
            outer_elem = poly.find(".//kml:outerBoundaryIs//kml:coordinates", ns)
            if outer_elem is None:
                for elem in poly.iter():
                    if elem.tag.endswith("outerBoundaryIs"):
                        for c in elem.iter():
                            if c.tag.endswith("coordinates"):
                                outer_elem = c
                                break
            if outer_elem is not None and outer_elem.text:
                outer_coords = self._parse_kml_coordinates(outer_elem.text)
                poly_area = self._calculate_ring_area(outer_coords)

                # Subtract inner boundary holes
                inner_rings = poly.findall(".//kml:innerBoundaryIs//kml:coordinates", ns)
                if not inner_rings:
                    for elem in poly.iter():
                        if elem.tag.endswith("innerBoundaryIs"):
                            for c in elem.iter():
                                if c.tag.endswith("coordinates"):
                                    inner_rings.append(c)
                for inner_elem in inner_rings:
                    if inner_elem.text:
                        inner_coords = self._parse_kml_coordinates(inner_elem.text)
                        poly_area -= self._calculate_ring_area(inner_coords)

                total_area_m2 += max(0.0, poly_area)

        # Fallback to direct LinearRing if no Polygon element
        if total_area_m2 == 0.0 and not polygons:
            rings = placemark.findall(".//kml:LinearRing//kml:coordinates", ns)
            if not rings:
                rings = [elem for elem in placemark.iter() if elem.tag.endswith("coordinates")]
            for ring_elem in rings:
                if ring_elem.text:
                    coords = self._parse_kml_coordinates(ring_elem.text)
                    if len(coords) >= 3:
                        total_area_m2 += self._calculate_ring_area(coords)

        return total_area_m2 / 10000.0

    @staticmethod
    def _format_area_ha(area_ha: float) -> str:
        """Format area in whole rounded hectares (e.g. 12.23ha -> '12ha', 3.4ha -> '3ha')."""
        if area_ha <= 0:
            return "0ha"
        rounded = round(area_ha)
        if rounded == 0 and area_ha > 0:
            rounded = 1
        return f"{rounded}ha"

    # ──────────────────────────────────────────
    # Export: Single polygon → KML (outline only)
    # ──────────────────────────────────────────
    def _export_single(self, placemark, name: str, output_dir: str):
        pm_copy = copy.deepcopy(placemark)

        # Sync placemark internal name with the target name
        pm_name = pm_copy.find(f"{{{KML_NS}}}name")
        if pm_name is not None:
            pm_name.text = name
        else:
            ET.SubElement(pm_copy, f"{{{KML_NS}}}name").text = name

        su = pm_copy.find(f"{{{KML_NS}}}styleUrl")
        if su is not None:
            su.text = "#outline_only"
        else:
            su = ET.SubElement(pm_copy, f"{{{KML_NS}}}styleUrl")
            su.text = "#outline_only"

        new_root = ET.Element(f"{{{KML_NS}}}kml")
        doc = ET.SubElement(new_root, f"{{{KML_NS}}}Document")
        ET.SubElement(doc, f"{{{KML_NS}}}name").text = name

        style = ET.SubElement(doc, f"{{{KML_NS}}}Style", attrib={"id": "outline_only"})
        ls = ET.SubElement(style, f"{{{KML_NS}}}LineStyle")
        ET.SubElement(ls, f"{{{KML_NS}}}color").text = "ff0000ff"
        ET.SubElement(ls, f"{{{KML_NS}}}width").text = "2"
        ps = ET.SubElement(style, f"{{{KML_NS}}}PolyStyle")
        ET.SubElement(ps, f"{{{KML_NS}}}fill").text = "0"

        doc.append(pm_copy)
        ET.ElementTree(new_root).write(
            os.path.join(output_dir, f"{name}.kml"),
            encoding="utf-8", xml_declaration=True)




# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Entry
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    root = tk.Tk()
    root.update_idletasks()
    w, h = 1020, 800
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")
    KMLRenamerApp(root)
    root.mainloop()
