"""Convert captured public Zhihu articles into Mizuki Markdown posts.

The input can be a flattened JSON list of Zhihu article objects or the capture
file produced by ``fetch-zhihu.mjs``. Existing Zhihu posts are matched by
article ID and backed up byte-for-byte before replacement.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify


ARTICLE_ID_RE = re.compile(r"(?:zhuanlan\.)?zhihu\.com/p/(\d+)")
FRONTMATTER_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
MARKDOWN_IMAGE_RE = re.compile(r"!\[\[([^\]]+)\]\]|!\[[^\]]*\]\(([^)]+)\)")
CHINA_TZ = timezone(timedelta(hours=8))


@dataclass
class ExistingPost:
    path: Path
    data: dict[str, Any]
    raw: bytes


@dataclass
class ArticlePlan:
    article_id: int
    title: str
    target: Path
    existing: ExistingPost | None
    markdown: str
    source_chars: int
    markdown_chars: int
    headings: int
    code_blocks: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", type=Path, required=True)
    parser.add_argument("--posts-dir", type=Path, required=True)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-current", action="store_true")
    return parser.parse_args()


def read_frontmatter(path: Path) -> ExistingPost | None:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    data: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        field = re.match(r"^([A-Za-z][A-Za-z0-9_]*):\s*(.*)$", line)
        if not field:
            continue
        key, raw_value = field.groups()
        value = raw_value.strip()
        if value.startswith(('"', "[", "{")):
            try:
                data[key] = json.loads(value)
                continue
            except json.JSONDecodeError:
                pass
        if value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
        elif re.fullmatch(r"-?\d+(?:\.\d+)?", value):
            data[key] = float(value) if "." in value else int(value)
        else:
            data[key] = value
    return ExistingPost(path=path, data=data, raw=raw)


def load_existing(posts_dir: Path) -> tuple[dict[int, ExistingPost], dict[str, list[ExistingPost]]]:
    by_id: dict[int, ExistingPost] = {}
    by_title: dict[str, list[ExistingPost]] = {}
    for path in posts_dir.rglob("*.md"):
        if "（原文备份" in path.name:
            continue
        post = read_frontmatter(path)
        if post is None:
            continue
        title = str(post.data.get("title", "")).strip()
        if title:
            by_title.setdefault(title, []).append(post)
        match = ARTICLE_ID_RE.search(str(post.data.get("sourceLink", "")))
        if match:
            article_id = int(match.group(1))
            if article_id in by_id:
                raise RuntimeError(f"duplicate Zhihu sourceLink for article {article_id}")
            by_id[article_id] = post
    return by_id, by_title


def load_articles(input_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict) and isinstance(payload.get("articles"), list):
        candidates = payload["articles"]
    elif isinstance(payload, dict):
        candidates = []
        for page in payload.get("activitiesPages", []) + payload.get("activityProbes", []):
            try:
                page_payload = json.loads(page["body"])
            except (KeyError, TypeError, json.JSONDecodeError):
                continue
            for activity in page_payload.get("data", []):
                target = activity.get("target", {})
                if target.get("type") == "article":
                    candidates.append(target)
    else:
        raise RuntimeError("unsupported Zhihu input format")

    articles: dict[int, dict[str, Any]] = {}
    for article in candidates:
        if not isinstance(article, dict) or article.get("type", "article") != "article":
            continue
        article_id = int(article["id"])
        previous = articles.get(article_id)
        if previous and previous != article:
            # The same activity can appear in more than one compatibility probe.
            # Prefer the copy with the longest body.
            if len(str(previous.get("content", ""))) >= len(str(article.get("content", ""))):
                continue
        articles[article_id] = article
    return sorted(articles.values(), key=lambda item: (int(item["created"]), int(item["id"])))


def sanitize_path_component(title: str) -> str:
    value = title.replace("/", "-").replace("\\", "-").replace(":", "：")
    value = re.sub(r'[<>"|?*]', "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value or "untitled"


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def iso_timestamp(value: int) -> str:
    return datetime.fromtimestamp(value, CHINA_TZ).isoformat(timespec="seconds")


def normalize_description(value: str) -> str:
    normalized = re.sub(r"\s+", " ", html.unescape(value)).strip()
    return re.sub(r"\s+([，。；：！？、])", r"\1", normalized)


def classify(title: str) -> tuple[str, list[str]]:
    lowered = title.lower()
    if "agent" in lowered:
        return "AI Agent", ["Agent", "Python", "人工智能"]
    if any(word in title for word in ("前缀和", "滑动窗口", "数组分区", "算法每日一题")):
        return "算法", ["算法", "数据结构"]
    return "学习笔记", ["学习笔记"]


def language_for_pre(element: Tag) -> str:
    code = element.find("code")
    classes = [] if code is None else list(code.get("class", []))
    classes.extend(element.get("class", []))
    for name in classes:
        if name.startswith("language-"):
            language = name.removeprefix("language-")
            return {"python3": "python"}.get(language, language)
        if name.startswith("lang-"):
            language = name.removeprefix("lang-")
            return {"python3": "python"}.get(language, language)
    return ""


def githubish_slug(text: str, seen: dict[str, int]) -> str:
    slug = re.sub(r"[\s]+", "-", text.strip().lower())
    slug = re.sub(r"[^\w\-\u4e00-\u9fff]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-") or "section"
    count = seen.get(slug, 0)
    seen[slug] = count + 1
    return slug if count == 0 else f"{slug}-{count}"


def build_toc(headings: list[tuple[int, str]]) -> str:
    if not headings:
        return ""
    seen: dict[str, int] = {"目录": 1}
    lines = ["## 目录", ""]
    for level, text in headings:
        if level > 4:
            continue
        indent = "  " * max(0, level - 2)
        lines.append(f"{indent}- [{text}](#{githubish_slug(text, seen)})")
    return "\n".join(lines).rstrip() + "\n\n"


def remove_manual_toc(content: BeautifulSoup) -> None:
    for marker in list(content.find_all(["p", "div", "h2", "h3"])):
        if marker.get_text(" ", strip=True) not in {"目录", "文章目录"}:
            continue
        sibling = marker.find_next_sibling()
        if isinstance(sibling, Tag) and sibling.name in {"ul", "ol"}:
            sibling.decompose()
        marker.decompose()
        return


def unwrap_zhihu_links(content: BeautifulSoup) -> None:
    for link in content.find_all("a", href=True):
        parsed = urlparse(str(link["href"]))
        if parsed.netloc == "link.zhihu.com":
            target = parse_qs(parsed.query).get("target", [""])[0]
            if target:
                link["href"] = unquote(target)


def normalize_prose_blank_lines(markdown: str) -> str:
    blocks: list[str] = []

    def stash(match: re.Match[str]) -> str:
        blocks.append(match.group(0))
        return f"\n\n@@ZHIHU_CODE_BLOCK_{len(blocks) - 1}@@\n\n"

    prose = re.sub(r"```[^\n]*\n.*?\n```", stash, markdown, flags=re.DOTALL)
    prose = re.sub(r"\n{3,}", "\n\n", prose)
    for index, block in enumerate(blocks):
        prose = prose.replace(f"@@ZHIHU_CODE_BLOCK_{index}@@", block)
    return prose


def render_frontmatter(article: dict[str, Any], existing: ExistingPost | None) -> str:
    title = str(article["title"])
    category, tags = classify(title)
    existing_data = existing.data if existing else {}
    soup = BeautifulSoup(str(article["content"]), "html.parser")
    first_paragraph = soup.find("p")
    description = normalize_description(
        str(existing_data.get("description") or (first_paragraph.get_text(" ", strip=True) if first_paragraph else ""))
    )
    lines = [
        "---",
        f"title: {yaml_string(title)}",
        f"published: {iso_timestamp(int(article['created']))}",
        f"updated: {iso_timestamp(int(article.get('updated') or article['created']))}",
        f"description: {yaml_string(description)}",
        f"tags: {json.dumps(tags, ensure_ascii=False)}",
        f"category: {yaml_string(category)}",
        f"author: {yaml_string(str(existing_data.get('author') or 'Mem0rin'))}",
        f"sourceLink: {yaml_string(f'https://zhuanlan.zhihu.com/p/{article["id"]}')}",
        f"draft: {str(bool(existing_data.get('draft', False))).lower()}",
        f"pinned: {str(bool(existing_data.get('pinned', False))).lower()}",
    ]
    for key in ("image", "licenseName", "licenseUrl", "alias", "permalink", "encrypted", "password", "priority"):
        value = existing_data.get(key)
        if value in (None, "", False):
            continue
        if isinstance(value, bool):
            rendered = str(value).lower()
        elif isinstance(value, (int, float)):
            rendered = str(value)
        else:
            rendered = yaml_string(str(value))
        lines.append(f"{key}: {rendered}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def plan_article(
    article: dict[str, Any],
    posts_dir: Path,
    by_id: dict[int, ExistingPost],
    by_title: dict[str, list[ExistingPost]],
) -> ArticlePlan:
    article_id = int(article["id"])
    title = str(article["title"])
    existing = by_id.get(article_id)
    if existing is None:
        same_title = by_title.get(title, [])
        if len(same_title) > 1:
            raise RuntimeError(f"article {article_id} matches multiple posts by title")
        existing = same_title[0] if same_title else None
    target = existing.path if existing else posts_dir / sanitize_path_component(title) / "index.md"

    content = BeautifulSoup(str(article["content"]), "html.parser")
    for element in content.select("script, style, link, svg, noscript"):
        element.decompose()
    remove_manual_toc(content)
    unwrap_zhihu_links(content)

    heading_tags = content.find_all(re.compile(r"^h[1-6]$"))
    heading_levels = [int(tag.name[1]) for tag in heading_tags]
    if heading_levels:
        delta = 2 - min(heading_levels)
        for heading in heading_tags:
            heading.name = f"h{min(6, max(2, int(heading.name[1]) + delta))}"
            if re.match(r"^（[一二三四五六七八九十]+）", heading.get_text(" ", strip=True)):
                heading.name = "h3"
    headings = [(int(tag.name[1]), tag.get_text(" ", strip=True)) for tag in heading_tags]

    source_text = content.get_text("\n", strip=True)
    body = markdownify(
        str(content),
        heading_style="ATX",
        bullets="-",
        code_language_callback=language_for_pre,
        escape_asterisks=False,
        escape_underscores=False,
        strip_pre="strip",
    )
    body = body.replace("\ufeff", "").replace("\u200b", "")
    body = normalize_prose_blank_lines(body).strip() + "\n"
    body = build_toc(headings) + body

    for index, pre in enumerate(content.select("pre"), start=1):
        code = pre.get_text().strip()
        if code and code not in body:
            raise RuntimeError(f"article {article_id} lost code block {index} during conversion")
    if len(source_text) >= 200 and len(body) < len(source_text) * 0.5:
        raise RuntimeError(
            f"article {article_id} conversion is suspiciously short: {len(source_text)} -> {len(body)}"
        )
    markdown = render_frontmatter(article, existing) + "\n" + body
    return ArticlePlan(
        article_id=article_id,
        title=title,
        target=target,
        existing=existing,
        markdown=markdown,
        source_chars=len(source_text),
        markdown_chars=len(body),
        headings=len(headings),
        code_blocks=len(content.select("pre")),
    )


def backup_path_for(path: Path, raw: bytes) -> Path:
    primary = path.with_name(f"{path.stem}（原文备份）{path.suffix}")
    if not primary.exists() or primary.read_bytes() == raw:
        return primary
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}（原文备份-{index}）{path.suffix}")
        if not candidate.exists() or candidate.read_bytes() == raw:
            return candidate
        index += 1


def write_backup(post: ExistingPost) -> Path:
    backup = backup_path_for(post.path, post.raw)
    if not backup.exists():
        backup.write_bytes(post.raw)
    if hashlib.sha256(post.raw).digest() != hashlib.sha256(backup.read_bytes()).digest():
        raise RuntimeError(f"backup hash mismatch for {post.path}")
    return backup


def verify_local_images(plan: ArticlePlan) -> None:
    for first, second in MARKDOWN_IMAGE_RE.findall(plan.markdown):
        reference = (first or second).strip().strip("<>").split("|", 1)[0]
        if reference.startswith(("http://", "https://", "data:")):
            continue
        resolved = (plan.target.parent / unquote(reference.split("#", 1)[0])).resolve()
        if not resolved.is_file():
            raise RuntimeError(f"missing local image in {plan.target}: {reference}")


def main() -> int:
    args = parse_args()
    input_path = args.input_json.resolve()
    posts_dir = args.posts_dir.resolve()
    articles = load_articles(input_path)
    if args.expected_count is not None and len(articles) != args.expected_count:
        raise RuntimeError(f"expected {args.expected_count} unique articles, got {len(articles)}")
    by_id, by_title = load_existing(posts_dir)
    plans = [plan_article(article, posts_dir, by_id, by_title) for article in articles]
    targets = [plan.target.resolve() for plan in plans]
    if len(targets) != len(set(targets)):
        raise RuntimeError("multiple Zhihu articles map to the same post path")

    existing_count = sum(plan.existing is not None for plan in plans)
    print(f"articles={len(plans)} existing={existing_count} new={len(plans) - existing_count}")
    print(
        "source_chars=%d markdown_chars=%d headings=%d code_blocks=%d"
        % (
            sum(plan.source_chars for plan in plans),
            sum(plan.markdown_chars for plan in plans),
            sum(plan.headings for plan in plans),
            sum(plan.code_blocks for plan in plans),
        )
    )
    for plan in plans:
        state = "update" if plan.existing else "new"
        print(
            f"{plan.article_id}\t{state}\ttext={plan.source_chars}\tmd={plan.markdown_chars}"
            f"\th={plan.headings}\tcode={plan.code_blocks}\t{plan.target.relative_to(posts_dir)}"
        )

    if args.check_current:
        for plan in plans:
            if plan.target.read_text(encoding="utf-8") != plan.markdown:
                raise RuntimeError(f"generated output differs from current file: {plan.target}")
            verify_local_images(plan)
        print("current output and local image references verified")

    if not args.write:
        print("audit complete; no files written")
        return 0

    backups = [write_backup(plan.existing) for plan in plans if plan.existing]
    for plan in plans:
        plan.target.parent.mkdir(parents=True, exist_ok=True)
        plan.target.write_text(plan.markdown, encoding="utf-8", newline="\n")
    print(f"written={len(plans)} backups={len(backups)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise
