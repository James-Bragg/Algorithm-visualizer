"""Colour palette, typography and ttk styles."""

from __future__ import annotations

import sys
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from tkinter import ttk


@dataclass(frozen=True)
class Palette:
    bg: str = "#0e1016"
    surface: str = "#161922"
    surface_alt: str = "#1f2330"
    surface_hover: str = "#282d3d"
    border: str = "#2b3142"
    text: str = "#e8eaf0"
    text_muted: str = "#8b92a6"
    text_faint: str = "#5d6478"
    accent: str = "#6d72ff"
    accent_hover: str = "#8388ff"
    accent_pressed: str = "#585df0"
    accent_tint: str = "#262a52"
    on_accent: str = "#ffffff"
    bar: str = "#3e4a6c"
    compare: str = "#f5c04a"
    swap: str = "#f2557a"
    write: str = "#38bdf8"
    sorted: str = "#34d399"


PALETTE = Palette()

# Tk forgets images that Python stops referencing, so keep the themed ones here.
_images: list[tk.PhotoImage] = []

_FONT_FAMILIES = (
    "Segoe UI Variable Text",
    "Segoe UI",
    "SF Pro Text",
    "Helvetica Neue",
    "Inter",
    "Cantarell",
    "Ubuntu",
    "DejaVu Sans",
)


@dataclass(frozen=True)
class Theme:
    """Fonts and a pixel scale for the current display."""

    scale: float
    body: tuple
    body_bold: tuple
    small: tuple
    caption: tuple
    title: tuple
    heading: tuple
    stat: tuple

    def px(self, value: float) -> int:
        """Convert a size designed at 96 DPI to pixels on this display."""
        return round(value * self.scale)


def enable_dpi_awareness() -> None:
    """Ask Windows not to bitmap-stretch the window on high-DPI displays."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


def use_dark_title_bar(root: tk.Tk) -> None:
    """Match the Windows title bar to the dark UI (Windows 10 20H1 and later)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        enabled = ctypes.c_int(1)
        dwmwa_use_immersive_dark_mode = 20
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, dwmwa_use_immersive_dark_mode, ctypes.byref(enabled), ctypes.sizeof(enabled)
        )
    except (AttributeError, OSError):
        pass


