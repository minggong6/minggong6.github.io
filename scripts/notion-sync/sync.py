"""Notion page -> Jekyll _posts markdown sync (runs in GitHub Actions)."""

import mimetypes
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from notion_client import Client

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
PAGE_ID = os.environ.get("NOTION_PAGE_ID", "3c86c74e-657a-8054a134e507933557de")
TAGS_ENV = [t.strip() for t in os.environ.get("POST_TAGS", "").split(",") if t.strip()]
POSTS_DIR = Path("_posts")
ASSET_DIR = Path("assets/notion")
DEFAULT_EXT = {"image": ".png", "video": ".mp4", "audio": ".mp3", "pdf": ".pdf", "file": ".bin"}
TZ8 = timezone(timedelta(hours=8))
FOOTER_RE = re.compile(r"^\*⏱.*\*\s*$", re.M)

SLUG = os.environ.get("POST_SLUG", "").strip()
client = Client(auth=NOTION_TOKEN, timeout_ms=60000)
http = requests.Session()
unsupported = set()


def retry(fn, *args, **kwargs):
    for i in range(3):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if i == 2:
                raise
            print(f"retry after error: {e}", file=sys.stderr)
            time.sleep(3 * (i + 1))


def rich_to_md(rich):
    out = []
    for rt in rich:
        kind = rt.get("type", "text")
        if kind == "text":
            seg = rt["text"]["content"]
            if not seg:
                continue
            ann = rt.get("annotations", {})
            if ann.get("code"):
                seg = f"`{seg}`"
            if ann.get("bold"):
                seg = f"**{seg}**"
            if ann.get("italic"):
                seg = f"*{seg}*"
            if ann.get("strikethrough"):
                seg = f"~~{seg}~~"
            if ann.get("underline"):
                seg = f"<u>{seg}</u>"
            link = rt["text"].get("link") or {}
            if link.get("url"):
                seg = f"[{seg}]({link['url']})"
            out.append(seg)
        elif kind == "equation":
            out.append(f"${rt['equation']['expression']}$")
        elif kind == "mention" and rt["mention"].get("type") == "page":
            try:
                sub = retry(client.pages.retrieve, page_id=rt["mention"]["page"]["id"])
                out.append(f"[{page_title(sub)}]({sub['url']})")
            except Exception:
                out.append(rt.get("plain_text", "sub-page"))
        else:
            out.append(rt.get("plain_text", ""))
    return "".join(out)


def rich_plain(rich):
    return "".join(rt.get("plain_text", "") for rt in rich)


def page_title(page):
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return rich_plain(prop.get("title", []))
    return "untitled"


def tags_from(page):
    for name, prop in page.get("properties", {}).items():
        if name.lower() not in ("tags", "tag", "标签"):
            continue
        if prop.get("type") == "multi_select":
            return [v["name"] for v in prop.get("multi_select", [])]
        if prop.get("type") == "select" and prop.get("select"):
            return [prop["select"]["name"]]
    return []


def caption_of(payload):
    return rich_to_md(payload.get("caption", [])).strip()


def download_asset(payload, kind):
    """Returns (site_path, url). Notion-hosted files get downloaded: signed URLs expire in ~1h."""
    ptype = payload.get("type")
    url = payload.get("file", {}).get("url") if ptype == "file" else payload.get("external", {}).get("url")
    if not url:
        return None, None
    if ptype == "external":
        return None, url
    raw = payload.get("name") or Path(unquote(urlparse(url).path)).name or "asset"
    stem = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", Path(raw).stem)[:40].strip("-") or "asset"
    ext = Path(raw).suffix or DEFAULT_EXT.get(kind, ".bin")
    dest = ASSET_DIR / SLUG / f"{stem}{ext}"
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = retry(http.get, url, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"downloaded {dest}")
    return f"/{dest.as_posix()}", url


def media_line(payload, kind):
    alt = caption_of(payload)
    if kind == "image":
        path, url = download_asset(payload, kind)
        if path:
            return f"![{alt}]({path})"
        if url:
            return f"![{alt}]({url})"
        return ""
    path, url = download_asset(payload, kind)
    target = path or url
    return f"[📎 {alt or kind}]({target})" if target else ""


def fetch_children(block_id):
    results, cursor = [], None
    while True:
        resp = retry(client.blocks.children.list, block_id=block_id, start_cursor=cursor, page_size=100)
        results.extend(resp["results"])
        if not resp.get("has_more"):
            return results
        cursor = resp["next_cursor"]
        time.sleep(0.35)


def blocks_to_md(block_id, depth=0):
    lines = []
    for b in fetch_children(block_id):
        lines.extend(block_to_md(b, depth))
        lines.append("")
    return lines


def list_item(b, prefix, payload, depth):
    out = [f"{'    ' * depth}{prefix}{rich_to_md(payload.get('rich_text', []))}"]
    if b.get("has_children"):
        out.extend(blocks_to_md(b["id"], depth + 1))
    return out


