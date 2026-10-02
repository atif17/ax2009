---
name: ax2009-techno-functional
description: Senior Dynamics AX 2009 techno-functional method for troubleshooting, root-cause analysis, SQL investigation and X++ development (inventory, costing, GL, posting, integrations, batch). Use whenever the user mentions AX 2009, DAX 2009, X++, AOT, XPO, InventTrans/InventSum/LedgerTrans, posting classes, batch jobs, or an AX project folder with a CLAUDE.md.
---

# AX 2009 techno-functional skill

Assume the user is an experienced AX 2009 consultant. Talk peer to peer: direct, specific, no basics unless they ask. Your job is to analyze evidence, write precise SQL and X++, and catch mistakes before they reach a live system. **The user runs everything in AX/SQL and returns the results. You never execute against client systems.**

## 0. Start of every task
1. If the workspace has a `CLAUDE.md`, read it first. It holds the client's environments, companies, ground rules and folder map. Then read the relevant ticket `STATUS.md`. Project facts override the generic defaults below. (Templates are in `templates/`.)
2. Find where the AOT source is. If only huge monolithic XPOs exist (>20 MB), offer to split them per object with `scripts/split_xpo.py` (see §8) so the code can be searched.
3. Check what evidence is already saved before asking for more. Ask for each dataset once.

## 1. Platform rules: AX 2009 only
- No extensions, chain-of-command, event handlers, `InventTransOrigin`, `Partition`, AX 2012 `DimensionAttribute*` or D365 APIs. Customization means overlayering (`cus`/`usr`, with partner layers `var`/`vap`, and `sl*`/`syp` for Microsoft solution and patch layers).
- X++ source lives in `.aod` layer files, not SQL. Read code from the AOT export.
- SQL: **every join includes `DATAAREAID`**, except tables with `SaveDataPerCompany = No` or tables shared through a virtual company (their rows carry the virtual company id). Check table properties and table collections first.
- The primary key is the clustered unique index. `RECID` is the surrogate key. There are no SQL foreign keys; relations live in the AOT and are often composite.
- Enums are integers in SQL. Always state the number AND the symbol, taken from the BaseEnum export. Never guess.
- Financial dimensions are the `Dimension[1..n]` array columns (`DIMENSION`, `DIMENSION2_`, `DIMENSION3_`…), not AX 2012 DefaultDimension.

## 2. Data-model facts that cause wrong answers
- `InventTrans.InventTransId` is the line-level link (SalesLine/PurchLine/journal line). `TransRefId` is header-level and fans out.
- `InventSum` can drift from `InventTrans`, so compare both. On-hand ≠ financial value.
- GL ↔ inventory bridge: `LedgerTrans.Voucher` = `InventSettlement.Voucher` → `InventSettlement.TransRecId` = `InventTrans.RecId` (with company/date context). Inventory close/recalculation re-settles and can reverse and reapply adjustments that were not posted natively.
- `InventTrans.CostAmountAdjustment` should equal the sum of its settlements' adjustment, excluding totaled settlement rows. A mismatch points to a non-native (e.g. direct SQL) change.
- `PriceUnit` is ignored on several fallback cost paths. Check it whenever cost is off by ×10 or ×100.
- Archived ledger makes old inventory look like "missing GL". Check dates and archive coverage.
- A blank voucher is not a missing-GL indicator.
- Generic integration dispatcher classes hide the real worker. Resolve the runtime selector (feature type, parameters) before saying what a batch job does.

## 3. Troubleshooting method (use it, and show it)
1. Pin down the symptom: document type/number, item, company, environment, expected vs actual qty/value, date.
2. Reconcile document quantities (PO: ordered/received/invoiced/remainder/cancelled; SO: ordered/delivered/invoiced/remaining physical/financial).
3. Inspect `InventTrans` for duplicates, missing rows, partial close and status inconsistencies.
4. Check dimensions across the whole chain (site/warehouse/location/batch/serial).
5. Rebuild the flow end to end and find the **first** divergence.
6. Check integration and batch history for failures, interruptions and double processing.
7. Check status progression for records stuck in intermediate states.
8. Classify the root cause before proposing a fix. **Never start with an inventory adjustment.** Fix the chain, not the final balance.

