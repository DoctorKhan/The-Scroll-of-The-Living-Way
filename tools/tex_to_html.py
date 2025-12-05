#!/usr/bin/env python3
import re
import sys
from pathlib import Path


SECTION_RE = re.compile(r"^\\section\{([^}]*)\}")
CHAPTER_RE = re.compile(r"^\\chapter\{([^}]*)\}")


def slugify(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "saying"


def tex_to_html(tex_path: Path, html_path: Path) -> None:
    lines = tex_path.read_text(encoding="utf-8").splitlines()

    title = ""
    subtitle = ""
    in_titlepage = False
    say_num = 0

    books = []  # list of (book_title, preface_lines, sayings)
    current_book = None
        current_block_lines = []

        def flush_block_into_saying(saying):
            """Attach accumulated body lines to the given saying, preserving line breaks."""
            nonlocal current_block_lines
            if not current_block_lines or saying is None:
                current_block_lines = []
                return
            paragraphs = []
            buff = []
            for ln in current_block_lines:
                stripped = ln.rstrip()
                if stripped == "":
                    if buff:
                        paragraphs.append("<br>".join(buff).strip())
                        buff = []
                else:
                    # strip trailing LaTeX linebreaks \\ and comments
                    stripped = re.sub(r"\\\\\s*$", "", stripped)
                    # normalize TeX-style double backticks / single quotes to plain quotes
                    stripped = stripped.replace("``", "\"").replace("''", "\"")
                    # ignore bare ornament commands
                    if stripped.strip() == "\\ornament":
                        continue
                    buff.append(stripped)
            if buff:
                paragraphs.append("<br>".join(buff).strip())
            saying["paragraphs"] = paragraphs
            current_block_lines = []

    def flush_block_into_saying():
        """Convert accumulated TeX body lines into HTML paragraphs, preserving line breaks."""
        nonlocal current_block_lines
        if not current_block_lines:
            return None
        paragraphs = []
        buff = []
        for ln in current_block_lines:
            stripped = ln.rstrip()
            if stripped == "":
                if buff:
                    paragraphs.append("<br>".join(buff).strip())
                    buff = []
            else:
                # strip trailing LaTeX linebreaks \\ and comments
                stripped = re.sub(r"\\\\\s*$", "", stripped)
                # normalize TeX-style double backticks / single quotes to plain quotes
                stripped = stripped.replace("``", "\"").replace("''", "\"")
                buff.append(stripped)
        if buff:
            paragraphs.append("<br>".join(buff).strip())
        current_block_lines = []
        return paragraphs

    def start_new_book(ch_title: str):
        nonlocal current_book
        if current_book is not None:
            books.append(current_book)
        current_book = {"title": ch_title, "preface": [], "sayings": []}
            current_saying = None

    in_front_matter = True

    for raw in lines:
        line = raw.rstrip("\n")

        # crude titlepage parsing
        if line.strip().startswith("\\begin{titlepage}"):
            in_titlepage = True
            continue
        if line.strip().startswith("\\end{titlepage}"):
            in_titlepage = False
            continue
        if in_titlepage:
            # Capture main title line
            if "\\Huge" in line and "textsc" in line:
                m = re.findall(r"\\textsc\{([^}]*)\}", line)
                if m:
                    title = " ".join(m)
            # Capture subtitle text between { and }
            if "The 81 Sayings of" in line or "Book of Awakening" in line or "Suttas of the Living Buddha" in line:
                m = re.search(r"\{([^}]*)\}", line)
                if m:
                    subtitle = m.group(1).strip()
            continue

        # ignore everything before mainmatter
        if line.strip().startswith("\\mainmatter"):
            in_front_matter = False
            continue
        if in_front_matter:
            continue

        ch_m = CHAPTER_RE.match(line)
        if ch_m:
              # starting new book: flush any dangling text into previous saying
              flush_block_into_saying(current_saying)
            start_new_book(ch_m.group(1).strip())
            continue

        sec_m = SECTION_RE.match(line)
        if sec_m:
                # starting new saying: first flush body into previous saying
                flush_block_into_saying(current_saying)
            say_num += 1
            if current_book is None:
                start_new_book("")
                current_saying = {
                "num": say_num,
                "title": sec_m.group(1).strip(),
                "paragraphs": [],
                }
                current_book["sayings"].append(current_saying)
            continue

        # ornament or back matter enders
        # ornament-only lines should not become content
        if line.strip() == "\\ornament":
            continue

        # back matter marker: stop collecting sayings
        if line.strip().startswith("% --- BACK MATTER ---"):
            break

        # accumulate content
        if current_book is not None:
            current_block_lines.append(line)

    # flush last saying
    # flush last saying
    flush_block_into_saying(current_saying)
    if current_book is not None:
        books.append(current_book)

    # build HTML
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html lang=\"en\">")
    parts.append("<head>")
    parts.append("  <meta charset=\"utf-8\">")
    parts.append(f"  <title>{tex_path.stem}</title>")
    parts.append("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
    parts.append("  <style>body{font-family:serif;max-width:40rem;margin:2rem auto;padding:0 1rem;line-height:1.5;}h1,h2,h3{text-align:center;}h3{text-align:left;margin-top:2rem;}p{margin:0.4rem 0;}hr{margin:2rem 0;border:0;border-top:1px solid #ccc;}</style>")
    parts.append("</head>")
    parts.append("<body>")

    if title:
        parts.append(f"<h1>{title}</h1>")
    else:
        parts.append(f"<h1>{tex_path.stem}</h1>")
    if subtitle:
        parts.append(f"<h2>{subtitle}</h2>")

    for book in books:
        if book["title"]:
            parts.append(f"<h2>{book['title']}</h2>")
        for saying in book["sayings"]:
            num = saying["num"]
            stitle = saying["title"]
            sid = f"s{num}-{slugify(stitle)}"
            parts.append(f"<h3 id=\"{sid}\">{num}. {stitle}</h3>")
            for para in saying["paragraphs"]:
                # convert LaTeX line-break style ' \\' we already collapsed into sentences
                parts.append(f"<p>{para}</p>")
        parts.append("<hr>")

    parts.append("</body>")
    parts.append("</html>")

    html_path.write_text("\n".join(parts), encoding="utf-8")


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
