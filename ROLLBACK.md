# Rollback — Category Templates feature

The category-templates feature (`wiki_create_from_template`, `wiki_list_templates`,
`wiki_show_template`) is fully gated by `WIKIJS_TEMPLATES_ENABLED`. Three rollback
options, ordered from fastest to most permanent.

---

## Option 1 — Env flag flip (seconds, no redeploy)

Set the env var to `false` in the managed settings for the MCP client:

```jsonc
// settings.json (Claude admin) or user .claude/settings.json
{
  "mcpServers": {
    "wikijs-mcp": {
      "env": { "WIKIJS_TEMPLATES_ENABLED": "false" }
    }
  }
}
```

Accepted falsy values (case-insensitive): `false`, `0`, `no`.

When the flag is off:
- the 3 template tools do **not** register in the MCP tool list;
- `wiki_create_page` and every other tool keep working unchanged;
- no wiki override fetches happen, no `templates/*.md` reads.

Users pick up the change on next MCP restart (managed settings poll ~60min, or `/config reload`).

---

## Option 2 — Repin previous SHA (minutes)

Point the MCP client back to the commit **before** this feature landed
(`0138f62` — the base of `feat/category-templates`):

```jsonc
{
  "mcpServers": {
    "wikijs-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/LerianStudio/wikijs-mcp.git@0138f62",
        "wikijs-mcp"
      ]
    }
  }
}
```

Verify the SHA in `git log --oneline main | head` before pinning.

---

## Option 3 — Revert the merge (permanent)

```bash
git revert -m 1 <merge-sha>
git push origin main
```

Use only if the feature must be removed entirely from `main`.

---

## Backwards compatibility guarantee

- `wiki_create_page` API unchanged (no `template` parameter added).
- `WikiJSClient.create_page` unchanged.
- Default env (flag unset) = feature ON; `false` = pre-feature behavior 100%.
