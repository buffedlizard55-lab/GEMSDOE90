"""Synthetic unit tests + committed receipt/ledger integrity for AXIS=CONCENTRATION.

No competition raster is opened by the synthetic tests, so CI can run without
the ignored pinned data. Receipt tests read only committed JSON/CSV.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_concentration_variants as conc_build  # noqa: E402
from src.concentration import (  # noqa: E402
    density_cv,
    region_evenness_report,
    reallocate_to_high_prior,
    structural_prior,
)


def _toy_features(path: Path) -> None:
    h = w = 60
    yy, xx = np.mgrid[0:h, 0:w]
    bands = np.zeros((2, h, w), dtype="float32")
    bands[0] = (xx / 10.0 + yy / 100.0).astype("float32")
    bands[1] = (yy / 10.0 + xx / 100.0).astype("float32")
    profile = dict(
        driver="GTiff", height=h, width=w, count=2, dtype="float32",
        crs="EPSG:32611", transform=from_origin(0, 600, 1, 1), nodata=np.nan,
    )
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(bands)


def test_structural_prior_is_disjoint_and_rank_based(tmp_path: Path) -> None:
    feat = tmp_path / "features.tif"
    _toy_features(feat)
    foot = np.ones((60, 60), dtype=bool)
    foot[:, 55:] = False  # one partly excluded eastern strip
    prior = structural_prior(str(feat), foot, block_px=20, min_foot_frac=0.5, tail_frac=0.25, bands=(1, 2))
    assert prior["meta"]["n_blocks_total"] == 9
    assert prior["meta"]["n_donor_blocks"] >= 2
    assert prior["meta"]["n_recipient_blocks"] >= 2
    assert not np.any(prior["donor_mask"] & prior["recipient_mask"])
    assert prior["meta"]["low_prior_cut"] < prior["meta"]["high_prior_cut"]
    assert np.nanmin(prior["composite"][foot]) > 0.0
    assert np.nanmax(prior["composite"][foot]) < 1.0


def test_reallocate_holds_count_respects_blocks_and_3px_collar() -> None:
    h = w = 40
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    cat[20, :] = True
    dcat = distance_transform_edt(~cat)
    support = np.zeros_like(foot)
    support[5, 4:36] = True
    support[12, 4:36] = True
    support[30, 4:36] = True
    support[35, 4:36] = True
    parent = np.zeros_like(foot)
    parent[5, 4:36:4] = True
    parent[12, 4:36:4] = True
    parent[30, 10] = True
    # Hand-build a tiny two-block prior split at row 20.
    block_id = np.zeros((h, w), dtype=np.int32)
    block_id[20:, :] = 1
    scores = np.array([0.1, 0.9])
    prior = {
        "composite": np.ones((h, w)),
        "block_id": block_id,
        "scores": scores,
        "donor_ids": np.array([0]),
        "recipient_ids": np.array([1]),
        "donor_mask": block_id == 0,
        "recipient_mask": block_id == 1,
        "boxes": [(0, 20, 0, w), (20, h, 0, w)],
        "meta": {"block_px": 20, "n_blocks_total": 2},
    }
    n_parent = int(parent.sum())
    out, stats = reallocate_to_high_prior(parent, support, dcat, prior, n_shift=4)
    assert int(out.sum()) == n_parent
    assert stats["removed_dots"] == 4 and stats["added_dots"] == 4
    added = out & ~parent
    removed = parent & ~out
    assert np.all(prior["recipient_mask"][added])
    assert np.all(prior["donor_mask"][removed])
    assert float(dcat[added].min()) >= 3.0
    assert stats["added_dots_below_3px"] == 0
    assert out.sum() == parent.sum()


def test_region_evenness_gate_accepts_spread_removal_and_rejects_an_empty_block() -> None:
    h = w = 40
    bp = 20
    block_id = np.zeros((h, w), dtype=np.int32)
    block_id[:20, 20:] = 1
    block_id[20:, :20] = 2
    block_id[20:, 20:] = 3
    boxes = [(0, 20, 0, 20), (0, 20, 20, 40), (20, 40, 0, 20), (20, 40, 20, 40)]
    prior = {
        "block_id": block_id,
        "scores": np.array([0.1, 0.2, 0.8, 0.9]),
        "donor_ids": np.array([0, 1]),
        "recipient_ids": np.array([2, 3]),
        "donor_mask": np.isin(block_id, [0, 1]),
        "recipient_mask": np.isin(block_id, [2, 3]),
        "boxes": boxes,
        "meta": {"block_px": bp, "n_blocks_total": 4},
    }
    parent = np.zeros((h, w), dtype=bool)
    for k, (y0, y1, x0, x1) in enumerate(boxes):
        parent[y0:y1:4, x0:x1:4] = True
    # Moderate, distributed removal from both donor blocks.
    cand = parent.copy()
    for k in (0, 1):
        ys, xs = np.nonzero(parent & (block_id == k))
        cand[ys[:4], xs[:4]] = False
    ok = region_evenness_report(parent, cand, prior, nominal_shift_frac=0.2)
    assert ok["pass"]

    # Empty donor block 0 completely: the fail-closed gate must reject it.
    bad = cand.copy()
    ys, xs = np.nonzero(parent & (block_id == 0))
    bad[ys, xs] = False
    rejected = region_evenness_report(parent, bad, prior, nominal_shift_frac=0.2)
    assert not rejected["pass"]
    assert rejected["fraction_donor_blocks_near_emptied"] > 0


def test_receipt_ledger_cards_and_reservations_are_consistent() -> None:
    if not conc_build.RECEIPT_PATH.is_file():
        pytest.skip("concentration receipt not built in this checkout")
    receipt = json.loads(conc_build.RECEIPT_PATH.read_text(encoding="utf-8"))
    cards = json.loads(conc_build.CARDS_PATH.read_text(encoding="utf-8"))
    reservations = json.loads(conc_build.RESERVATIONS_PATH.read_text(encoding="utf-8"))
    assert receipt["axis"] == "CONCENTRATION"
    assert len(receipt["variants"]) == 3
    assert receipt["prior_definition"]["block_km"] == 15.0
    assert not receipt["proxy_reports"]["leakage_canary"]["auc_gt_0_90"]
    assert receipt["proxy_reports"]["catalogue_hide_recover"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["sgmc_control"]["evidence_class"] == "PROXY"

    with conc_build.LEDGER_PATH.open(newline="", encoding="utf-8") as fh:
        all_rows = list(csv.DictReader(fh))
    built = {r["id"]: r for r in all_rows if r["status"] == "BUILT" and r["axis"] == "CONCENTRATION"}
    assert set(built) == {v["id"] for v in receipt["variants"]}
    card_ids = {c["id"] for c in cards["concentration"]["variants"]}
    assert card_ids == set(built)
    tags = [v["tag"] for v in receipt["variants"]]
    assert tags == reservations["concentration_reservations_20261023"]["occupied_tags"]

    seen: list[str] = []
    for row in all_rows:
        for col in ("sha256", "sha256_zeros"):
            if row.get(col, "").strip():
                seen.append(row[col].strip())
    assert len(seen) == len(set(seen))

    for v in receipt["variants"]:
        row = built[v["id"]]
        assert int(row["n_dots"]) == 37_654
        assert row["sha256"] == v["files"]["nan"]["sha256"]
        assert row["sha256_zeros"] == v["files"]["zeros"]["sha256"]
        assert len(v["form_note"]) <= 140
        assert row["form_note"] == v["form_note"]
        assert 1.0 <= v["pct_changed"] <= 50.0
        # 3,765 / 37,654 = 9.9989% and 7,531 / 37,654 = 20.0005% after integer rounding.
        assert 9.99 <= v["mass_shifted_pct"] <= 20.01
        assert float(row["pct_changed"]) == pytest.approx(v["pct_changed"], abs=1e-6)
        assert v["block_density_cv"]["before"] == pytest.approx(receipt["r0_block_density_cv"], abs=1e-6)
        assert v["region_evenness"]["pass"]
        assert v["files"]["nan"]["added_dots_below_3px"] == 0
        assert v["files"]["zeros"]["added_dots_below_3px"] == 0
        assert v["files"]["nan"]["checks"]["all_added_dots_on_h19_support"]
        assert v["files"]["zeros"]["checks"]["all_added_dots_on_h19_support"]


def test_repeated_build_is_stopped_by_reservation_guard() -> None:
    if not conc_build.RECEIPT_PATH.is_file():
        pytest.skip("concentration receipt not built in this checkout")
    with pytest.raises(ValueError, match="duplicate experiment"):
        conc_build.check_concentration_reservations()


def test_15km_cv_helper_uses_density_not_raw_counts() -> None:
    foot = np.ones((300, 300), dtype=bool)
    foot[150:, 150:] = False
    uniform = np.zeros_like(foot)
    for y in range(0, 300, 15):
        for x in range(0, 300, 15):
            if foot[y, x]:
                uniform[y, x] = True
    # At 150 px blocks, a uniform lattice still has a small boundary effect but CV < 0.1.
    assert density_cv(uniform, foot, block_px=150, min_foot_frac=0.5) < 0.1
