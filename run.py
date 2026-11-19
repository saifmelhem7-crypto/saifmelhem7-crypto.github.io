#!/usr/bin/env python3
"""Site helper. Usage: python run.py check"""
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors, self.links, self.title = [], [], [], False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.title = True
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.links.append(value)
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag not in (t for t, _ in self.stack):
            self.errors.append(f"line {self.getpos()[0]}: stray </{tag}>")
            return
        while self.stack:
            open_tag, line = self.stack.pop()
            if open_tag == tag:
                break
            if open_tag not in ("p", "li"):  # implicitly closable
                self.errors.append(f"line {line}: <{open_tag}> not closed")


def check():
    pages = sorted(ROOT.glob("*.html"))
    failed = 0
    for page in pages:
        p = Checker()
        p.feed(page.read_text(encoding="utf-8"))
        errors = p.errors + [f"line {l}: <{t}> not closed"
                             for t, l in p.stack if t not in ("p", "li")]
        if not p.title:
            errors.append("missing <title>")
        for link in p.links:
            if link.startswith(("http://", "https://", "mailto:", "#", "//")):
                continue
            target = link.split("#")[0].split("?")[0]
            if target and not (ROOT / target).exists():
                errors.append(f"broken local link: {link}")
        status = "OK" if not errors else "FAIL"
        print(f"[{status}] {page.name}")
        for e in errors:
            print(f"    {e}")
        failed += bool(errors)
    print(f"\n{len(pages) - failed}/{len(pages)} pages passed")
    return 1 if failed else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "check":
        sys.exit(check())
    print(__doc__)
    sys.exit(2)
