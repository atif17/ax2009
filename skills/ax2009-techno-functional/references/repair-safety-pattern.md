# Data-repair safety pattern

Use this for any X++ that writes business data (inventory, settlements, GL). It was proven on multi-stage inventory/GL repairs run on a refreshed test copy of production.

## Modes
| Mode | Writes | Purpose |
|---|---|---|
| `PREVIEW` (default) | none | Checks every guard and prints the exact plan (records, amounts, accounts, dimensions, date) plus a state-bound token |
| `ROLLBACK_TEST` | inside `ttsBegin … ttsAbort` | Runs the real write path, verifies the expected result inside the transaction, aborts, and asserts the original state is restored |
| `APPLY` | one outer `ttsCommit` | Runs only when the supplied token matches a fresh hash of the live state |

## Token
Hash the exact target RecIds, RecVersions, key field values, planned amounts and posting date. If anything changed since PREVIEW, APPLY refuses. Tokens are never reused across refreshes, environments or code changes.

## Guards
- Environment: allowed `@@SERVERNAME`/database/company only. Production is blocked unless a separate release says otherwise.
- Exact source records with expected values. Stop on any mismatch, and never weaken a failing check just to make it run.
- Duplicate markers in journal header, journal line and GL text, so a second run is detected.
- Preservation checks: rows and fields outside the target must be unchanged (compare snapshots).
- Period open, accounts valid, dimensions valid, balanced voucher.

## Rules
- Never turn a rollback test into APPLY by replacing `ttsAbort` with `ttsCommit`. APPLY is its own reviewed branch.
- After "COMMIT ATTEMPT", a client crash or any uncertain outcome, **do not rerun**. Inspect the persisted state and server sessions first. Closing the client doesn't stop the server.
- If a later check fails after a financial commit, it does not undo the postings. Recover separately, with its own guards. Never rerun the financial step.
- Number-sequence gaps after rollback tests are expected.
- Independent verification: run a read-only SQL AFTER capture (labeled grids) and the business report (e.g. Inventory Value Report). The class's Infolog alone is not proof.
- Report clearly what was tested locally vs compiled vs executed in AX.

## User-facing run steps (template)
1. Import the XPO (or paste the method text) and compile. Send any compiler errors exactly.
2. Run PREVIEW and send the full Infolog, including the token.
3. After review, set `ROLLBACK_TEST` with that token, run once and send the Infolog.
4. Set `APPLY` with the same token (if the state is unchanged), run **once** and send the Infolog.
5. Run the AFTER SQL and the business report, then send both.