def apply_theme(root: tk.Tk) -> Theme:
    available = set(tkfont.families(root))
    family = next((name for name in _FONT_FAMILIES if name in available), "TkDefaultFont")
    theme = Theme(
        scale=max(1.0, root.winfo_fpixels("1i") / 96),
        body=(family, 10),
        body_bold=(family, 10, "bold"),
        small=(family, 9),
        caption=(family, 8, "bold"),
        title=(family, 13, "bold"),
        heading=(family, 18, "bold"),
        stat=(family, 17, "bold"),
    )
    p = PALETTE
    px = theme.px

    root.configure(background=p.bg)
    root.option_add("*TCombobox*Listbox.background", p.surface_alt)
    root.option_add("*TCombobox*Listbox.foreground", p.text)
    root.option_add("*TCombobox*Listbox.selectBackground", p.accent)
    root.option_add("*TCombobox*Listbox.selectForeground", p.on_accent)
    root.option_add("*TCombobox*Listbox.borderWidth", 0)
    root.option_add("*TCombobox*Listbox.font", theme.body)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        ".",
        background=p.bg,
        foreground=p.text,
        font=theme.body,
        bordercolor=p.border,
        lightcolor=p.surface_alt,
        darkcolor=p.surface_alt,
        troughcolor=p.surface_alt,
        fieldbackground=p.surface_alt,
        selectbackground=p.accent,
        selectforeground=p.on_accent,
        insertcolor=p.text,
        focuscolor=p.accent,
        relief="flat",
    )

    # Containers
    style.configure("TFrame", background=p.bg)
    style.configure("Sidebar.TFrame", background=p.surface)
    style.configure("Card.TFrame", background=p.surface)
    style.configure("Divider.TFrame", background=p.border)

    # Text
    style.configure("TLabel", background=p.bg, foreground=p.text)
    style.configure("Muted.TLabel", foreground=p.text_muted)
    style.configure("Heading.TLabel", font=theme.heading)
    style.configure("Card.TLabel", background=p.surface)
    style.configure("Card.Muted.TLabel", background=p.surface, foreground=p.text_muted)
    style.configure(
        "Card.Caption.TLabel", background=p.surface, foreground=p.text_muted, font=theme.caption
    )
    style.configure("Card.Title.TLabel", background=p.surface, font=theme.title)
    style.configure("Card.Stat.TLabel", background=p.surface, font=theme.stat)
    style.configure(
        "Pill.TLabel", background=p.surface_alt, font=theme.body_bold, padding=(px(10), px(3))
    )

    # Buttons
    flat_button = {"lightcolor": p.surface_alt, "darkcolor": p.surface_alt}
    style.configure(
        "TButton",
        background=p.surface_alt,
        foreground=p.text,
        bordercolor=p.border,
        padding=(px(14), px(7)),
        font=theme.body_bold,
        anchor="center",
        **flat_button,
    )
    style.map(
        "TButton",
        background=[("disabled", p.surface), ("pressed", p.border), ("active", p.surface_hover)],
        lightcolor=[("disabled", p.surface), ("pressed", p.border), ("active", p.surface_hover)],
        darkcolor=[("disabled", p.surface), ("pressed", p.border), ("active", p.surface_hover)],
        foreground=[("disabled", p.text_faint)],
        bordercolor=[("disabled", p.surface_alt), ("focus", p.accent)],
    )
    style.configure(
        "Accent.TButton",
        background=p.accent,
        foreground=p.on_accent,
        bordercolor=p.accent,
        lightcolor=p.accent,
        darkcolor=p.accent,
    )
    style.map(
        "Accent.TButton",
        background=[
            ("disabled", p.accent_tint),
            ("pressed", p.accent_pressed),
            ("active", p.accent_hover),
        ],
        lightcolor=[
            ("disabled", p.accent_tint),
            ("pressed", p.accent_pressed),
            ("active", p.accent_hover),
        ],
        darkcolor=[
            ("disabled", p.accent_tint),
            ("pressed", p.accent_pressed),
            ("active", p.accent_hover),
        ],
        bordercolor=[
            ("disabled", p.accent_tint),
            ("focus", p.on_accent),
            ("pressed", p.accent_pressed),
            ("active", p.accent_hover),
        ],
        foreground=[("disabled", p.text_muted)],
    )

    # Segmented control: radio buttons drawn as a row of toggle buttons.
    style.configure(
        "Segment.Toolbutton",
        background=p.surface_alt,
        foreground=p.text_muted,
        bordercolor=p.surface_alt,
        padding=(px(12), px(6)),
        font=theme.body_bold,
        anchor="center",
        **flat_button,
    )
    style.map(
        "Segment.Toolbutton",
        background=[("selected", p.accent), ("active", p.surface_hover)],
        lightcolor=[("selected", p.accent), ("active", p.surface_hover)],
        darkcolor=[("selected", p.accent), ("active", p.surface_hover)],
        bordercolor=[("selected", p.accent), ("focus", p.accent)],
        foreground=[("disabled", p.text_faint), ("selected", p.on_accent), ("active", p.text)],
    )

    # Inputs
    style.configure("TEntry", padding=(px(10), px(6)), bordercolor=p.border, **flat_button)
    style.map(
        "TEntry",
        bordercolor=[("focus", p.accent)],
        lightcolor=[("focus", p.accent)],
        darkcolor=[("focus", p.accent)],
    )
    style.configure(
        "TCombobox",
        padding=(px(10), px(6)),
        background=p.surface_alt,
        foreground=p.text,
        arrowcolor=p.text_muted,
        bordercolor=p.border,
        arrowsize=px(12),
        **flat_button,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("disabled", p.surface), ("readonly", p.surface_alt)],
        background=[("disabled", p.surface), ("active", p.surface_hover)],
        foreground=[("disabled", p.text_faint), ("readonly", p.text)],
        selectbackground=[("readonly", p.surface_alt)],
        selectforeground=[("readonly", p.text)],
        bordercolor=[("focus", p.accent)],
        arrowcolor=[("disabled", p.text_faint), ("active", p.text)],
    )
    # Sliders: the sidebar's sit on cards, "Page." ones on the window background.
    _images.clear()
    _slider_style(style, theme, "Horizontal.TScale", p.surface)
    _slider_style(style, theme, "Page.Horizontal.TScale", p.bg)

    # History table
    row_height = tkfont.Font(root=root, font=theme.body).metrics("linespace") + px(14)
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure(
        "Treeview",
        background=p.surface,
        fieldbackground=p.surface,
        foreground=p.text,
        rowheight=row_height,
        borderwidth=0,
    )
    style.map(
        "Treeview", background=[("selected", p.accent_tint)], foreground=[("selected", p.text)]
    )
    style.configure(
        "Treeview.Heading",
        background=p.surface,
        foreground=p.text_muted,
        font=theme.caption,
        relief="flat",
        padding=(px(8), px(8)),
        bordercolor=p.surface,
        lightcolor=p.surface,
        darkcolor=p.surface,
    )
    style.map("Treeview.Heading", background=[("active", p.surface_alt)])

    # A thin scrollbar without arrow buttons
    style.layout(
        "Vertical.TScrollbar",
        [
            (
                "Vertical.Scrollbar.trough",
                {
                    "sticky": "ns",
                    "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})],
                },
            )
        ],
    )
    style.configure(
        "Vertical.TScrollbar",
        background=p.surface_hover,
        troughcolor=p.surface,
        bordercolor=p.surface,
        lightcolor=p.surface_hover,
        darkcolor=p.surface_hover,
        arrowsize=px(10),
        gripcount=0,
    )
    style.map("Vertical.TScrollbar", background=[("active", p.border)])

    return theme


