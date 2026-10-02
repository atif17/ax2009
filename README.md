# AX 2009 techno-functional skill for Claude

A skill that makes Claude work like a senior Dynamics AX 2009 techno-functional consultant on troubleshooting, root-cause analysis, read-only SQL investigation and X++ development. Typical work: inventory, costing, GL posting, integrations and batch jobs.

It encodes a working method proven on real AX 2009 support work:

- **AX 2009-correct answers.** It won't suggest AX 2012/D365 features (extensions, InventTransOrigin, DefaultDimension). It knows the DATAAREAID, virtual-company and enum traps.
- **An evidence loop.** Claude writes the query or class, you run it, Claude interprets the result. It never connects to or executes against client systems.
- **A safe data-repair pattern.** PREVIEW → ROLLBACK_TEST → APPLY, with state-bound tokens, environment guards and independent verification.
- **Searchable source.** `split_xpo.py` turns 100+ MB XPO exports into one file per AOT object, with an index that shows which layers customized each object and method.
- **Project memory.** Templates for a one-page `CLAUDE.md` and per-ticket `STATUS.md`, so every session starts from the current state.

## Contents
```
skills/ax2009-techno-functional/
  SKILL.md                          main instructions
  scripts/split_xpo.py              split XPO exports + build indexes (Python 3, no dependencies)
  references/xpp-compile-pitfalls.md
  references/repair-safety-pattern.md
  templates/CLAUDE.md               project memory template
  templates/STATUS.md               ticket status template
```

## Install
- **Claude Code:** copy `skills/ax2009-techno-functional/` to `~/.claude/skills/` (personal) or `<project>/.claude/skills/` (project).
- **Claude apps (claude.ai / desktop / Cowork):** zip the `ax2009-techno-functional` folder and upload it under Settings → Capabilities → Skills.
- **Claude API / Agent SDK:** upload it as a custom skill, following the Anthropic skills documentation.

## Recommended project layout
```
<client>/
  CLAUDE.md                 from templates/CLAUDE.md
  00_Knowledge/             estate map, environments, findings, open items
  01_AOT_Source/<EXPORT>/   original XPO exports (+ UtilElements inventory TSV)
  01_AOT_Source/Split/      output of split_xpo.py
  02_Schema_Metadata/       table/field/index metadata, relations, enums
  03_Runtime_Config/        batch and integration setup captures
  10_Tickets/<id>/STATUS.md
```
Split the AOT:
```
python3 skills/ax2009-techno-functional/scripts/split_xpo.py \
  --out <client>/01_AOT_Source/Split <client>/01_AOT_Source/<EXPORT> \
  --utilelements <client>/01_AOT_Source/<EXPORT>/UtilElements_inventory.tsv
```

## Safety and data
- Keep client code and data **out of this repository**. `.gitignore` blocks common AX export and data file types as a backstop. Don't rely on it alone.
- AOT exports can contain credentials in comments. Treat them as sensitive and get secrets rotated by their owner.
- Every X++ output from Claude says what was checked locally versus compiled and run in AX. Compile and test in a non-production environment before any deployment.

## Roadmap
- D365 F&O companion skill (extensions/CoC, data entities, DMF, LCS/PPAC) for clients migrating from AX 2009
- Generic SQL snippet library (inventory-to-GL reconciliation, settlement consistency, batch history)

## License
MIT. See `LICENSE`. No warranty: you are responsible for reviewing and testing everything before running it in your environment.
