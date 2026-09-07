"""Convert downloaded CSDN article pages into Mizuki Markdown posts.

The script is intentionally offline. Download the three list API responses as
``list-1.json`` ... ``list-3.json`` and each article page as ``<id>.html`` into
one directory, then run this script against that directory. Existing posts are
matched by their CSDN article ID and backed up byte-for-byte before replacement.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify


AUTHOR_IMAGE_ID = "e0d5d6d8d09640aba7d634b39fb1a5e4"
ARTICLE_ID_RE = re.compile(r"blog\.csdn\.net/2501_93882415/article/details/(\d+)")
FRONTMATTER_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
MARKDOWN_IMAGE_RE = re.compile(r"!\[\[([^\]]+)\]\]|!\[[^\]]*\]\(([^)]+)\)")


# A previously copied article has the CS61A source URL by mistake. These
# overrides also make existing URL preservation explicit and deterministic.
EXISTING_PATH_OVERRIDES = {
    155483208: "MIT-Missing-Semester/MIT-Missing-Semester-Lecture1整理和习题答案.md",
    155542031: "cs61a print/index.md",
    155728901: "【C语言】scanf 和 printf 整理/2025-12-11-【C语言】scanf-和-printf整理.md",
    155807966: "分支语句/2025-12-11-【C语言】分支语句（简略版）.md",
    155888955: "形参和实参/形参实参.md",
    156112579: "指针（1）/index.md",
    156115036: "指针2/指针的运算和遍历.md",
    156130860: "指针3/指针的传参1.md",
    156154264: "指针4/指针的传参2.md",
    156205986: "整数和浮点数/整数和浮点数的存储.md",
    157137010: "Java基础/java基础.md",
    157183304: "Java：类的定义和使用/CS61B：Defining and Using Class.md",
    158508329: "[Java]代码块/代码块.md",
    158579136: "[Java]继承的概念和访问/继承.md",
    158851734: "[Java]继承的构造和代码块/继承.md",
    158969681: "[Java]多态/多态.md",
    159119102: "[Java]抽象类/抽象类.md",
    159252153: "[Java]String类/String.md",
    159390888: "[Java]异常及其处理/异常.md",
    159495525: "[Java数据结构]ArrayList/ArrayList.md",
    159735934: "[Java数据结构]链表/LinkedList.md",
    161319102: "[LLM] Transformer 模型/Transformer模型.md",
}


# These source notes are read only for original local images. Article text
# always comes from the current public CSDN page when that page is available.
CS_SOURCE_BY_ID = {
    155728901: "C语言/2025-12-11-【C语言】scanf-和-printf整理.md",
    155807966: "C语言/2025-12-11-【C语言】分支语句（简略版）.md",
    155888955: "C语言/形参实参.md",
    156112579: "C语言/指针1.md",
    156115036: "C语言/指针的运算和遍历.md",
    156130860: "C语言/指针的传参1.md",
    156154264: "C语言/指针的传参2.md",
    156205986: "C语言/整数和浮点数的存储.md",
    157137010: "Java/java基础.md",
    157183304: "Java/CS61B：Defining and Using Class.md",
    158508329: "Java/代码块.md",
    158579136: "Java/继承的概念和访问.md",
    158851734: "Java/继承的构造和代码块.md",
    158969681: "Java/多态.md",
    159119102: "Java/抽象类.md",
    159252153: "Java/String.md",
    159390888: "Java/异常.md",
    161319102: "LLM/Transformer模型.md",
    161491162: "Agent/基本概念，消息和聊天模板.md",
    162850480: "MySQL/增删改查.md",
    163021169: "MySQL/约束.md",
    163054021: "MySQL/表设计.md",
    163172860: "MySQL/聚合函数、分组查询、连接查询.md",
    163573118: "Algorithm/算法50分钟打卡/20260806-寻找最小值、点名.md",
    163595533: "Algorithm/算法50分钟打卡/20260808-一维二维前缀和.md",
    163643612: "Algorithm/算法50分钟打卡/20260810-前缀和-中心下标、数组乘积.md",
    163671761: "Algorithm/算法50分钟打卡/20260811-二分查找-左右边界.md",
    163669807: "MySQL（博客）/20260809-MySQL查询组合（连接、子查询、UNION与视图）.md",
    163705320: "MySQL（博客）/20260809-InnoDB索引（从页和B+树到覆盖索引与回表）.md",
    163733410: "MySQL（博客）/20260809-MySQL事务（ACID、隔离级别与并发异常）.md",
    163753346: "Algorithm/算法50分钟打卡/20260814-前缀和-子数组.md",
}


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
    text_chars: int
    markdown_chars: int
    headings: int
    code_blocks: int
    images: int
    local_images: list[tuple[Path, Path]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-dir", type=Path, required=True)
    parser.add_argument("--posts-dir", type=Path, required=True)
    parser.add_argument("--cs-dir", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-current", action="store_true")
    parser.add_argument("--reuse-existing-backups", action="store_true")
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
        if len(value) >= 2 and value[0] == value[-1] == "'":
            data[key] = value[1:-1].replace("''", "'")
        elif value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
        elif re.fullmatch(r"-?\d+(?:\.\d+)?", value):
            data[key] = float(value) if "." in value else int(value)
        else:
            data[key] = value
    return ExistingPost(path=path, data=data, raw=raw)


def load_existing(posts_dir: Path) -> tuple[dict[Path, ExistingPost], dict[int, list[ExistingPost]]]:
    by_path: dict[Path, ExistingPost] = {}
    by_id: dict[int, list[ExistingPost]] = {}
    for path in posts_dir.rglob("*.md"):
        if "（原文备份" in path.name:
            continue
        post = read_frontmatter(path)
        if post is None:
            continue
        by_path[path.resolve()] = post
        match = ARTICLE_ID_RE.search(str(post.data.get("sourceLink", "")))
        if match:
            by_id.setdefault(int(match.group(1)), []).append(post)
    return by_path, by_id


def load_articles(download_dir: Path) -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []
    expected_total: int | None = None
    for page in sorted(download_dir.glob("list-*.json")):
        payload = json.loads(page.read_text(encoding="utf-8"))
        page_total = int(payload["data"]["total"])
        if expected_total is None:
            expected_total = page_total
        elif page_total != expected_total:
            raise RuntimeError("CSDN list pages report inconsistent article totals")
        articles.extend(payload["data"]["list"])
    ids = [int(article["articleId"]) for article in articles]
    if expected_total is None:
        raise RuntimeError("no CSDN list pages found")
    if len(articles) != expected_total or len(ids) != len(set(ids)):
        raise RuntimeError(
            f"expected {expected_total} unique articles, got {len(articles)} / {len(set(ids))}"
        )
    return articles


def sanitize_path_component(title: str) -> str:
    value = title.replace("/", "-").replace("\\", "-").replace(":", "：")
    value = re.sub(r"[<>\"|?*]", "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value or "untitled"


def find_existing(
    article_id: int,
    posts_dir: Path,
    by_path: dict[Path, ExistingPost],
    by_id: dict[int, list[ExistingPost]],
) -> ExistingPost | None:
    override = EXISTING_PATH_OVERRIDES.get(article_id)
    if override:
        return by_path.get((posts_dir / override).resolve())
    candidates = by_id.get(article_id, [])
    if len(candidates) > 1:
        raise RuntimeError(f"article {article_id} maps to multiple existing posts")
    return candidates[0] if candidates else None


def clean_image_url(url: str) -> str:
    parsed = urlsplit(html.unescape(url))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))


def image_extension(url: str) -> str:
    suffix = Path(urlsplit(url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        return suffix
    return ".img"


def extract_markdown_local_images(markdown_path: Path, fallback_root: Path) -> list[Path]:
    if not markdown_path.exists():
        return []
    text = markdown_path.read_text(encoding="utf-8-sig", errors="replace")
    images: list[Path] = []
    for first, second in MARKDOWN_IMAGE_RE.findall(text):
        raw_ref = (first or second).strip().strip("<>")
        raw_ref = raw_ref.split("|", 1)[0]
        if raw_ref.startswith(("http://", "https://", "data:")):
            continue
        ref = unquote(raw_ref.split("#", 1)[0].split("?", 1)[0])
        candidates = [markdown_path.parent / ref, fallback_root / Path(ref).name]
        for candidate in candidates:
            if candidate.is_file():
                resolved = candidate.resolve()
                if resolved not in images:
                    images.append(resolved)
                break
    return images


def extract_modified_time(soup: BeautifulSoup) -> str | None:
    meta = soup.select_one('meta[property="article:modified_time"]')
    if meta and meta.get("content"):
        return str(meta["content"])
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(script.string or script.get_text())
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and payload.get("dateModified"):
            return str(payload["dateModified"])
    return None


def iso_published(post_time: str) -> str:
    value = datetime.strptime(post_time, "%Y-%m-%d %H:%M:%S")
    return value.isoformat(timespec="seconds") + "+08:00"


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def normalize_description(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def classify(title: str) -> tuple[str, list[str]]:
    lowered = title.lower()
    if "mysql" in lowered:
        return "MySQL", ["MySQL", "数据库"]
    if "agent" in lowered:
        return "AI Agent", ["Agent", "LLM", "人工智能"]
    if "llm" in lowered or "transformer" in lowered:
        return "AI", ["LLM", "Transformer", "人工智能"]
    if "python/数学模型" in lowered:
        return "Python", ["Python", "数学建模"]
    if "操作系统" in title:
        tags = ["操作系统"]
        if "rust" in lowered:
            tags.append("Rust")
        return "操作系统", tags
    if "rust" in lowered:
        return "Rust", ["Rust"]
    if "java" in lowered or "cs61b" in lowered:
        tags = ["Java"]
        if any(word in title for word in ("数据结构", "链表", "栈", "队列", "树", "排序")):
            tags.append("数据结构")
        return "Java", tags
    if "c语言" in lowered:
        return "C", ["C"]
    if any(word in title for word in ("前缀和", "二分查找")):
        return "算法", ["算法", "数据结构"]
    if "cs61a" in lowered:
        return "Python", ["Python", "CS61A"]
    if "missing-semester" in lowered:
        return "Linux", ["Linux", "Shell"]
    return "学习笔记", ["学习笔记"]


def language_for_pre(element: Tag) -> str:
    code = element.find("code")
    classes = [] if code is None else list(code.get("class", []))
    classes.extend(element.get("class", []))
    for name in classes:
        if name.startswith("language-"):
            return name.removeprefix("language-")
        if name.startswith("lang-"):
            return name.removeprefix("lang-")
    return ""


def githubish_slug(text: str, seen: dict[str, int]) -> str:
    slug = text.strip().lower()
    slug = re.sub(r"[\s]+", "-", slug)
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
        if level > 3:
            continue
        indent = "  " * max(0, level - 2)
        lines.append(f"{indent}- [{text}](#{githubish_slug(text, seen)})")
    return "\n".join(lines).rstrip() + "\n\n"


def normalize_prose_blank_lines(markdown: str) -> str:
    """Collapse prose whitespace without touching fenced code contents."""
    blocks: list[str] = []

    def stash(match: re.Match[str]) -> str:
        blocks.append(match.group(0))
        return f"\n\n@@CSDN_CODE_BLOCK_{len(blocks) - 1}@@\n\n"

    prose = re.sub(r"```[^\n]*\n.*?\n```", stash, markdown, flags=re.DOTALL)
    prose = re.sub(r"\n{3,}", "\n\n", prose)
    for index, block in enumerate(blocks):
        prose = prose.replace(f"@@CSDN_CODE_BLOCK_{index}@@", block)
    return prose


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


def render_frontmatter(
    article: dict[str, Any],
    modified: str | None,
    existing: ExistingPost | None,
) -> str:
    title = str(article["title"])
    category, tags = classify(title)
    existing_data = existing.data if existing else {}
    description = str(existing_data.get("description") or article.get("description") or "")
    published = iso_published(str(article["postTime"]))
    lines = [
        "---",
        f"title: {yaml_string(title)}",
        f"published: {published}",
    ]
    if modified:
        lines.append(f"updated: {modified}")
    lines.extend(
        [
            f"description: {yaml_string(normalize_description(description))}",
            f"tags: {json.dumps(tags, ensure_ascii=False)}",
            f"category: {yaml_string(category)}",
            f"author: {yaml_string(str(existing_data.get('author') or 'Mem0rin'))}",
            f"sourceLink: {yaml_string(str(article['url']))}",
            f"draft: {str(bool(existing_data.get('draft', False))).lower()}",
            f"pinned: {str(bool(existing_data.get('pinned', False))).lower()}",
        ]
    )
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
    download_dir: Path,
    posts_dir: Path,
    cs_dir: Path,
    assets_dir: Path,
    existing: ExistingPost | None,
    remote_manifest: dict[str, set[Path]],
) -> ArticlePlan:
    article_id = int(article["articleId"])
    page = download_dir / f"{article_id}.html"
    soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
    content = soup.select_one("#content_views")
    if content is None:
        raise RuntimeError(f"article {article_id} has no #content_views")

    target = existing.path if existing else posts_dir / sanitize_path_component(str(article["title"])) / "index.md"
    for element in content.select("script, style, link, svg"):
        element.decompose()
    for toc in content.select(".toc"):
        toc.decompose()
    for paragraph in content.find_all(["p", "div"]):
        if paragraph.get_text(strip=True).lower() in {"[toc]", "toc"} and not paragraph.find(True):
            paragraph.decompose()

    heading_tags = content.find_all(re.compile(r"^h[1-6]$"))
    heading_levels = [int(tag.name[1]) for tag in heading_tags]
    if heading_levels:
        delta = 2 - min(heading_levels)
        for heading in heading_tags:
            heading.name = f"h{min(6, max(2, int(heading.name[1]) + delta))}"
    headings = [(int(tag.name[1]), tag.get_text(" ", strip=True)) for tag in heading_tags]

    cs_images: list[Path] = []
    source_rel = CS_SOURCE_BY_ID.get(article_id)
    if source_rel:
        cs_images = extract_markdown_local_images(cs_dir / source_rel, cs_dir)
    project_images: list[Path] = []
    if existing:
        original_backup = existing.path.with_name(
            f"{existing.path.stem}（原文备份）{existing.path.suffix}"
        )
        if original_backup.exists():
            project_images = extract_markdown_local_images(original_backup, existing.path.parent)
    local_candidates: list[Path] = []
    candidate_hashes: set[bytes] = set()
    for candidate in cs_images + project_images:
        digest = hashlib.sha256(candidate.read_bytes()).digest()
        if digest not in candidate_hashes:
            candidate_hashes.add(digest)
            local_candidates.append(candidate)

    image_nodes = list(content.select("img"))
    non_author_nodes = [
        node
        for node in image_nodes
        if AUTHOR_IMAGE_ID not in str(node.get("data-src") or node.get("src") or "")
    ]
    use_local_sequence = bool(local_candidates) and len(local_candidates) == len(non_author_nodes)
    local_images: list[tuple[Path, Path]] = []
    local_index = 0
    for node in image_nodes:
        raw_url = str(node.get("data-src") or node.get("src") or "").strip()
        if not raw_url:
            continue
        if AUTHOR_IMAGE_ID not in raw_url and use_local_sequence:
            source = local_candidates[local_index]
            local_index += 1
            destination = target.parent / source.name
            if destination.exists() and destination.resolve() != source.resolve():
                if hashlib.sha256(destination.read_bytes()).digest() != hashlib.sha256(source.read_bytes()).digest():
                    destination = target.parent / f"body-image-{local_index}{source.suffix.lower()}"
            local_images.append((source, destination))
            node["src"] = os.path.relpath(destination, target.parent).replace("\\", "/")
            node.attrs.pop("data-src", None)
            continue
        if raw_url.startswith(("http://", "https://")):
            url = clean_image_url(raw_url)
            digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
            destination = assets_dir / f"csdn-{digest}{image_extension(url)}"
            remote_manifest.setdefault(url, set()).add(destination)
            node["src"] = os.path.relpath(destination, target.parent).replace("\\", "/")
            node.attrs.pop("data-src", None)

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
    body = re.sub(r"(?im)^\s*\[toc\]\s*$", "", body)
    body = normalize_prose_blank_lines(body).strip() + "\n"
    body = build_toc(headings) + body
    for index, pre in enumerate(content.select("pre"), start=1):
        code = pre.get_text().strip()
        if code and code not in body:
            raise RuntimeError(f"article {article_id} lost code block {index} during conversion")
    modified = extract_modified_time(soup)
    frontmatter = render_frontmatter(article, modified, existing)
    markdown = frontmatter + "\n" + body

    if len(source_text) >= 200 and len(body) < len(source_text) * 0.35:
        raise RuntimeError(
            f"article {article_id} conversion is suspiciously short: {len(source_text)} -> {len(body)}"
        )
    return ArticlePlan(
        article_id=article_id,
        title=str(article["title"]),
        target=target,
        existing=existing,
        markdown=markdown,
        text_chars=len(source_text),
        markdown_chars=len(body),
        headings=len(headings),
        code_blocks=len(content.select("pre")),
        images=len(image_nodes),
        local_images=local_images,
    )


def write_backup(post: ExistingPost) -> Path:
    backup = backup_path_for(post.path, post.raw)
    if not backup.exists():
        backup.write_bytes(post.raw)
    source_hash = hashlib.sha256(post.raw).hexdigest()
    backup_hash = hashlib.sha256(backup.read_bytes()).hexdigest()
    if source_hash != backup_hash:
        raise RuntimeError(f"backup hash mismatch for {post.path}")
    return backup


def main() -> int:
    args = parse_args()
    download_dir = args.download_dir.resolve()
    posts_dir = args.posts_dir.resolve()
    cs_dir = args.cs_dir.resolve()
    assets_dir = posts_dir / "_assets"
    articles = load_articles(download_dir)
    by_path, by_id = load_existing(posts_dir)
    remote_manifest: dict[str, set[Path]] = {}
    plans: list[ArticlePlan] = []
    targets: set[Path] = set()

    for article in articles:
        article_id = int(article["articleId"])
        existing = find_existing(article_id, posts_dir, by_path, by_id)
        plan = plan_article(
            article,
            download_dir,
            posts_dir,
            cs_dir,
            assets_dir,
            existing,
            remote_manifest,
        )
        if plan.target.resolve() in targets:
            raise RuntimeError(f"duplicate target path: {plan.target}")
        targets.add(plan.target.resolve())
        plans.append(plan)

    existing_count = sum(plan.existing is not None for plan in plans)
    print(f"articles={len(plans)} existing={existing_count} new={len(plans) - existing_count}")
    print(
        "source_chars=%d markdown_chars=%d headings=%d code_blocks=%d body_images=%d remote_images=%d"
        % (
            sum(plan.text_chars for plan in plans),
            sum(plan.markdown_chars for plan in plans),
            sum(plan.headings for plan in plans),
            sum(plan.code_blocks for plan in plans),
            sum(plan.images for plan in plans),
            len(remote_manifest),
        )
    )
    for plan in plans:
        state = "update" if plan.existing else "new"
        print(
            f"{plan.article_id}\t{state}\ttext={plan.text_chars}\tmd={plan.markdown_chars}"
            f"\th={plan.headings}\tcode={plan.code_blocks}\timg={plan.images}\t{plan.target.relative_to(posts_dir)}"
        )

    if args.check_current:
        missing_images: list[str] = []
        for plan in plans:
            current = plan.target.read_text(encoding="utf-8")
            if current != plan.markdown:
                raise RuntimeError(f"generated output differs from current file: {plan.target}")
            for first, second in MARKDOWN_IMAGE_RE.findall(current):
                reference = (first or second).strip().strip("<>").split("|", 1)[0]
                if reference.startswith(("http://", "https://", "data:")):
                    continue
                resolved = (plan.target.parent / unquote(reference.split("#", 1)[0])).resolve()
                if not resolved.is_file():
                    missing_images.append(f"{plan.target}: {reference}")
        if missing_images:
            raise RuntimeError("missing local images:\n" + "\n".join(missing_images))
        print("current output and local image references verified")

    if not args.write:
        print("audit complete; no files written")
        return 0

    backups: list[Path] = []
    for plan in plans:
        if plan.existing:
            primary_backup = plan.existing.path.with_name(
                f"{plan.existing.path.stem}（原文备份）{plan.existing.path.suffix}"
            )
            if args.reuse_existing_backups:
                if plan.article_id in EXISTING_PATH_OVERRIDES and not primary_backup.exists():
                    raise RuntimeError(f"expected original backup is missing: {primary_backup}")
                continue
            backups.append(write_backup(plan.existing))
    for plan in plans:
        plan.target.parent.mkdir(parents=True, exist_ok=True)
        plan.target.write_text(plan.markdown, encoding="utf-8", newline="\n")
        for source, destination in plan.local_images:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)

    manifest_path = download_dir / "image-manifest.json"
    manifest = [
        {
            "url": url,
            "destinations": [str(path) for path in sorted(destinations)],
        }
        for url, destinations in sorted(remote_manifest.items())
    ]
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    print(f"written={len(plans)} backups={len(backups)} manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise
