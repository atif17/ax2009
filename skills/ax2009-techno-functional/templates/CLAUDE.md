# <Client> AX 2009: project memory (read first)

Microsoft Dynamics **AX 2009** at <client>. Scope: <AX only / AX + D365>. Owners of other systems: <vendor / team>.
Use the `ax2009-techno-functional` skill for general method. This file holds project specifics only. Keep it under one page.

## Ground rules
1. Read-only by default. Never run, post, deploy or email. The consultant executes and returns results.
2. Production is never a test target. Test on <TEST/UAT/refreshed copy> with a guarded PREVIEW → ROLLBACK_TEST → APPLY class.
3. Code is the tie-breaker. Look up the real source in `01_AOT_Source/Split/` before claiming behavior.
4. Tag claims `[Confirmed]/[Likely]/[To confirm]/[Assumption]`.
5. Don't ask for data that is already saved. Check the ticket's `STATUS.md` and `Runs/` first.
6. Never copy credentials found in source code.
7. At the end of a session, update the ticket's `STATUS.md` and the right `00_Knowledge/` file.

## Folder map
| Folder | What |
|---|---|
| `00_Knowledge/` | estate-map, environments-and-people, technical-findings, working-method, open-items |
| `01_AOT_Source/Split/` | one XPO per object + `INDEX-objects.tsv` + `INDEX-custom-methods.tsv` |
| `01_AOT_Source/<EXPORT>/` | original monolithic exports + UtilElements inventory |
| `02_Schema_Metadata/` | table/field/index metadata, relations, enums, batch class list |
| `03_Runtime_Config/` | batch setup, integration schedules/parameters/watermarks |
| `04_Reference_Docs/` | design docs, process docs |
| `05_Tools_Collectors/` | extraction jobs, collectors, split script |
| `10_Tickets/<id>/` | one folder per issue, each with `STATUS.md` |

## Environments
| Name | Server / DB | Use |
|---|---|---|
| PROD | <server> / <db> | read-only |
| TEST | <server> / <db> | testing |

## Companies
Live: `<id>`. Virtual/shared: `<id>`. Closed with history: `<ids>`.

## Active tickets
- **<ID> <title>**: <one-line state>. See STATUS.md.

## Quick facts
<duplicate voucher policy, key accounts, posting windows, freeze periods>
