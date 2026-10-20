# Agent Skills

PCO-level skills available to all governed repos. Each skill is defined in its own `SKILL.md` and symlinked into `.claude/skills/` (and equivalents for other harnesses) by `distill_harness.py sync` (or `wire`).

Project-specific skills live in `ai_context/project/ai_harness/skills/` and override PCO skills on name collision.

## Skills

Status is the skill's `stage` in [capability_registry.yaml](../../governance/capability_registry.yaml); `—` means the skill is not registered there and has no lifecycle stage.

| Name | Status | Description |
|------|--------|-------------|
| [backlog-continuity](backlog-continuity/SKILL.md) | Established | Creates/updates anchor-doc checkpoints for backlog continuity. Invoke when starting/continuing a backlog item or creating a TODO anchor doc. |
| [capture-lessons](capture-lessons/SKILL.md) | Emerging | Capture lessons from implementation work into ai_context/ before they are lost. Enforces selectivity: most fixes do not belong here. |
| [docs-alignment](docs-alignment/SKILL.md) | — | Validates and fixes a repo or implementation's docs against the platform documentation contract. Invoke when creating a new repo/implementation, before publishing, or when docs may have drifted. |
| [use-context](use-context/SKILL.md) | Established | Use AI context before starting tasks. Identifies which already-loaded rule files apply, via the deterministic router in ASSISTANTS.md. |

