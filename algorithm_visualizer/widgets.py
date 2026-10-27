"""Custom widgets."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Iterable

from .theme import PALETTE, Theme

# Value labels are drawn above the bars only when there is room for them.
_LABEL_MAX_BARS = 40
_LABEL_MIN_WIDTH = 18


class BarChart(tk.Canvas):
    """Draws a list of numbers as vertical bars and recolours them on demand.

    The chart keeps a reference to the list it is given, so after the list is
    changed in place call :meth:`refresh` with the indices that changed.
    """

    def __init__(self, master: tk.Misc, theme: Theme) -> None:
        super().__init__(master, background=PALETTE.surface, highlightthickness=0, borderwidth=0)
        self._theme = theme
        self._values: list[int] = []
        self._bars: list[int] = []
        self._labels: list[int] = []
        self._base_colors: list[str] = []
        self._highlights: dict[int, str] = {}
        self._low = 0
        self._span = 1
        self._sweep_job: str | None = None
        self._empty_text = self.create_text(
            0, 0, fill=PALETTE.text_muted, font=theme.body, text="Generate or load numbers to begin"
        )
        self.bind("<Configure>", lambda _event: self._layout())

    def set_values(self, values: list[int]) -> None:
        self._cancel_sweep()
        self.delete("bar", "label")
        self._values = values
        self._base_colors = [PALETTE.bar] * len(values)
        self._highlights = {}
        if values:
            self._low = min(0, min(values))
            self._span = max(1, max(0, max(values)) - self._low)
        self._bars = [
            self.create_rectangle(0, 0, 0, 0, width=0, fill=PALETTE.bar, tags="bar") for _ in values
        ]
        self._labels = [
            self.create_text(
                0, 0, fill=PALETTE.text_muted, font=self._theme.small, anchor="s", tags="label"
            )
            for _ in values
        ]
        self._layout()

    def refresh(self, indices: Iterable[int]) -> None:
        for i in indices:
            self._place(i)

    def highlight(self, colors: dict[int, str]) -> None:
        """Replace the current highlight with ``colors`` (index -> colour)."""
        for i in self._highlights.keys() - colors.keys():
            self.itemconfigure(self._bars[i], fill=self._base_colors[i])
        for i, color in colors.items():
            self.itemconfigure(self._bars[i], fill=color)
        self._highlights = dict(colors)

    def mark_sorted(self, i: int) -> None:
        self._base_colors[i] = PALETTE.sorted
        if i not in self._highlights:
            self.itemconfigure(self._bars[i], fill=PALETTE.sorted)

    def sweep(self, duration_ms: int = 450) -> None:
        """Animate every bar to the sorted colour from left to right."""
        self._cancel_sweep()
        self.highlight({})
        frames = max(1, duration_ms // 15)
        per_frame = max(1, -(-len(self._bars) // frames))

        def run(start: int) -> None:
            end = min(start + per_frame, len(self._bars))
            for i in range(start, end):
                self.mark_sorted(i)
            self._sweep_job = self.after(15, run, end) if end < len(self._bars) else None

        run(0)

    def _cancel_sweep(self) -> None:
        if self._sweep_job is not None:
            self.after_cancel(self._sweep_job)
            self._sweep_job = None

    def _layout(self) -> None:
        width, height = self.winfo_width(), self.winfo_height()
        self.coords(self._empty_text, width / 2, height / 2)
        self.itemconfigure(self._empty_text, state="hidden" if self._values else "normal")
        for i in range(len(self._values)):
            self._place(i)

    def _place(self, i: int) -> None:
        px = self._theme.px
        pad_x, pad_top, pad_bottom = px(24), px(28), px(20)
        width = max(1, self.winfo_width() - 2 * pad_x)
        plot_height = max(1, self.winfo_height() - pad_top - pad_bottom)
        n = len(self._values)

        slot = width / n
        gap = min(px(4), slot * 0.2) if slot >= 3 else 0
        x0 = pad_x + i * slot + gap / 2
        x1 = pad_x + (i + 1) * slot - gap / 2
        bottom = pad_top + plot_height
        bar_height = max(px(3), (self._values[i] - self._low) / self._span * plot_height)
        top = bottom - bar_height

        self.coords(self._bars[i], x0, top, x1, bottom)
        show_label = n <= _LABEL_MAX_BARS and slot >= px(_LABEL_MIN_WIDTH)
        self.coords(self._labels[i], (x0 + x1) / 2, top - px(4))
        self.itemconfigure(
            self._labels[i], text=self._values[i], state="normal" if show_label else "hidden"
        )
