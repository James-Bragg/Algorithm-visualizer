# Algorithm Visualizer

A desktop app that animates sorting algorithms one operation at a time, so you can see
every comparison, swap and write as it happens.

- **Six algorithms**: Bubble, Insertion, Selection, Merge, Quick and Heap sort, each with
  its time and space complexity shown alongside.
- **Your data or random data**: shuffle a random list, type numbers in, or open a `.txt`
  or `.csv` file. Numbers can be separated by spaces, commas, semicolons or new lines.
- **Full playback control**: start, pause, single-step, reset and adjust the speed.
- **Run history**: every completed sort is saved with its comparison count, move count and
  run time (measured without the animation). Double-click a past run to load its numbers again.

This software is for private use only and should not be used in any public or commercial use.

## Requirements

- Python 3.11 or newer, with Tkinter (included with the python.org installers on Windows
  and macOS; on Debian/Ubuntu install `python3-tk`)

There are no third-party runtime dependencies.

## Running

```sh
python -m algorithm_visualizer
```

`python main.py` also works. To keep history somewhere other than the default location,
pass `--db path/to/history.sqlite3`.

### Keyboard shortcuts

| Key      | Action        |
| -------- | ------------- |
| Space    | Start / pause |
| →        | Step once     |
| R        | Reset         |
| N        | Shuffle       |
| Ctrl+O   | Open a file   |

## Where history is stored

- **Windows:** `%APPDATA%\AlgorithmVisualizer\history.sqlite3`
- **macOS:** `~/Library/Application Support/AlgorithmVisualizer/history.sqlite3`
- **Linux:** `$XDG_DATA_HOME/AlgorithmVisualizer/history.sqlite3` (default `~/.local/share`)

On first start, runs recorded by the original version of this app in `SQLDB.sqlite3` are
imported automatically. After that the old file is no longer used and can be deleted.

## Project layout

```text
algorithm_visualizer/
  algorithms.py   sorting algorithms as step generators (no UI code)
  data.py         parsing and generating lists of numbers
  storage.py      SQLite run history
  theme.py        colours, fonts and ttk styles
  widgets.py      the animated bar chart
  app.py          the main window
examples/         sample input files
tests/            pytest suite
```

## Development

```sh
python -m venv .venv
.venv\Scripts\activate          # or: source .venv/bin/activate
pip install -e ".[dev]"

pytest                          # run the tests
ruff format .                   # format
ruff check .                    # lint
```

### Adding an algorithm

Write a generator in `algorithms.py` that sorts a list in place and yields a `Step` for
each comparison (`Op.COMPARE`), swap (`Op.SWAP`) or write (`Op.WRITE`), plus `Op.SORTED`
when an index reaches its final position. Register it in `ALGORITHMS` and the UI and tests
pick it up automatically.
