"""Convenience launcher so ``python main.py`` keeps working."""

from algorithm_visualizer.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
