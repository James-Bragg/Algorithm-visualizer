"""The main application window."""

from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .algorithms import ALGORITHMS, Op, Step, measure
from .data import MAX_SIZE, MIN_SIZE, load_numbers, parse_numbers, random_values
from .storage import HistoryStore, Run
from .theme import PALETTE, apply_theme, enable_dpi_awareness, use_dark_title_bar
from .widgets import BarChart

# Databases written by the original version of the app lived in the project root.
LEGACY_DB_PATH = Path(__file__).resolve().parent.parent / "SQLDB.sqlite3"

# Speed slider position -> (milliseconds between frames, steps per frame).
SPEEDS = (
    (240, 1),
    (120, 1),
    (60, 1),
    (30, 1),
    (16, 1),
    (16, 2),
    (16, 4),
    (16, 8),
    (16, 16),
    (16, 48),
)
DEFAULT_SPEED = 6
DEFAULT_SIZE = 40

STEP_COLORS = {Op.COMPARE: PALETTE.compare, Op.SWAP: PALETTE.swap, Op.WRITE: PALETTE.write}

# Widgets that handle these keys themselves; global shortcuts are ignored while
# one of them has focus.
_KEY_CONSUMERS = {"TEntry", "TCombobox", "TScale", "Treeview", "TButton", "TRadiobutton"}


class State(Enum):
    READY = ("Ready", PALETTE.text_muted)
    RUNNING = ("Sorting", PALETTE.accent_hover)
    PAUSED = ("Paused", PALETTE.compare)
    DONE = ("Sorted", PALETTE.sorted)

    def __init__(self, label: str, color: str) -> None:
        self.label = label
        self.color = color


class App:
    def __init__(self, root: tk.Tk, store: HistoryStore) -> None:
        self.root = root
        self.store = store
        self.theme = apply_theme(root)

        self.state = State.READY
        self.values: list[int] = []
        self.original: list[int] = []
        self.comparisons = 0
        self.moves = 0
        self._steps: Iterator[Step] | None = None
        self._job: str | None = None
        self._runs: dict[str, Run] = {}

        self.algorithm = tk.StringVar(value="Bubble Sort")
        self.ascending = tk.BooleanVar(value=True)
        self.size = tk.IntVar(value=DEFAULT_SIZE)
        self.speed = tk.IntVar(value=DEFAULT_SPEED)
        self.page = tk.StringVar(value="visualizer")
        self.custom_numbers = tk.StringVar()

        self._configure_window()
        self._build()
        self._bind_shortcuts()

        self.algorithm.trace_add("write", lambda *_: self._on_settings_changed())
        self.ascending.trace_add("write", lambda *_: self._on_settings_changed())

        self.set_values(random_values(DEFAULT_SIZE))
        self.refresh_history()

    # ----------------------------------------------------------------- layout

    def _configure_window(self) -> None:
        px = self.theme.px
        root = self.root
        root.title("Algorithm Visualizer")
        width, height = px(1240), px(780)
        x = max(0, (root.winfo_screenwidth() - width) // 2)
        y = max(0, (root.winfo_screenheight() - height) // 3)
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._icon = _make_icon()
        root.iconphoto(True, self._icon)
        use_dark_title_bar(root)

    def _build(self) -> None:
        sidebar = self._build_sidebar()
        sidebar.grid(row=0, column=0, sticky="nsew")
        self._build_main().grid(row=0, column=1, sticky="nsew")
        # Never let the window get short enough to clip the sidebar controls.
        self.root.update_idletasks()
        self.root.minsize(self.theme.px(980), max(self.theme.px(620), sidebar.winfo_reqheight()))

    def _build_sidebar(self) -> ttk.Frame:
        px = self.theme.px
        sidebar = ttk.Frame(self.root, style="Sidebar.TFrame", padding=(px(24), px(24)))
        sidebar.columnconfigure(0, weight=1)
        sidebar.columnconfigure(1, weight=1)
        wrap = px(262)
        row = _RowCounter()

        brand = ttk.Frame(sidebar, style="Card.TFrame")
        brand.grid(row=row.next(), column=0, columnspan=2, sticky="ew")
        ttk.Label(brand, image=self._icon, style="Card.TLabel").grid(
            row=0, column=0, rowspan=2, padx=(0, px(12))
        )
        ttk.Label(brand, text="Algorithm Visualizer", style="Card.Title.TLabel").grid(
            row=0, column=1, sticky="w"
        )
        ttk.Label(brand, text="Sorting, one step at a time", style="Card.Muted.TLabel").grid(
            row=1, column=1, sticky="w"
        )

        # Algorithm
        self._caption(sidebar, "ALGORITHM", row.next(), top=px(28))
        self.algorithm_box = ttk.Combobox(
            sidebar, textvariable=self.algorithm, values=list(ALGORITHMS), state="readonly"
        )
        self.algorithm_box.grid(row=row.next(), column=0, columnspan=2, sticky="ew")
        self.algorithm_box.bind(
            "<<ComboboxSelected>>", lambda _e: self.algorithm_box.selection_clear()
        )
        self.summary = ttk.Label(
            sidebar, style="Card.Muted.TLabel", wraplength=wrap, justify="left"
        )
        self.summary.grid(row=row.next(), column=0, columnspan=2, sticky="w", pady=(px(10), 0))
        complexity = ttk.Frame(sidebar, style="Card.TFrame")
        complexity.grid(row=row.next(), column=0, columnspan=2, sticky="ew", pady=(px(12), 0))
        self.complexity: dict[str, ttk.Label] = {}
        for column, case in enumerate(("best", "average", "worst")):
            complexity.columnconfigure(column, weight=1, uniform="complexity")
            ttk.Label(complexity, text=case.upper(), style="Card.Caption.TLabel").grid(
                row=0, column=column, sticky="w"
            )
            self.complexity[case] = ttk.Label(complexity, style="Card.TLabel")
            self.complexity[case].grid(row=1, column=column, sticky="w")
        self.traits = ttk.Label(sidebar, style="Card.Muted.TLabel", font=self.theme.small)
        self.traits.grid(row=row.next(), column=0, columnspan=2, sticky="w", pady=(px(6), 0))

        # Order
        self._caption(sidebar, "ORDER", row.next())
        order = ttk.Frame(sidebar, style="Card.TFrame")
        order.grid(row=row.next(), column=0, columnspan=2, sticky="ew")
        self.order_buttons = []
        for column, (text, value) in enumerate((("Ascending", True), ("Descending", False))):
            order.columnconfigure(column, weight=1, uniform="order")
            button = ttk.Radiobutton(
                order, text=text, value=value, variable=self.ascending, style="Segment.Toolbutton"
            )
            button.grid(row=0, column=column, sticky="ew")
            self.order_buttons.append(button)

        # Data
        self._caption(sidebar, "DATA", row.next())
        self.size_label = self._labelled_value(sidebar, "Size", row.next())
        self.size_scale = ttk.Scale(
            sidebar,
            from_=MIN_SIZE,
            to=MAX_SIZE,
            variable=self.size,
            command=lambda _v: self._on_size_changed(),
        )
        self.size_scale.grid(
            row=row.next(), column=0, columnspan=2, sticky="ew", pady=(px(4), px(12))
        )
        data_row = row.next()
        self.shuffle_button = ttk.Button(sidebar, text="Shuffle", command=self.shuffle)
        self.shuffle_button.grid(row=data_row, column=0, sticky="ew", padx=(0, px(4)))
        self.open_button = ttk.Button(sidebar, text="Open file…", command=self.open_file)
        self.open_button.grid(row=data_row, column=1, sticky="ew", padx=(px(4), 0))
        ttk.Label(
            sidebar, text="Or type your own, then press Enter", style="Card.Muted.TLabel"
        ).grid(row=row.next(), column=0, columnspan=2, sticky="w", pady=(px(14), px(6)))
        self.custom_entry = ttk.Entry(sidebar, textvariable=self.custom_numbers)
        self.custom_entry.grid(row=row.next(), column=0, columnspan=2, sticky="ew")
        self.custom_entry.bind("<Return>", lambda _e: self.apply_custom_numbers())

        sidebar.rowconfigure(row.next(), weight=1)
        self._caption(sidebar, "SHORTCUTS", row.next())
        shortcuts = ttk.Frame(sidebar, style="Card.TFrame")
        shortcuts.grid(row=row.next(), column=0, columnspan=2, sticky="ew")
        for index, (keys, action) in enumerate(
            (
                ("Space", "Start / pause"),
                ("→", "Step"),
                ("R", "Reset"),
                ("N", "Shuffle"),
                ("Ctrl+O", "Open file"),
            )
        ):
            line, column = divmod(index, 2)
            shortcuts.columnconfigure(column * 2 + 1, weight=1)
            ttk.Label(shortcuts, text=keys, style="Card.TLabel", font=self.theme.small).grid(
                row=line, column=column * 2, sticky="w", padx=(0, px(8)), pady=px(1)
            )
            ttk.Label(
                shortcuts, text=action, style="Card.Muted.TLabel", font=self.theme.small
            ).grid(row=line, column=column * 2 + 1, sticky="w")

        self._locked_while_sorting = [
            self.algorithm_box,
            *self.order_buttons,
            self.size_scale,
            self.shuffle_button,
            self.open_button,
            self.custom_entry,
        ]
        self._on_size_changed(regenerate=False)
        return sidebar

    def _build_main(self) -> ttk.Frame:
        px = self.theme.px
        main = ttk.Frame(self.root, padding=(px(32), px(24), px(32), px(28)))
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        header = ttk.Frame(main)
        header.grid(row=0, column=0, sticky="ew", pady=(0, px(20)))
        header.columnconfigure(0, weight=1)
        title_row = ttk.Frame(header)
        title_row.grid(row=0, column=0, sticky="w")
        self.heading = ttk.Label(title_row, style="Heading.TLabel")
        self.heading.grid(row=0, column=0, sticky="w")
        self.status = ttk.Label(title_row, style="Pill.TLabel")
        self.status.grid(row=0, column=1, sticky="w", padx=(px(14), 0))
        self.subheading = ttk.Label(header, style="Muted.TLabel")
        self.subheading.grid(row=1, column=0, sticky="w", pady=(px(2), 0))

        tabs = ttk.Frame(header)
        tabs.grid(row=0, column=1, rowspan=2, sticky="e")
        for column, (text, value) in enumerate(
            (("Visualizer", "visualizer"), ("History", "history"))
        ):
            ttk.Radiobutton(
                tabs,
                text=text,
                value=value,
                variable=self.page,
                style="Segment.Toolbutton",
                command=self._show_page,
            ).grid(row=0, column=column)

        self.pages = {
            "visualizer": self._build_visualizer(main),
            "history": self._build_history(main),
        }
        for page in self.pages.values():
            page.grid(row=1, column=0, sticky="nsew")
        self._show_page()
        return main

    def _build_visualizer(self, parent: ttk.Frame) -> ttk.Frame:
        px = self.theme.px
        page = ttk.Frame(parent)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(page)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, px(16)))
        toolbar.columnconfigure(3, weight=1)
        self.play_button = ttk.Button(
            toolbar, text="Start", width=9, style="Accent.TButton", command=self.toggle_play
        )
        self.play_button.grid(row=0, column=0, padx=(0, px(8)))
        self.step_button = ttk.Button(toolbar, text="Step", command=self.step_once)
        self.step_button.grid(row=0, column=1, padx=(0, px(8)))
        self.reset_button = ttk.Button(toolbar, text="Reset", command=self.reset)
        self.reset_button.grid(row=0, column=2)
        ttk.Label(toolbar, text="Speed", style="Muted.TLabel").grid(
            row=0, column=4, padx=(0, px(12))
        )
        ttk.Scale(
            toolbar,
            from_=1,
            to=len(SPEEDS),
            length=px(180),
            variable=self.speed,
            style="Page.Horizontal.TScale",
        ).grid(row=0, column=5)
        self.speed_label = ttk.Label(toolbar, style="Muted.TLabel", width=6, anchor="e")
        self.speed_label.grid(row=0, column=6)
        self.speed.trace_add("write", lambda *_: self._on_speed_changed())
        self._on_speed_changed()

        card = ttk.Frame(page, style="Card.TFrame", padding=px(8))
        card.grid(row=1, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)
        self.chart = BarChart(card, self.theme)
        self.chart.grid(row=0, column=0, sticky="nsew")

        legend = ttk.Frame(card, style="Card.TFrame", padding=(px(16), px(4), px(16), px(8)))
        legend.grid(row=1, column=0, sticky="w")
        for column, (text, color) in enumerate(
            (
                ("Compare", PALETTE.compare),
                ("Swap", PALETTE.swap),
                ("Write", PALETTE.write),
                ("Sorted", PALETTE.sorted),
            )
        ):
            ttk.Label(legend, text="■", foreground=color, style="Card.TLabel").grid(
                row=0, column=2 * column, padx=(0 if column == 0 else px(18), px(6))
            )
            ttk.Label(legend, text=text, style="Card.Muted.TLabel").grid(
                row=0, column=2 * column + 1
            )

        stats = ttk.Frame(page)
        stats.grid(row=2, column=0, sticky="ew", pady=(px(16), 0))
        self.stat_values: dict[str, ttk.Label] = {}
        for column, name in enumerate(("Comparisons", "Moves", "Elements", "Run time")):
            stats.columnconfigure(column, weight=1, uniform="stats")
            tile = ttk.Frame(stats, style="Card.TFrame", padding=(px(18), px(14)))
            tile.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else px(8), 0))
            ttk.Label(tile, text=name.upper(), style="Card.Caption.TLabel").grid(
                row=0, column=0, sticky="w"
            )
            value = ttk.Label(tile, text="—", style="Card.Stat.TLabel")
            value.grid(row=1, column=0, sticky="w", pady=(px(4), 0))
            self.stat_values[name] = value
        return page

    def _build_history(self, parent: ttk.Frame) -> ttk.Frame:
        px = self.theme.px
        page = ttk.Frame(parent, style="Card.TFrame", padding=(px(20), px(16)))
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(page, style="Card.TFrame")
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, px(12)))
        toolbar.columnconfigure(1, weight=1)
        ttk.Label(toolbar, text="Run history", style="Card.Title.TLabel").grid(row=0, column=0)
        self.history_count = ttk.Label(toolbar, style="Card.Muted.TLabel")
        self.history_count.grid(row=0, column=1, sticky="w", padx=(px(10), 0))
        self.load_run_button = ttk.Button(
            toolbar, text="Load numbers", command=self.load_selected_run
        )
        self.load_run_button.grid(row=0, column=2, padx=(0, px(8)))
        self.clear_button = ttk.Button(toolbar, text="Clear history", command=self.clear_history)
        self.clear_button.grid(row=0, column=3)

        columns = {
            "when": ("WHEN", 150, "w"),
            "algorithm": ("ALGORITHM", 140, "w"),
            "order": ("ORDER", 100, "w"),
            "size": ("SIZE", 70, "e"),
            "comparisons": ("COMPARISONS", 120, "e"),
            "moves": ("MOVES", 90, "e"),
            "time": ("RUN TIME", 100, "e"),
        }
        self.tree = ttk.Treeview(page, columns=list(columns), show="headings", selectmode="browse")
        for key, (title, width, anchor) in columns.items():
            self.tree.heading(key, text=title, anchor=anchor)
            self.tree.column(
                key, width=px(width), minwidth=px(60), anchor=anchor, stretch=key == "algorithm"
            )
        self.tree.tag_configure("odd", background=PALETTE.bg)
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda _e: self.load_selected_run())
        self.tree.bind("<Return>", lambda _e: self.load_selected_run())
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_history_buttons())
        scrollbar = ttk.Scrollbar(page, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(px(6), 0))
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.history_empty = ttk.Label(
            page,
            style="Card.Muted.TLabel",
            justify="center",
            text="No runs yet.\nFinish a sort and it will be recorded here.",
        )
        return page

    def _caption(self, parent: ttk.Frame, text: str, row: int, top: int | None = None) -> None:
        px = self.theme.px
        ttk.Label(parent, text=text, style="Card.Caption.TLabel").grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(px(22) if top is None else top, px(8)),
        )

    def _labelled_value(self, parent: ttk.Frame, text: str, row: int) -> ttk.Label:
        ttk.Label(parent, text=text, style="Card.TLabel").grid(row=row, column=0, sticky="w")
        value = ttk.Label(parent, style="Card.Muted.TLabel")
        value.grid(row=row, column=1, sticky="e")
        return value

    def _bind_shortcuts(self) -> None:
        shortcuts = {
            "<space>": self.toggle_play,
            "<Right>": self.step_once,
            "<KeyPress-r>": self.reset,
            "<KeyPress-n>": self.shuffle,
            "<Control-o>": self.open_file,
        }
        for sequence, action in shortcuts.items():
            self.root.bind(sequence, lambda event, action=action: self._shortcut(event, action))

    def _shortcut(self, event: tk.Event, action) -> None:
        focused_input = (
            isinstance(event.widget, tk.Misc) and event.widget.winfo_class() in _KEY_CONSUMERS
        )
        if focused_input and event.keysym != "o":  # Ctrl+O works everywhere
            return
        action()

    # ------------------------------------------------------------------ data

    def set_values(self, values: list[int]) -> None:
        """Replace the data being sorted and reset the visualizer."""
        self._stop()
        self.original = list(values)
        self.values = list(values)
        self.chart.set_values(self.values)
        self._set_state(State.READY)
        self._reset_stats()
        self._refresh_labels()

    def shuffle(self) -> None:
        if self._unlocked():
            self.set_values(random_values(self.size.get()))

    def open_file(self) -> None:
        if not self._unlocked():
            return
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Open a list of numbers",
            filetypes=(("Text files", "*.txt *.csv"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            values = load_numbers(path)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            messagebox.showerror("Couldn't open file", _describe(error), parent=self.root)
            return
        self.set_values(values)

    def apply_custom_numbers(self) -> None:
        if not self._unlocked():
            return
        try:
            values = parse_numbers(self.custom_numbers.get())
        except ValueError as error:
            messagebox.showerror("Couldn't use those numbers", str(error), parent=self.root)
            return
        self.set_values(values)

    def _on_size_changed(self, regenerate: bool = True) -> None:
        size = round(float(self.size.get()))
        self.size_label.configure(text=str(size))
        if regenerate and size != len(self.values) and self._unlocked():
            self.set_values(random_values(size))

    def _on_speed_changed(self) -> None:
        speed = round(float(self.speed.get()))
        self.speed_label.configure(text=f"{speed} / {len(SPEEDS)}")

    def _on_settings_changed(self) -> None:
        if self.state is State.DONE:
            self.reset()
        self._refresh_labels()

    # -------------------------------------------------------------- playback

    def toggle_play(self) -> None:
        if self.state is State.RUNNING:
            self._stop()
            self._set_state(State.PAUSED)
            return
        if self.state is State.DONE:
            self.reset()
        if not self.values:
            return
        if self.state is State.READY:
            self._begin()
        self._set_state(State.RUNNING)
        self._tick()

    def step_once(self) -> None:
        if self.state is State.DONE or not self.values:
            return
        self._stop()
        if self.state is State.READY:
            self._begin()
        self._set_state(State.PAUSED)
        self._advance(1)

    def reset(self) -> None:
        self.set_values(self.original)

    def _begin(self) -> None:
        sort = ALGORITHMS[self.algorithm.get()].sort
        self._steps = sort(self.values, self.ascending.get())
        self._reset_stats()

    def _tick(self) -> None:
        delay, steps = SPEEDS[round(float(self.speed.get())) - 1]
        if self._advance(steps):
            self._job = self.root.after(delay, self._tick)

    def _advance(self, count: int) -> bool:
        """Apply up to ``count`` steps. Returns False once the sort has finished."""
        assert self._steps is not None
        changed: set[int] = set()
        last: Step | None = None
        finished = False
        for _ in range(count):
            step = next(self._steps, None)
            if step is None:
                finished = True
                break
            if step.op is Op.COMPARE:
                self.comparisons += 1
            elif step.op is Op.SORTED:
                self.chart.mark_sorted(step.i)
                continue
            else:
                self.moves += 1
                changed.update((step.i, step.j) if step.op is Op.SWAP else (step.i,))
            last = step

        self.chart.refresh(changed)
        if finished:
            self._finish()
            return False
        if last is not None:
            color = STEP_COLORS[last.op]
            self.chart.highlight({i: color for i in (last.i, last.j) if i >= 0})
        self._update_live_stats()
        return True

    def _finish(self) -> None:
        self._job = None
        self._steps = None
        self.chart.sweep()
        self._set_state(State.DONE)

        algorithm = self.algorithm.get()
        stats = measure(ALGORITHMS[algorithm].sort, self.original, self.ascending.get())
        duration_ms = stats.seconds * 1000
        self._update_live_stats()
        self.stat_values["Run time"].configure(text=_format_ms(duration_ms))
        try:
            self.store.add(
                algorithm,
                self.original,
                self.ascending.get(),
                stats.comparisons,
                stats.moves,
                duration_ms,
            )
        except Exception as error:
            messagebox.showwarning("Run not saved", _describe(error), parent=self.root)
        self.refresh_history()

    def _stop(self) -> None:
        if self._job is not None:
            self.root.after_cancel(self._job)
            self._job = None

    def _set_state(self, state: State) -> None:
        self.state = state
        self.status.configure(text=state.label, foreground=state.color)
        self.play_button.configure(
            text={
                State.READY: "Start",
                State.RUNNING: "Pause",
                State.PAUSED: "Resume",
                State.DONE: "Replay",
            }[state]
        )
        unlocked = self._unlocked()
        for widget in self._locked_while_sorting:
            widget.state(["!disabled"] if unlocked else ["disabled"])
        if unlocked:
            self.algorithm_box.state(["readonly"])
        self.step_button.state(["!disabled"] if state is not State.DONE else ["disabled"])

    def _unlocked(self) -> bool:
        return self.state in (State.READY, State.DONE)

    # ----------------------------------------------------------------- stats

    def _reset_stats(self) -> None:
        self.comparisons = self.moves = 0
        self._update_live_stats()
        self.stat_values["Run time"].configure(text="—")

    def _update_live_stats(self) -> None:
        self.stat_values["Comparisons"].configure(text=f"{self.comparisons:,}")
        self.stat_values["Moves"].configure(text=f"{self.moves:,}")
        self.stat_values["Elements"].configure(text=f"{len(self.values):,}")

    def _refresh_labels(self) -> None:
        algorithm = ALGORITHMS[self.algorithm.get()]
        order = "ascending" if self.ascending.get() else "descending"
        self.heading.configure(text=algorithm.name)
        self.subheading.configure(text=f"{len(self.values)} numbers, {order}")
        self.summary.configure(text=algorithm.summary)
        for case, label in self.complexity.items():
            label.configure(text=getattr(algorithm, case))
        stable = "Stable" if algorithm.stable else "Not stable"
        self.traits.configure(text=f"{stable}  ·  {algorithm.space} extra space")

    # --------------------------------------------------------------- history

    def _show_page(self) -> None:
        self.pages[self.page.get()].tkraise()

    def refresh_history(self) -> None:
        self.tree.delete(*self.tree.get_children())
        runs = self.store.runs()
        self._runs = {str(run.id): run for run in runs}
        for index, run in enumerate(runs):
            self.tree.insert(
                "",
                "end",
                iid=str(run.id),
                tags=("odd",) if index % 2 else (),
                values=_run_columns(run),
            )
        total = self.store.count()
        self.history_count.configure(text=f"{total:,} run{'s' if total != 1 else ''}")
        if runs:
            self.history_empty.place_forget()
        else:
            self.history_empty.place(relx=0.5, rely=0.5, anchor="center")
        self.clear_button.state(["!disabled"] if runs else ["disabled"])
        self._update_history_buttons()

    def _update_history_buttons(self) -> None:
        self.load_run_button.state(["!disabled"] if self.tree.selection() else ["disabled"])

    def load_selected_run(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        run = self._runs[selection[0]]
        if run.algorithm in ALGORITHMS:
            self.algorithm.set(run.algorithm)
        if run.ascending is not None:
            self.ascending.set(run.ascending)
        self.set_values(list(run.numbers))
        self.page.set("visualizer")
        self._show_page()

    def clear_history(self) -> None:
        if messagebox.askyesno(
            "Clear history",
            "Delete every recorded run? This can't be undone.",
            icon="warning",
            parent=self.root,
        ):
            self.store.clear()
            self.refresh_history()

    def close(self) -> None:
        self._stop()
        self.root.destroy()


class _RowCounter:
    def __init__(self) -> None:
        self._row = -1

    def next(self) -> int:
        self._row += 1
        return self._row


def _run_columns(run: Run) -> tuple[str, ...]:
    when = run.created_at.astimezone().strftime("%d %b %Y, %H:%M") if run.created_at else "—"
    order = {True: "Ascending", False: "Descending", None: "—"}[run.ascending]
    return (
        when,
        run.algorithm,
        order,
        f"{len(run.numbers):,}",
        "—" if run.comparisons is None else f"{run.comparisons:,}",
        "—" if run.moves is None else f"{run.moves:,}",
        "—" if run.duration_ms is None else _format_ms(run.duration_ms),
    )


def _format_ms(ms: float) -> str:
    return f"{ms:.2f} ms" if ms < 10 else f"{ms:,.0f} ms"


def _describe(error: BaseException) -> str:
    if isinstance(error, UnicodeDecodeError):
        return "The file isn't a plain text file."
    if isinstance(error, OSError) and error.strerror:
        return error.strerror
    return str(error)


def _make_icon() -> tk.PhotoImage:
    """Draw a small bar-chart logo so the app doesn't need an image file."""
    size = 32
    icon = tk.PhotoImage(width=size, height=size)
    icon.put(PALETTE.accent_tint, to=(0, 0, size, size))
    colors = (PALETTE.bar, PALETTE.accent, PALETTE.bar, PALETTE.sorted, PALETTE.accent)
    for i, (height, color) in enumerate(zip((10, 18, 13, 24, 20), colors, strict=True)):
        x = 4 + i * 5
        icon.put(color, to=(x, size - 4 - height, x + 4, size - 4))
    return icon


def run(db_path: Path) -> int:
    enable_dpi_awareness()
    root = tk.Tk(className="AlgorithmVisualizer")
    with HistoryStore(db_path) as store:
        # Old data is a bonus, never a reason not to start.
        with contextlib.suppress(Exception):
            store.import_legacy(LEGACY_DB_PATH)
        App(root, store)
        root.mainloop()
    return 0
