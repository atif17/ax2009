# X++ (AX 2009) compile and runtime pitfalls

Each of these came from a real compile or runtime failure.

| Symptom | Fix |
|---|---|
| Syntax error on long pasted/imported lines | Keep every source line **under 200 chars**. Wrap long container literals at value boundaries. |
| "Container …" error in a `where` clause | Unbounded `str` variables can't be used in `where`. Declare bounded strings (`str 60 x;`) or use the EDT (`LedgerJournalId journalId;`). |
| Compiler rejects `forUpdate` + `pessimisticLock` together | Use `select firstonly pessimisticLock …` alone. |
| `IO_Status::EOF` invalid | It doesn't exist in AX 2009. Use the `IO_Status` members that do exist (e.g. `FileTooShort`) and check `status()`. |
| `finalize()` protected-method error on file IO | Don't call `finalize()`. Release the handle with `file = null;`. |
| Compiler stack overflow on a huge container literal | Build it with many small `result += [[a, b, c]];` statements. |
| Error on a variable named `group` | It's a reserved word. Rename it. |
| Statement placed before a declaration | X++ 2009 requires all declarations first. Initialize in the declaration if needed. |
| Field not found on a kernel table (e.g. `UtilElements.Id`) | Check that the field exists in this version's table definition. |
| Base enum not found by AOT path | Use the `#BaseEnumsPath` macro and verify that the element exists. |
| File not found when running on the server tier | Server code can't see client paths. Check `isRunningOnServer()` or run the IO on the client. |

## Framework behavior worth knowing
- `InventSumReCalcItem` defaults to `CheckFix::Fix`. Pass `CheckFix::Check` explicitly for diagnostics.
- `InventTransAdjust.updateNow` adds a **delta**. A zero final target can still need a non-zero delta.
- Native settlement consistency repair can reset adjustments or remove mismatched settlements. Know its effect before you call it.
- If duplicate vouchers are rejected, a correction needs a new voucher from the journal's number sequence (`makeDecisionLater = false`). Keep the original voucher as a reference in the document number or text.
- A GL journal alone does not change inventory valuation. Inventory-side corrections need native inventory paths.

## File formats
- XPO import: UTF-8 **with BOM**, **CRLF**, a header of `Exportfile for AOT version 1.0 or later` + `Formatversion: 1`, and a footer of `***Element: END`.
- Method-text `.xpp`: paste-ready text for one AOT node. It is not importable.
