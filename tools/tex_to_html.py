#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def tex_to_html(tex_path: Path, html_path: Path) -> None:
    """Convert a LaTeX file to HTML using Pandoc.

    This delegates all formatting (including \textbf, \emph, sections, etc.)
    to Pandoc instead of maintaining a custom LaTeX parser here.
    """

    cmd = [
        "pandoc",
        "-s",  # standalone HTML (includes <html>, <head>, etc.)
        "--from=latex",
        "--to=html",
        str(tex_path),
        "-o",
        str(html_path),
    ]

    subprocess.run(cmd, check=True)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        # No explicit files: process all .tex files in CWD
        tex_files = sorted(Path(".").glob("*.tex"))
        if not tex_files:
            print("No .tex files found.", file=sys.stderr)
            return 1
    else:
        tex_files = [Path(arg) for arg in argv]

    for tex_path in tex_files:
        if not tex_path.exists():
            print(f"Skipping missing {tex_path}", file=sys.stderr)
            continue
        # Use the .tex stem directly for HTML filename, e.g. The_Living_Way.tex -> The_Living_Way.html
        html_name = tex_path.stem + ".html"
        html_path = tex_path.parent / html_name
        tex_to_html(tex_path, html_path)
        print(f"Wrote {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
