#!/usr/bin/env python3
"""Write/refresh the three MASS rows in ledger/submissions.csv from the build receipt.

Idempotent: rows are keyed on (axis, value) with axis MASS and parent h33-h33-2-b2,
so re-running replaces those rows and never duplicates them. Historical rows and the
PRUNE rows from the earlier session are preserved byte-for-byte in place.

receipt_score / date are left empty on purpose: only the human can paste a
submission-page receipt. The agent never submits.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "submissions.csv"
FIELDS = ["id", "site", "name", "score", "evidence_class", "encoding", "n_dots", "pct_changed",
          "sha256", "sha256_zeros", "parent", "axis", "value", "status", "receipt",
          "receipt_score", "predicted_change", "date", "form_note", "notes"]


def main() -> int:
    receipt = json.loads((ROOT / "evidence" / "build_receipt_mass.json").read_text())
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        existing = [row for row in reader]
        fields = reader.fieldnames or FIELDS
    mine = {(r.get("axis"), r.get("value")) for r in existing
            if (r.get("axis") or "").upper() == "MASS"
            and (r.get("parent") or "") == receipt["parent"]["id"]
            and (r.get("site") or "") == "GEMSDOE90"}
    kept = [r for r in existing
            if not ((r.get("axis") or "").upper() == "MASS"
                    and (r.get("parent") or "") == receipt["parent"]["id"]
                    and (r.get("site") or "") == "GEMSDOE90")]

    notes = {
        "fifo20": "collar d_cat>=3px (1,611 dots, identical in all three) + 7,531 lowest "
                  "FIFO-BFS-ranked dots; dropped dots average the same unique credit as the kept "
                  "set, so this is a near-arbitrary 20% mass cut (the brief-literal control)",
        "uniq20": "collar + 7,531 lowest unique-300m-kernel-credit dots at the SAME count as "
                  "fifo20; dropped mean unique credit 1.00 vs 2.29 kept",
        "uniq30": "collar + 11,296 lowest unique-credit dots; dose response beyond uniq20",
    }
    rows = []
    for v in receipt["variants"]:
        note = (f"{receipt['parent']['id']}; MASS {v['value']}: drop {v['dose_dots']:,} "
                f"{'FIFO-rank' if v['value'].startswith('fifo') else 'least-unique-credit'} dots "
                f"+ 3px collar; pred {v['predicted_change'].split(' (')[0]} MODEL")
        assert len(note) <= 140, (len(note), note)
        rows.append({
            "id": v["id"],
            "site": "GEMSDOE90",
            "name": v["id"],
            "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback",
            "n_dots": v["n_dots"],
            "pct_changed": f"{v['pct_changed_vs_r0']:.6f}",
            "sha256": v["sha256"],
            "sha256_zeros": v["sha256_zeros"],
            "parent": receipt["parent"]["id"],
            "axis": receipt["axis"],
            "value": v["value"],
            "status": "BUILT",
            "receipt": "N",
            "receipt_score": "",
            "predicted_change": v["predicted_change"],
            "date": "",
            "form_note": note,
            "notes": notes[v["value"]],
        })

    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in kept + rows:
            writer.writerow({k: row.get(k, "") for k in fields})

    cards = {
        "schema_version": 1,
        "parent": receipt["parent"]["id"],
        "axis": receipt["axis"],
        "collar_policy": receipt["collar_policy"],
        "variants": [{"id": v["id"], "value": v["value"], "mechanism_card": v["mechanism_card"]}
                     for v in receipt["variants"]],
    }
    (ROOT / "ledger" / "mechanism_cards_mass.json").write_text(
        json.dumps(cards, indent=2) + "\n", encoding="utf-8")
    print(f"ledger rows: {len(kept)} kept + {len(rows)} MASS; existing MASS rows replaced: "
          f"{len(mine)}")
    for r in rows:
        print(f"  {r['id']}: n={r['n_dots']} pct={r['pct_changed']} note={len(r['form_note'])}ch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
