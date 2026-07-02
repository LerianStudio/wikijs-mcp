"""Path-prefix category detection for template auto-selection."""

import re

# Order matters — first match wins.
RULES: list[tuple[str, str]] = [
    (r"^security/security-home/03-riscos-vulnerabilidades/", "risk"),
    (r"^security/security-home/04-monitoramento-incidentes/incidents/", "postmortem"),
    (r"^security/security-home/04-monitoramento-incidentes/", "postmortem"),
    (r"^security/security-home/", "technical"),
    (r"^infradevops/devopssre-docs/03-gitops-architecture/", "architecture"),
    (r"^infradevops/devopssre-docs/06-operations-monitoring/", "runbook"),
    (r"/adrs/[^/]+$", "adr"),
    (r"/adr-[^/]*$", "adr"),
    (r"/postmortem-[^/]*$", "postmortem"),
    (r"/pm-[^/]*$", "postmortem"),
    (r"/runbook-[^/]*$", "runbook"),
]

FALLBACK = "technical"


def detect(path: str) -> str:
    """Return template name for given wiki path; FALLBACK if no rule matches."""
    for pattern, name in RULES:
        if re.search(pattern, path):
            return name
    return FALLBACK
