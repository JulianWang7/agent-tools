---
name: create-review-uml-diagrams
description: Create, revise, render, or review formal UML and engineering diagrams under STD-004. Use for use-case, architecture, component, sequence, class, state, activity, and deployment diagrams; for PlantUML or Draw.io MCP source; for SVG delivery, Markdown diagram references, diagram QA, or requests mentioning UML、架构图、组件图、时序图、用例图、状态图、活动图、部署图、PlantUML、draw.io.
---

# Create and Review UML Diagrams

Apply the STD-004 pilot without loading the complete standard into context. Treat the generated references as a routed snapshot; if they conflict with the normative source, the source standard wins.

## Route References

Always read `references/core-and-style.md` and `references/tooling-and-acceptance.md`. Then read only the diagram-specific reference needed:

- Use case: `references/use-case-diagrams.md`
- System/layered architecture or component: `references/architecture-and-components.md`
- Sequence: `references/sequence-diagrams.md`
- Other UML types: use the rules and PlantUML examples in the two always-read references and the closest template under `assets/plantuml/`

Do not invent a section number. Cite only headings that exist in the loaded references.

## Required Workflow

1. Inspect the request and its evidence before drawing. Identify diagram type, theme, boundary, nodes, and relationships. Every element must come from requirements, interfaces, code, logs, or explicit user input; mark uncertainty as `待确认`, `TBD`, or `基于当前材料推断`.
2. Choose the tool. Use PlantUML first for formal UML. Use Draw.io MCP second only when PlantUML cannot express the requirement adequately or precise manual layout is explicitly needed. Record the fallback reason. Do not silently switch tools.
3. Create one editable source of truth: `.puml` for PlantUML or `.drawio` for a Draw.io MCP fallback. Do not maintain competing authoritative sources for the same diagram.
4. Render an SVG. A formal diagram is delivered as exactly two maintained artifacts: editable source plus SVG.
5. Run automatic checks. From the skill directory, use:

   ```powershell
   python scripts/verify_diagrams.py <project-root>
   ```

6. Open the actual SVG and complete the visual checks. Then compare the diagram against source evidence for the semantic/factual checks. Automatic success never substitutes for these two reviews.
7. Report the source path, SVG path, tool used, fallback reason if any, and the result of all three validation layers.

## Non-Negotiable Rules

- Markdown embeds the rendered SVG, never `.puml`, `.drawio`, `.mmd`, or `.d2`.
- Use relative Markdown paths; never write machine-specific absolute image paths.
- Keep source and SVG synchronized after every edit.
- Do not use `skinparam`; use PlantUML themes and `<style>`.
- Do not fabricate actors, modules, dependencies, messages, returns, or exceptions.
- Do not claim visual success until the SVG has actually been opened and inspected at 100% scale.
- Do not claim semantic success until the diagram has been checked against its evidence.
- For Draw.io MCP output, keep standard editable shapes and connectors. Check anchors, waypoints, label backgrounds, perpendicular incidence, overlaps, and sequence-message Y order.
- Do not write layout-fix notes, generator parameters, or defect-remediation history on the visible canvas.
- Do not make a Git commit unless the user explicitly requests it.

## Three Validation Layers

### Automatic

Verify the source/SVG pair, SVG parsing and size, `skinparam` prohibition, directory/extension match, and Markdown link safety. Treat any error as a blocker.

### Visual

Open the SVG at 100%. Check Chinese text, title, clipping, overlap, whitespace, arrow routing, labels, legend, grayscale readability, and rendering in the target Markdown/HTML/PDF surface.

### Semantic and Factual

Check diagram type and boundary, every node and relationship, message direction and return semantics, exceptional paths when relevant, naming consistency, and evidence/version alignment. Resolve or visibly label every unsupported assertion.

## Output Locations

- PlantUML source: `docs/diagrams/plantuml/source/<name>.puml`
- PlantUML SVG: `docs/diagrams/plantuml/rendered/<name>.svg`
- Draw.io MCP source: `docs/diagrams/drawio/source/<name>.drawio`
- Draw.io MCP SVG: `docs/diagrams/drawio/rendered/<name>.svg`

Use the templates in `assets/plantuml/` as starting points, not as facts about the target system.