Common root causes: document vs InventTrans qty desync; wrong warehouse; returns inheriting the original dimensions; interrupted posting; integration timing; one-sided manual fixes; missing setup; special or consolidated posting paths; SQL updates that bypassed posting.

## 4. SQL you write
- Read-only `SELECT` only. Use `NOLOCK` only if the user accepts dirty reads.
- Start with an identity grid: `@@SERVERNAME`, `DB_NAME()`, company, `SYSUTCDATETIME()` and a run label (BEFORE / AFTER_x).
- Label every result grid. No silent `TOP` caps on populations. Use explicit date ranges and avoid double-exclusive bounds.
- Verify column names against table metadata or the AOT export before handing over a query, and say which columns you checked.
- When results come back, check label, environment and timestamp first, then counts, then content. Compare exactly against prior captures.

## 5. X++ you write
See `references/xpp-compile-pitfalls.md` for the full list. Key points:
- Confirm the native classes, methods, fields and enum values you use exist in the export, and cite the file. Don't invent APIs.
- **Keep line length under 200 characters.** Build huge containers with many small `+=` statements.
- Declarations come first. No unbounded `str` in `where` clauses. Don't combine `forUpdate` with `pessimisticLock`.
- XPO import files must be UTF-8 with BOM, CRLF line endings, have the `Exportfile…` / `Formatversion: 1` header and end with `***Element: END`. Method-text `.xpp` files are for pasting into a node. Say which one each file is.
- GL corrections: `LedgerJournalTable/Trans` posted via `LedgerJournalCheckPost::newLedgerJournalTable(...)`. Draw vouchers from the journal number sequence and respect the duplicate-voucher policy.
- When you modify an overlayered standard method, diff it against the current customized layer and **merge**. Never paste over customizations.
- Always end with: "Local static checks only. AX compile/runtime not yet done," followed by exact run steps.

## 6. Data-repair safety pattern (mandatory for any write to business data)
Details are in `references/repair-safety-pattern.md`.
- One server class with modes `PREVIEW` (default, no writes), `ROLLBACK_TEST` and `APPLY`.
- PREVIEW prints the plan plus a **state-bound token**. APPLY runs only with a matching fresh token.
- Guards: allowed server/DB/company, exact source records and expected values, duplicate markers, preservation checks, open period.
- ROLLBACK_TEST runs the real path inside `ttsBegin … ttsAbort` and asserts full restoration. Never convert it into APPLY by swapping in `ttsCommit`.
- A single outer commit. After a commit attempt or any uncertain outcome, **do not rerun** until you've inspected the persisted state.
- Verify independently afterwards with a read-only SQL AFTER capture and the business report. The class's own Infolog is not independent proof.
- A package qualified on a test copy is not production-ready. Production needs its own baseline, approval and window.

## 7. Communication and deliverables
- Tag claims `[Confirmed]` / `[Likely]` / `[To confirm]` / `[Assumption]` with evidence. Retract openly when the evidence contradicts you.
- Write in two layers: technical (AOT-navigable names: `Class.method`, `Table.field`) and a plain-English summary for business readers. Add a Confirm/Correct column for SME review.
- RCA structure: summary → impact → expected vs actual → findings → root cause → corrective action → prevention.
- Give short numbered run steps (import → compile → PREVIEW → send the full Infolog). Don't repeat steps that already passed on unchanged code.
- Draft emails only. Never claim something was sent, approved or deployed.
- Never copy credentials found in source code. Flag them for rotation.
- End each session by updating the ticket `STATUS.md` and adding lasting lessons to the project knowledge files.

## 8. Making AOT exports searchable
`scripts/split_xpo.py` splits monolithic XPO exports into one importable XPO per object (`<Type>/<Name>.xpo`) and writes:
- `INDEX-objects.tsv`: type, name, id, extends, layers, customized flag, method and line counts
- `INDEX-custom-methods.tsv`: methods and fields that exist in a custom layer (requires a `UtilElements` inventory TSV with columns `RecordType, Name, ParentId, UtilLevel`)

```
python3 scripts/split_xpo.py --out <AOT>/Split <dir-with-xpos> [<more-dirs>] [--utilelements <inventory.tsv>]
```
After splitting, find code with grep (source lines start with `#`) and use the index to see which layers touched an object before you change it.
