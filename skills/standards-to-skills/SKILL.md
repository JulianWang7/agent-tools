---
name: standards-to-skills
description: Convert or maintain normative Markdown standards as portable Agent Skills and lightweight routing rules. Use when onboarding a STD document, generating routed references/templates, updating the standards maintenance manifest, checking source or installation drift, synchronizing Skills to Cursor/Claude/QwenPaw, or extending the STD-004 pilot to another standard.
---

# Standards to Skills

Keep each normative Markdown document as the source of truth. Use the canonical tool at `D:\Workspace\tools\standards-to-skills` to generate context-efficient runtime Skills, track hashes, and synchronize declared installations.

## Operating Model

- Source standard: normative rules and version history; edit this first.
- Maintenance manifest: `standards-manifest.json`; records ownership, section routing, hashes, targets, and pilot status.
- Canonical Skill: reviewed workflow plus generated references/assets.
- Installed copies: disposable managed replicas. Never edit them directly.
- Environment rule: a short trigger/router only; do not duplicate the complete standard in a rule.

## Required Workflow

1. Inspect the source standard and existing manifest before changing anything. Preserve unrelated workspace edits.
2. Resolve contradictions in the source standard first. Never hide source defects inside a generated Skill.
3. Use `skill-creator` or the target agent's equivalent scaffold for a new canonical Skill. Keep `SKILL.md` concise and route detailed content into `references/`.
4. Add or update exactly one manifest entry. Define source file, owner, status, section groups, generated assets, target roots, and the gate for broader rollout.
5. Build and inspect the canonical output:

   ```powershell
   cd D:\Workspace\tools\standards-to-skills
   python standards_to_skills.py build --standard STD-004
   python standards_to_skills.py status --standard STD-004
   ```

6. Validate the Skill structure and run the repository tests. Review generated references for missing headings, stale terminology, and broken cross-references.
7. Preview synchronization before applying it. Apply only to manifest-declared targets:

   ```powershell
   python standards_to_skills.py sync --standard STD-004 --target cursor --target claude
   python standards_to_skills.py sync --standard STD-004 --target cursor --target claude --apply
   ```

8. For QwenPaw, run its native skill scan/test and explicitly enable a newly discovered customized Skill. File presence alone is not activation.
9. Finish only when source drift and canonical drift are false, every intended copy is hash-equal, environment activation is verified where required, and the maintenance manifest contains the evidence.

## Safety Rules

- Do not overwrite an existing installation unless it carries a matching `.standards-to-skills.json` marker.
- Do not manually edit generated `references/` or generated template assets.
- Do not convert every standard in bulk. Pilot one standard, observe real use, revise triggers and validation, then expand.
- Do not put the complete standard into global rules or `SKILL.md`; progressive disclosure is part of the design.
- Do not claim token savings from file conversion alone. Savings come from concise trigger metadata and loading only relevant references.
- Do not commit or push unless the user explicitly requests it.

## STD-004 Pilot Gate

Treat STD-004 as the only active pilot until it has been exercised on real UML creation and review tasks. Before onboarding another standard, record false triggers, missed triggers, rule conflicts, manual review defects, and maintenance effort; then adjust the generator or Skill structure based on evidence.