def _rounded_rect(
    width: int, height: int, radius: float, color: str, background: str
) -> tk.PhotoImage:
    """Draw an anti-aliased rounded rectangle blended onto ``background``.

    Tk photo images only support on/off transparency, so edges are smoothed by
    mixing with the colour the shape will sit on.
    """
    fg, bg = _hex_to_rgb(color), _hex_to_rgb(background)
    samples = 4
    offsets = [(k + 0.5) / samples for k in range(samples)]
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            covered = 0
            for oy in offsets:
                dy = max(radius - (y + oy), 0, (y + oy) - (height - radius))
                for ox in offsets:
                    dx = max(radius - (x + ox), 0, (x + ox) - (width - radius))
                    covered += dx * dx + dy * dy <= radius * radius
            alpha = covered / samples**2
            row.append(
                "#{:02x}{:02x}{:02x}".format(
                    *(round(b + (f - b) * alpha) for f, b in zip(fg, bg, strict=True))
                )
            )
        rows.append("{" + " ".join(row) + "}")
    image = tk.PhotoImage(width=width, height=height)
    image.put(" ".join(rows))
    return image


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def _slider_style(style: ttk.Style, theme: Theme, name: str, background: str) -> None:
    """Style a horizontal ttk.Scale as a slim rounded track with a round knob.

    Clam paints the track outline and the knob in the same colour, so both
    are drawn as images, smoothed against the colour they will sit on.
    """
    p = PALETTE
    knob, track, track_width = theme.px(16), theme.px(4), theme.px(12)
    prefix = name.removesuffix("Horizontal.TScale").replace(".", "")
    images = [
        _rounded_rect(knob, knob, knob / 2, color, background)
        for color in (p.accent, p.accent_hover, p.border)
    ] + [
        _rounded_rect(track_width, track, track / 2, color, background)
        for color in (p.surface_hover, p.surface_alt)
    ]
    _images.extend(images)
    knob_normal, knob_hover, knob_disabled, track_normal, track_disabled = images

    slider, trough = (
        f"{prefix}Knob.Horizontal.Scale.slider",
        f"{prefix}Slim.Horizontal.Scale.trough",
    )
    style.element_create(
        slider, "image", knob_normal, ("disabled", knob_disabled), ("active", knob_hover)
    )
    style.element_create(
        trough,
        "image",
        track_normal,
        ("disabled", track_disabled),
        border=(theme.px(4), 0),
        sticky="ew",
    )
    style.layout(
        name,
        [(trough, {"sticky": "nswe", "children": [(slider, {"side": "left", "sticky": ""})]})],
    )
    style.configure(name, background=background)
    # Clam otherwise paints disabled widgets in its own light grey.
    style.map(name, background=[("disabled", background)])
