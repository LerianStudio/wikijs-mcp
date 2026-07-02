"""Tests for category templates resolver + category map."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from wikijs_mcp import category_map
from wikijs_mcp.templates import (
    TemplateNotFoundError,
    apply_variables,
    get_source_marker,
    list_templates,
    resolve,
)

PACKAGED_TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent / "wikijs_mcp" / "templates"
)


@pytest.fixture
def templates_dir() -> Path:
    return PACKAGED_TEMPLATES_DIR


@pytest.fixture
def null_client():
    """Client stub whose get_page_by_path never returns an override."""
    client = AsyncMock()
    client.get_page_by_path = AsyncMock(return_value=None)
    return client


# ---------- resolve --------------------------------------------------------


async def test_resolve_from_file(templates_dir, null_client):
    name, content, from_wiki = await resolve("risk", "any/path", null_client, templates_dir)
    assert name == "risk"
    assert from_wiki is False
    assert "type: risk" in content
    assert "## Descrição" in content


async def test_resolve_missing_template(templates_dir, null_client):
    with pytest.raises(TemplateNotFoundError) as excinfo:
        await resolve("does-not-exist", "any/path", null_client, templates_dir)
    msg = str(excinfo.value)
    assert "does-not-exist" in msg
    # available templates listed in error
    assert "risk" in msg
    assert "runbook" in msg


async def test_resolve_auto_by_path(templates_dir, null_client):
    name, content, _ = await resolve(
        "auto",
        "security/security-home/03-riscos-vulnerabilidades/foo",
        null_client,
        templates_dir,
    )
    assert name == "risk"
    assert "type: risk" in content


async def test_resolve_wiki_override(templates_dir):
    client = AsyncMock()
    client.get_page_by_path = AsyncMock(
        return_value={"content": "# Override risk\n\ncustom body"}
    )
    name, content, from_wiki = await resolve("risk", "any/path", client, templates_dir)
    assert name == "risk"
    assert from_wiki is True
    assert content == "# Override risk\n\ncustom body"
    client.get_page_by_path.assert_awaited_once_with("_templates/risk")


async def test_resolve_wiki_override_empty_falls_back(templates_dir):
    client = AsyncMock()
    client.get_page_by_path = AsyncMock(return_value={"content": ""})
    name, content, from_wiki = await resolve("risk", "any/path", client, templates_dir)
    assert from_wiki is False
    assert "type: risk" in content


async def test_resolve_wiki_timeout_falls_back(templates_dir):
    async def _slow(*_args, **_kwargs):
        raise asyncio.TimeoutError()

    client = AsyncMock()
    client.get_page_by_path.side_effect = _slow
    name, content, from_wiki = await resolve("risk", "any/path", client, templates_dir)
    assert from_wiki is False
    assert "type: risk" in content


# ---------- apply_variables ------------------------------------------------


def test_apply_variables_defaults_to_todo():
    tpl = "hello {name}, missing={missing_var}"
    out = apply_variables(tpl, {"name": "Primo"})
    assert out == "hello Primo, missing=[TODO: preencher]"


def test_apply_variables_preserves_double_braces():
    tpl = "note: {{.is-warning}} + {who}"
    out = apply_variables(tpl, {"who": "you"})
    assert out == "note: {{.is-warning}} + you"


def test_apply_variables_none_variables():
    out = apply_variables("{a} - {b}", None)
    assert out == "[TODO: preencher] - [TODO: preencher]"


def test_apply_variables_renders_real_template():
    tpl_content = (PACKAGED_TEMPLATES_DIR / "risk.md").read_text(encoding="utf-8")
    rendered = apply_variables(
        tpl_content, {"title": "Log4j CVE", "owner": "@primo", "date": "2026-07-02"}
    )
    assert "# Log4j CVE" in rendered
    assert "**Owner:** @primo" in rendered
    # untouched placeholders -> TODO
    assert "[TODO: preencher]" in rendered
    # double-brace Wiki.js directive preserved
    assert "{{.is-warning}}" in rendered


# ---------- category_map ---------------------------------------------------


@pytest.mark.parametrize(
    "path,expected",
    [
        ("security/security-home/03-riscos-vulnerabilidades/log4j", "risk"),
        (
            "security/security-home/04-monitoramento-incidentes/incidents/2026-07-01",
            "postmortem",
        ),
        (
            "security/security-home/04-monitoramento-incidentes/dashboards",
            "postmortem",
        ),
        ("security/security-home/some-generic-page", "technical"),
        (
            "infradevops/devopssre-docs/03-gitops-architecture/argocd",
            "architecture",
        ),
        (
            "infradevops/devopssre-docs/06-operations-monitoring/pod-restarts",
            "runbook",
        ),
        ("random/team/adrs/2026-01-decision", "adr"),
        ("random/team/adr-0007-something", "adr"),
        ("some/team/postmortem-2026-07-01", "postmortem"),
        ("some/team/pm-2026-07-01", "postmortem"),
        ("some/team/runbook-postgres-failover", "runbook"),
        ("totally/unmatched/page", "technical"),  # fallback
        # Regression: `.*/adr-` used to misclassify a postmortem living under
        # an "adr-review" directory as an ADR.
        ("team/adr-review/postmortem-log4j", "postmortem"),
        # Non-leaf `adr-` directory does NOT match — falls back to technical.
        ("some/path/adr-decision/subpage", "technical"),
        # Sanity: leaf-anchored patterns still match.
        ("some/path/adr-log4j", "adr"),
    ],
)
def test_category_detect_all_rules(path, expected):
    assert category_map.detect(path) == expected


# ---------- list_templates -------------------------------------------------


def test_list_templates_extracts_titles(templates_dir):
    entries = list_templates(templates_dir)
    names = {e["name"] for e in entries}
    assert {"risk", "adr", "runbook", "postmortem", "architecture", "technical"} <= names
    for entry in entries:
        assert entry["title"], f"template {entry['name']} missing title"


def test_list_templates_missing_dir(tmp_path):
    assert list_templates(tmp_path / "nope") == []


# ---------- source marker --------------------------------------------------


def test_source_marker():
    assert get_source_marker("risk", from_wiki=True) == "risk (wiki override)"
    assert get_source_marker("risk", from_wiki=False) == "risk (default)"
