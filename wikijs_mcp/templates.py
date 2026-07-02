"""Category templates resolver: repo defaults + optional wiki override."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from . import category_map

logger = logging.getLogger(__name__)

WIKI_OVERRIDE_PREFIX = "_templates"
WIKI_OVERRIDE_TIMEOUT_S = 5.0


class TemplateNotFoundError(ValueError):
    """Raised when the requested template cannot be resolved."""


def _available(templates_dir: Path) -> list[str]:
    if not templates_dir.exists():
        return []
    return sorted(p.stem for p in templates_dir.glob("*.md") if not p.stem.startswith("_"))


async def resolve(
    name: str,
    path: str,
    client: Any,
    templates_dir: Path,
) -> tuple[str, str, bool]:
    """Resolve template content.

    Returns tuple ``(resolved_name, content, from_wiki)``.

    Order:
      1. If ``name == "auto"``, use :func:`category_map.detect` on ``path``.
      2. Try wiki override at ``_templates/<name>`` (short timeout).
      3. Fall back to ``templates_dir/<name>.md``.
      4. Raise TemplateNotFoundError with the list of available templates.
    """
    resolved_name = category_map.detect(path) if name == "auto" else name

    # Wiki override attempt (best-effort, timeout-guarded).
    from_wiki = False
    override_content: str | None = None
    if client is not None:
        try:
            page = await asyncio.wait_for(
                client.get_page_by_path(f"{WIKI_OVERRIDE_PREFIX}/{resolved_name}"),
                timeout=WIKI_OVERRIDE_TIMEOUT_S,
            )
            if page and page.get("content"):
                override_content = page["content"]
                from_wiki = True
        except asyncio.TimeoutError:
            logger.debug(
                "Wiki override for '%s' timed out after %ss; falling back to file",
                resolved_name,
                WIKI_OVERRIDE_TIMEOUT_S,
            )
            override_content = None
        except Exception as exc:
            logger.warning(
                "Wiki override for '%s' failed (%s: %s); falling back to file",
                resolved_name,
                type(exc).__name__,
                exc,
            )
            override_content = None

    if override_content:
        return resolved_name, override_content, True

    file_path = templates_dir / f"{resolved_name}.md"
    if not file_path.exists():
        available = _available(templates_dir)
        raise TemplateNotFoundError(
            f"Template '{resolved_name}' not found. "
            f"Available: {', '.join(available) if available else '(none)'}"
        )

    return resolved_name, file_path.read_text(encoding="utf-8"), from_wiki


_PLACEHOLDER_RE = re.compile(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})")


def apply_variables(content: str, variables: dict[str, str] | None) -> str:
    """Substitute ``{placeholder}`` markers; unknown keys become ``[TODO: preencher]``.

    Preserves Wiki.js kramdown block-IAL syntax (``{{.class}}``) by requiring
    a single-brace placeholder with no adjacent brace on either side.
    """
    variables = dict(variables or {})

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, "[TODO: preencher]")

    return _PLACEHOLDER_RE.sub(_sub, content)


def _extract_title_and_description(text: str) -> tuple[str | None, str | None]:
    """Pull first H1 as title and first non-frontmatter paragraph as description."""
    lines = text.splitlines()
    idx = 0

    # Skip YAML frontmatter.
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                idx = i + 1
                break

    title: str | None = None
    description_lines: list[str] = []
    seen_content = False

    for line in lines[idx:]:
        stripped = line.strip()
        if title is None and stripped.startswith("# "):
            title = stripped.lstrip("# ").strip()
            continue
        if title is None:
            continue
        if not stripped:
            if seen_content:
                break
            continue
        seen_content = True
        description_lines.append(stripped)

    description = " ".join(description_lines) if description_lines else None
    return title, description


def list_templates(templates_dir: Path) -> list[dict[str, str]]:
    """Return template metadata (name, title, description) for the given dir."""
    out: list[dict[str, str]] = []
    if not templates_dir.exists():
        return out
    for file_path in sorted(templates_dir.glob("*.md")):
        if file_path.stem.startswith("_"):
            continue
        content = file_path.read_text(encoding="utf-8")
        title, description = _extract_title_and_description(content)
        out.append(
            {
                "name": file_path.stem,
                "title": title or file_path.stem,
                "description": description or "",
            }
        )
    return out


def get_source_marker(template_name: str, from_wiki: bool) -> str:
    """Return a short marker describing where a resolved template came from."""
    return f"{template_name} (wiki override)" if from_wiki else f"{template_name} (default)"
