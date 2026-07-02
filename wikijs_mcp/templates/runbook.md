---
type: runbook
title: "{title}"
owner: "{owner}"
created: "{date}"
last_review: "{date}"
status: draft
severity: "{severity}"
---

# {title}

> **Status:** Draft · **Owner:** {owner} · **Created:** {date}
{{.is-info}}

## Purpose

[TODO: qual problema/incidente esse runbook resolve? 1-2 frases.]

## Symptoms

[TODO: como você sabe que precisa desse runbook? Alertas específicos, mensagens de log, sintomas do usuário.]

- Alerta: [TODO]
- Log pattern: [TODO]
- Sintoma UI/API: [TODO]

## Prerequisites

- **Acessos:** [TODO: kubectl, SSH, Vault, AWS console, etc.]
- **Ferramentas locais:** [TODO: kubectl, helm, jq, awscli]
- **Contexto necessário:** [TODO: entender X, ter lido Y]

## Diagnostic Steps

1. [TODO: primeiro comando de diagnóstico + o que confirmar]
2. [TODO]
3. [TODO]

## Remediation Steps

1. [TODO: primeiro passo de correção]
2. [TODO]
3. [TODO: verificar que voltou ao normal]

## Escalation Path

- **Primeiro nível:** [TODO: squad owner]
- **Segundo nível:** [TODO: on-call / lead]
- **Terceiro nível:** [TODO: infra / vendor]

## Post-Incident

- [ ] Registrar timeline no postmortem
- [ ] Verificar se precisa update deste runbook
- [ ] Verificar se precisa nova detecção/alerta

## Related Runbooks

- [TODO: link pra runbook adjacente]
