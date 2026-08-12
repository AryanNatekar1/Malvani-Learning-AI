"""A small, dependency-free visual language for the desktop application.

Keeping the palette and ttk styles in one place makes the Tkinter interface
easier to improve without mixing presentation decisions into learning logic.
The theme deliberately uses calm, high-contrast colours so that it supports
reading and problem solving instead of competing with the lesson itself.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


PALETTE = {
    "app": "#F6F8FB",
    "surface": "#FFFFFF",
    "surface_soft": "#EEF5FA",
    "sidebar": "#102A43",
    "sidebar_active": "#1C4B70",
    "primary": "#075985",
    "primary_hover": "#0C4A6E",
    "accent": "#0F9D8A",
    "text": "#0F172A",
    "muted": "#475569",
    "border": "#D7E1EA",
    "success": "#16794A",
    "warning": "#9A6700",
    "danger": "#B42318",
    "white": "#FFFFFF",
}


def configure_theme(root: tk.Misc) -> ttk.Style:
    """Apply the application's semantic ttk styles to ``root``.

    This stays intentionally small: it is a visual layer, not a third-party
    UI framework.  Every named style describes its purpose rather than the
    screen where it happens to be used.
    """
    style = ttk.Style(root)
    try:
        if style.theme_use() != "clam":
            style.theme_use("clam")
    except tk.TclError:
        # A platform may not provide the clam theme; the configured styles
        # below still give a usable interface with the native fallback.
        pass

    root.configure(background=PALETTE["app"])
    style.configure(".", font=("Segoe UI", 10), background=PALETTE["app"], foreground=PALETTE["text"])
    style.configure("App.TFrame", background=PALETTE["app"])
    style.configure("Surface.TFrame", background=PALETTE["surface"])
    style.configure("Soft.TFrame", background=PALETTE["surface_soft"])
    style.configure("Sidebar.TFrame", background=PALETTE["sidebar"])
    style.configure("Topbar.TFrame", background=PALETTE["surface"])
    style.configure("Card.TFrame", background=PALETTE["surface"], relief="solid", borderwidth=1)
    style.configure("LessonCard.TFrame", background=PALETTE["surface"], relief="solid", borderwidth=1)
    style.configure(
        "Surface.TLabel",
        background=PALETTE["surface"],
        foreground=PALETTE["text"],
    )
    style.configure(
        "SurfaceMuted.TLabel",
        background=PALETTE["surface"],
        foreground=PALETTE["muted"],
    )
    style.configure(
        "Warning.TLabel",
        background=PALETTE["surface"],
        foreground=PALETTE["warning"],
    )
    style.configure(
        "Soft.TLabel",
        background=PALETTE["surface_soft"],
        foreground=PALETTE["text"],
    )

    style.configure(
        "Title.TLabel",
        font=("Segoe UI", 26, "bold"),
        background=PALETTE["app"],
        foreground=PALETTE["text"],
    )
    style.configure(
        "PageTitle.TLabel",
        font=("Segoe UI", 20, "bold"),
        background=PALETTE["surface"],
        foreground=PALETTE["text"],
    )
    style.configure(
        "Section.TLabel",
        font=("Segoe UI", 15, "bold"),
        background=PALETTE["app"],
        foreground=PALETTE["text"],
    )
    style.configure(
        "CardTitle.TLabel",
        font=("Segoe UI", 11, "bold"),
        background=PALETTE["surface"],
        foreground=PALETTE["primary"],
    )
    style.configure(
        "CardBody.TLabel",
        font=("Segoe UI", 10),
        background=PALETTE["surface"],
        foreground=PALETTE["text"],
    )
    style.configure(
        "Subtitle.TLabel",
        font=("Segoe UI", 10),
        background=PALETTE["app"],
        foreground=PALETTE["muted"],
    )
    style.configure(
        "TopbarTitle.TLabel",
        font=("Segoe UI", 14, "bold"),
        background=PALETTE["surface"],
        foreground=PALETTE["text"],
    )
    style.configure(
        "TopbarMeta.TLabel",
        font=("Segoe UI", 9),
        background=PALETTE["surface"],
        foreground=PALETTE["muted"],
    )
    style.configure(
        "SidebarBrand.TLabel",
        font=("Segoe UI", 16, "bold"),
        background=PALETTE["sidebar"],
        foreground=PALETTE["white"],
    )
    style.configure(
        "SidebarMeta.TLabel",
        font=("Segoe UI", 9),
        background=PALETTE["sidebar"],
        foreground="#C7D7E6",
    )
    style.configure(
        "Status.TLabel",
        font=("Segoe UI", 9),
        background=PALETTE["surface_soft"],
        foreground=PALETTE["primary"],
        padding=(10, 5),
    )
    style.configure(
        "MetricValue.TLabel",
        font=("Segoe UI", 18, "bold"),
        background=PALETTE["surface"],
        foreground=PALETTE["primary"],
    )
    style.configure(
        "MetricLabel.TLabel",
        font=("Segoe UI", 9),
        background=PALETTE["surface"],
        foreground=PALETTE["muted"],
    )

    style.configure(
        "Primary.TButton",
        font=("Segoe UI", 10, "bold"),
        foreground=PALETTE["white"],
        background=PALETTE["primary"],
        borderwidth=0,
        padding=(14, 8),
    )
    style.map(
        "Primary.TButton",
        background=[("active", PALETTE["primary_hover"]), ("disabled", "#94A3B8")],
        foreground=[("disabled", PALETTE["white"])],
    )
    style.configure(
        "Secondary.TButton",
        font=("Segoe UI", 10),
        foreground=PALETTE["primary"],
        background=PALETTE["surface"],
        borderwidth=1,
        padding=(12, 7),
    )
    style.map(
        "Secondary.TButton",
        background=[("active", PALETTE["surface_soft"]), ("disabled", PALETTE["app"])],
        foreground=[("disabled", "#94A3B8")],
    )
    style.configure(
        "Chip.TButton",
        font=("Segoe UI", 9),
        foreground=PALETTE["primary"],
        background=PALETTE["surface_soft"],
        borderwidth=0,
        padding=(9, 5),
    )
    style.map("Chip.TButton", background=[("active", "#D9EEF5")])
    style.configure(
        "Nav.TButton",
        anchor="w",
        font=("Segoe UI", 10),
        foreground="#D6E4F0",
        background=PALETTE["sidebar"],
        borderwidth=0,
        padding=(14, 10),
    )
    style.map(
        "Nav.TButton",
        background=[("active", PALETTE["sidebar_active"])],
        foreground=[("active", PALETTE["white"])],
    )
    style.configure(
        "ActiveNav.TButton",
        anchor="w",
        font=("Segoe UI", 10, "bold"),
        foreground=PALETTE["white"],
        background=PALETTE["sidebar_active"],
        borderwidth=0,
        padding=(14, 10),
    )
    style.map("ActiveNav.TButton", background=[("active", "#27638F")])
    style.configure(
        "CompactNav.TButton",
        font=("Segoe UI", 9),
        foreground=PALETTE["primary"],
        background=PALETTE["surface"],
        borderwidth=0,
        padding=(7, 4),
    )
    style.map("CompactNav.TButton", background=[("active", PALETTE["surface_soft"])])

    style.configure(
        "Card.TLabelframe",
        background=PALETTE["surface"],
        bordercolor=PALETTE["border"],
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=PALETTE["surface"],
        foreground=PALETTE["text"],
        font=("Segoe UI", 11, "bold"),
    )
    style.configure(
        "TEntry",
        fieldbackground=PALETTE["surface"],
        bordercolor=PALETTE["border"],
        padding=(9, 7),
    )
    style.map("TEntry", bordercolor=[("focus", PALETTE["primary"])])
    style.configure(
        "TCombobox",
        fieldbackground=PALETTE["surface"],
        background=PALETTE["surface"],
        padding=(7, 5),
    )
    style.configure(
        "Tutor.Horizontal.TProgressbar",
        troughcolor=PALETTE["surface_soft"],
        background=PALETTE["accent"],
        bordercolor=PALETTE["surface_soft"],
        lightcolor=PALETTE["accent"],
        darkcolor=PALETTE["accent"],
    )
    return style
