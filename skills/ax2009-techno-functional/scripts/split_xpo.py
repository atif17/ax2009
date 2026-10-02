#!/usr/bin/env python3
"""Split Dynamics AX 2009 monolithic XPO exports into one importable XPO per AOT object.

Writes <out>/<Type>/<Name>.xpo plus:
  INDEX-objects.tsv         Type, Name, Id, Extends, Layers, Customized, Methods, Lines, File, ...
  INDEX-custom-methods.tsv  class/table methods and fields present in a custom layer
                            (only when --utilelements is given)

Usage:
  python3 split_xpo.py --out ./Split ./FULL_EXPORT [./EXTRA_EXPORT] [--utilelements inventory.tsv]

The UtilElements inventory is a TSV with header: RecordType, Name, ParentId, UtilLevel
(one row per UtilElements record; top-level objects have ParentId 0).
The output folder is wiped and rebuilt on each run. Original exports are never modified.
"""
import argparse, collections, csv, os, re, shutil

HEADER = "﻿Exportfile for AOT version 1.0 or later\r\nFormatversion: 1\r\n\r\n"
FOOTER = "\r\n***Element: END\r\n"
CUSTOM = {"cus", "usr", "var", "vap", "bus", "bup"}

FOLDER = {
    "CLS": "Classes", "DBT": "Tables", "FRM": "Forms", "DBE": "BaseEnums",
    "JOB": "Jobs", "QUE": "Queries", "RG": "Reports", "RGT": "Reports_Templates",
    "RST": "Reports_Templates", "MAP": "Maps", "VIE": "Views", "MCR": "Macros",
    "FTM": "MenuItems", "MNU": "Menus", "SEC": "SecurityKeys", "CON": "ConfigurationKeys",
    "TCL": "TableCollections", "DST": "DataSets", "LIC": "LicenseCodes",
    "PRS": "Perspectives", "REF": "References", "RLB": "ReportLibraries",
    "RES": "Resources", "SVC": "Services",
}
for _c in ["UTD", "UTE", "UTG", "UTI", "UTQ", "UTR", "UTS", "UTT", "UTW", "UTZ"]:
    FOLDER[_c] = "ExtendedDataTypes"

HDR_RE = re.compile(r"^; Microsoft Dynamics AX (.+?): (.+?) unloaded\s*$", re.M)
NAME_RE = re.compile(r"^\s+Name\s+#(.+?)\s*$", re.M)
ID_RE = re.compile(r"^\s+Id\s+(\d+)\s*$", re.M)
EXT_RE = re.compile(r"^\s+Extends\s+#(.*?)\s*$", re.M)
SRC_RE = re.compile(r"^\s+SOURCE #(\S+)\s*$", re.M)
BAD = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

TOP = {"Class": "Classes", "Table": "Tables", "Form": "Forms", "Report": "Reports",
       "Query": "Queries", "Job": "Jobs", "Enum": "BaseEnums", "ExtendedType": "ExtendedDataTypes",
       "TableMap": "Maps", "DisplayTool": "MenuItems", "ActionTool": "MenuItems",
       "OutputTool": "MenuItems", "Macro": "Macros", "View": "Views", "SecurityKey": "SecurityKeys"}
CHILD = {"ClassInstanceMethod": "Classes", "ClassStaticMethod": "Classes",
         "TableInstanceMethod": "Tables", "TableStaticMethod": "Tables", "TableField": "Tables"}


def safe(name):
    return BAD.sub("_", name).strip() or "_unnamed"


def folder_for(code, xpo_name):
    base = os.path.splitext(xpo_name)[0]
    if base.lower() in ("web", "workflow"):
        return f"{base.capitalize()}/{code}"
    return FOLDER.get(code, code)


def split(sources, out):
    rows, seen = [], collections.Counter()
    for src in sources:
        for fn in sorted(os.listdir(src)):
            if not fn.lower().endswith(".xpo"):
                continue
            text = open(os.path.join(src, fn), encoding="utf-8-sig", newline="").read()
            for part in re.split(r"(?m)^(?=\*\*\*Element: )", text):
                m = re.match(r"\*\*\*Element: (\S+)", part)
                if not m or m.group(1) == "END":
                    continue
                code = m.group(1)
                h = HDR_RE.search(part)
                if h:
                    kind, name = h.group(1), h.group(2)
                else:
                    n = NAME_RE.search(part)
                    kind, name = code, (n.group(1) if n else "_unnamed")
                folder = folder_for(code, fn)
                key = (folder, name.lower())
                seen[key] += 1
                fname = safe(name) + ("" if seen[key] == 1 else f"__{seen[key]}") + ".xpo"
                os.makedirs(os.path.join(out, folder), exist_ok=True)
                body = part.rstrip("\r\n")
                with open(os.path.join(out, folder, fname), "w", encoding="utf-8", newline="") as f:
                    f.write(HEADER + body + FOOTER)
                idm = ID_RE.search(part)
                ext = EXT_RE.search(part) if code == "CLS" else None
                rows.append({
                    "Type": folder, "Kind": kind, "Name": name,
                    "Id": idm.group(1) if idm else "", "Extends": ext.group(1) if ext else "",
                    "Methods": len(SRC_RE.findall(part)), "Lines": body.count("\n") + 1,
                    "File": f"{folder}/{fname}", "SourceExport": f"{os.path.basename(src)}/{fn}",
                    "Layers": "", "Customized": "",
                })
    return rows


def add_layers(rows, inventory):
    top = collections.defaultdict(set)
    child = []
    with open(inventory, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rt, nm, pid, lvl = r["RecordType"], r["Name"], r["ParentId"], r["UtilLevel"]
            if rt in TOP and pid == "0":
                top[(TOP[rt], nm.lower())].add(lvl)
            elif rt in CHILD:
                child.append((CHILD[rt], pid, rt, nm, lvl))
    by_id = {(r["Type"], r["Id"]): r for r in rows if r["Id"]}
    child_layers = collections.defaultdict(set)
    for typ, pid, rt, nm, lvl in child:
        obj = by_id.get((typ, pid))
        if obj:
            child_layers[(obj["File"], rt, nm)].add(lvl)
    custom_rows, touched = [], collections.defaultdict(set)
    for (file, rt, nm), lv in sorted(child_layers.items()):
        if lv & CUSTOM:
            custom_rows.append([file.split("/")[0], file.split("/", 1)[1][:-4], rt, nm,
                                ",".join(sorted(lv)), file])
            touched[file] |= lv
    for r in rows:
        lay = top.get((r["Type"], r["Name"].lower()), set()) | touched.get(r["File"], set())
        r["Layers"] = ",".join(sorted(lay))
        r["Customized"] = "Y" if lay & CUSTOM else ""
    return custom_rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+", help="folders containing .xpo exports")
    ap.add_argument("--out", required=True, help="output folder (wiped and rebuilt)")
    ap.add_argument("--utilelements", help="optional UtilElements inventory TSV for layer info")
    a = ap.parse_args()
    if os.path.isdir(a.out):
        shutil.rmtree(a.out)
    os.makedirs(a.out)
    rows = split(a.sources, a.out)
    custom_rows = add_layers(rows, a.utilelements) if a.utilelements else []
    cols = ["Type", "Name", "Id", "Extends", "Layers", "Customized", "Methods", "Lines",
            "File", "Kind", "SourceExport"]
    with open(os.path.join(a.out, "INDEX-objects.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(cols)
        for r in sorted(rows, key=lambda r: (r["Type"], r["Name"].lower())):
            w.writerow([r[c] for c in cols])
    if a.utilelements:
        with open(os.path.join(a.out, "INDEX-custom-methods.tsv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["Type", "Object", "ElementKind", "Element", "Layers", "File"])
            w.writerows(custom_rows)
    counts = collections.Counter(r["Type"].split("/")[0] for r in rows)
    cust = collections.Counter(r["Type"].split("/")[0] for r in rows if r["Customized"])
    print(f"{len(rows)} objects written to {a.out}")
    for k in sorted(counts):
        print(f"  {k:<20}{counts[k]:>7}" + (f"  customized={cust[k]}" if a.utilelements else ""))


if __name__ == "__main__":
    main()