def quote_block(lines):
    return [f"> {line}" if line else ">" for line in lines]


def md_table(b):
    rows = fetch_children(b["id"])
    grid = [r["table_row"]["cells"] for r in rows if r["type"] == "table_row"]
    if not grid:
        return []
    ncol = max(len(r) for r in grid)
    norm = [
        [rich_to_md(c).replace("|", "\\|").replace("\n", " ") for c in row + [""] * (ncol - len(row))]
        for row in grid
    ]
    out = [
        "| " + " | ".join(norm[0]) + " |",
        "|" + "|".join([" --- "] * ncol) + "|",
    ]
    out += ["| " + " | ".join(r) + " |" for r in norm[1:]]
    return out


def block_to_md(b, depth=0):
    t = b["type"]
    p = b.get(t, {})
    nested = blocks_to_md(b["id"]) if b.get("has_children") else []

    if t == "paragraph":
        return [rich_to_md(p.get("rich_text", []))]
    if t in ("heading_1", "heading_2", "heading_3"):
        return [f"{'#' * (int(t[-1]) + 1)} {rich_to_md(p.get('rich_text', []))}"]
    if t == "bulleted_list_item":
        return list_item(b, "- ", p, depth)
    if t == "numbered_list_item":
        return list_item(b, "1. ", p, depth)
    if t == "to_do":
        return list_item(b, f"- [{'x' if p.get('checked') else ' '}] ", p, depth)
    if t == "toggle":
        return [f"**{rich_to_md(p.get('rich_text', []))}**", ""] + nested
    if t == "quote":
        return quote_block([rich_to_md(p.get("rich_text", []))] + nested)
    if t == "callout":
        icon = (p.get("icon") or {}).get("emoji", "💡")
        return quote_block([f"{icon} {rich_to_md(p.get('rich_text', []))}"] + nested)
    if t == "divider":
        return ["---"]
    if t == "equation":
        return ["", f"$${p['expression']}$$", ""]
    if t == "code":
        lines = [f"```{p.get('language', '')}", rich_plain(p.get("rich_text", [])), "```"]
        cap = caption_of(p)
        if cap:
            lines.append(f"*{cap}*")
        return lines
    if t == "table":
        return md_table(b)
    if t in ("image", "video", "file", "pdf", "audio"):
        line = media_line(p, t)
        return [line] if line else []
    if t in ("bookmark", "embed", "link_preview"):
        url = p.get("url", "")
        return [f"[{caption_of(p) or url}]({url})"] if url else []
    if t == "child_page":
        try:
            sub = retry(client.pages.retrieve, page_id=b["id"])
            return [f"**[{page_title(sub)}]({sub['url']})**", ""]
        except Exception:
            return [f"**{p.get('title', 'sub-page')}**", ""]
    if t in ("column_list", "column"):
        return nested

    unsupported.add(t)
    return []


def main():
    global SLUG
    page = retry(client.pages.retrieve, page_id=PAGE_ID)
    title = os.environ.get("POST_TITLE", "").strip() or page_title(page)
    if not SLUG:
        SLUG = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", title).strip("-") or "notion-post"
    tags = tags_from(page) or TAGS_ENV

    existing = next(POSTS_DIR.glob(f"*-{SLUG}.md"), None)
    dest = existing or POSTS_DIR / f"{datetime.now(TZ8).strftime('%Y-%m-%d')}-{SLUG}.md"

    body = re.sub(r"\n{3,}", "\n\n", "\n".join(blocks_to_md(PAGE_ID)).strip()) + "\n"

    if existing:
        old = existing.read_text(encoding="utf-8")
        old_body = FOOTER_RE.sub("", old.split("---", 2)[2] if old.count("---") >= 2 else old).strip()
        if old_body == body.strip():
            print("No changes since last sync.")
            return

    date_str = None
    if existing:
        m = re.search(r"^date:\s*(.+)$", existing.read_text(encoding="utf-8"), re.M)
        date_str = m.group(1).strip() if m else None
    if not date_str:
        date_str = datetime.now(TZ8).strftime("%Y-%m-%d %H:%M:%S %z")

    tags_yaml = "[" + ", ".join(tags) + "]" if tags else "[]"
    front = f"---\ntitle: \"{title}\"\ndate: {date_str}\ntags: {tags_yaml}\n---\n\n"
    footer = f"\n*⏱ 最后更新于 {datetime.now(TZ8).strftime('%Y-%m-%d %H:%M')} · 由 [Notion](https://www.notion.so) 自动同步*\n"
    dest.write_text(front + body + footer, encoding="utf-8")
    print(f"wrote {dest}")
    if unsupported:
        print("skipped block types:", ", ".join(sorted(unsupported)))


if __name__ == "__main__":
    main()
