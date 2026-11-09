#!/usr/bin/env python3
"""Fill the newest <release> in the metainfo with notes from its upstream GitHub release.

Older <release> entries are collapsed back to one line so the file does not keep growing.

Usage:
  ./update-changelog.py

Set GITHUB_TOKEN to avoid the unauthenticated API rate limit.
"""
import json
import os
import re
import urllib.request
from html import escape

REPO = "usebruno/bruno"
METAINFO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "com.usebruno.Bruno.metainfo.xml")
MAX_ITEMS_PER_SECTION = 10
SKIPPED_SECTIONS = {"new contributors", "contributors", "others", "other"}

RELEASE_RE = re.compile(r'( *)<release version="([^"]+)" date="([^"]+)"\s*(?:/>|>.*?</release>)', re.S)
HEADING_RE = re.compile(r"^(?:#{1,6}\s+(.+?)|([A-Z][\w ]*):)\s*$")
ITEM_RE = re.compile(r"^[-*]\s+(.+)$")
CONVENTIONAL_PREFIX_RE = re.compile(r"^[a-z]+(?:\([^)]*\))?!?:\s*", re.I)


def fetch_release(version):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{REPO}/releases/tags/{version}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as res:
        return json.load(res)


def clean_item(text):
    text = re.sub(r"\s+by\s+@.*$", "", text)  # author and PR references
    text = re.sub(r"\s+in\s+https?://\S+.*$", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # markdown links
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = CONVENTIONAL_PREFIX_RE.sub("", text).strip()
    if not text:
        return None

    if re.match(r"[a-z]+\b(?![.(_])", text):  # leave identifiers like bru.hasVar untouched
        text = text[0].upper() + text[1:]
    # escape everything, then restore inline code spans as <code>
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escape(text, quote=False))


def parse_sections(body):
    sections, title = [], None
    for line in body.replace("\r", "").split("\n"):
        line = line.strip()
        heading = HEADING_RE.match(line)
        if heading:
            title = (heading.group(1) or heading.group(2)).strip()
            continue

        item = ITEM_RE.match(line)
        if not item or (title and title.lower() in SKIPPED_SECTIONS):
            continue

        text = clean_item(item.group(1))
        if not text:
            continue
        if not sections or sections[-1][0] != title:
            sections.append((title, []))
        sections[-1][1].append(text)
    return sections


def build_description(body, indent):
    pad = indent + "    "
    lines = []
    for title, items in parse_sections(body):
        if title and title.lower() not in {"changelog", "what's changed"}:
            lines.append(f"{pad}<p>{escape(title, quote=False)}</p>")
        shown = items[:MAX_ITEMS_PER_SECTION]
        if len(items) > len(shown):
            shown.append(f"…and {len(items) - len(shown)} more")
        lines.append(f"{pad}<ul>")
        lines.extend(f"{pad}  <li>{item}</li>" for item in shown)
        lines.append(f"{pad}</ul>")
    return lines


def render_release(indent, version, date, release):
    if not release:
        return f'{indent}<release version="{version}" date="{date}"></release>'

    lines = [f'{indent}<release version="{version}" date="{date}">']
    lines.append(f'{indent}  <url type="details">{escape(release["html_url"])}</url>')
    description = build_description(release.get("body") or "", indent)
    if description:
        lines.append(f"{indent}  <description>")
        lines.extend(description)
        lines.append(f"{indent}  </description>")
    lines.append(f"{indent}</release>")
    return "\n".join(lines)


def main():
    with open(METAINFO, encoding="utf-8") as f:
        metainfo = f.read()

    newest = RELEASE_RE.search(metainfo)
    release = fetch_release(newest.group(2))

    def replace(match):
        indent, version, date = match.groups()
        return render_release(indent, version, date, release if match.start() == newest.start() else None)

    metainfo = RELEASE_RE.sub(replace, metainfo)

    with open(METAINFO, "w", encoding="utf-8") as f:
        f.write(metainfo)


if __name__ == "__main__":
    main()
