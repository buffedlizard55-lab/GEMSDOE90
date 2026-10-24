"""Leakage canaries, unsupervised physics operator (Exp 1), nested single-quadrant
LOQO 2D spatial-worm multi-physics ensemble (Exp 2), and simulated-split Coulomb
tip/relay synthesis (Exp 3) for Lane H90.
"""

from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score

from vendor.gems57.holdout import Cell, DOMAIN_ERODE, HoldoutContext, quadrant_ids
from vendor.gems57.network import segments

from .h90_features import (
    DOMAIN_SLICES,
    STATIC_FEATURE_NAMES,
    VISIBLE_FEATURE_NAMES,
    compute_fold_visible_coulomb_features,
    steerable_line_anisotropy,
)

STAGE2_FEATURE_NAMES: tuple[str, ...] = (
    "p_joint",
    "p_pot",
    "p_morph",
    "p_hydro",
    "second_best_domain",
    "domain_geom_mean",
    "p_joint_g1_5",
    "p_joint_g4",
    "p_joint_g10",
    "p_joint_dog_sharp",
    "worm_along_800m",
    "worm_aniso_800m",
    "worm_along_1800m",
    "worm_aniso_1800m",
    "ctx_depth_base",
    "ctx_lid_valid",
)


def _rank01(vals: np.ndarray) -> np.ndarray:
    """Finite rank-percentile in [0, 1], mapping NaNs to median 0.5."""
    out = np.full(vals.shape, 0.5, dtype=np.float32)
    fin = np.isfinite(vals)
    n = int(fin.sum())
    if n > 1:
        out[fin] = ((rankdata(vals[fin], method="average") - 1.0) / (n - 1.0)).astype(np.float32)
    return out


def run_leakage_canary(
    X_fp: np.ndarray,
    ctx: HoldoutContext,
    *,
    auc_limit: float = 0.90,
    max_neg_sample: int = 250_000,
    seed: int = 90501,
) -> dict:
    """Protocol Rule #4: test EVERY feature alone on the hide-and-recover holdout."""
    fp = ctx.grid.footprint
    H, W = fp.shape
    fp_idx_map = np.full((H, W), -1, dtype=np.int32)
    fp_idx_map[fp] = np.arange(int(fp.sum()), dtype=np.int32)

    rng = np.random.default_rng(seed)
    pos_fp_indices = []
    neg_fp_indices = []
    vis_feats_pos = []
    vis_feats_neg = []

    primary_cells = [c for c in ctx.cells if c.seed == 20 and c.mode == "all"]
    neg_per_fold = max(max_neg_sample // max(len(primary_cells), 1), 1000)

    for cell in primary_cells:
        vis = ctx.visible(cell.key)
        _, d_clip_fp, tip_fp, relay_fp = compute_fold_visible_coulomb_features(vis, fp)

        sy, sx = cell.bbox
        act_crop = cell.active
        truth_crop = np.zeros_like(act_crop, dtype=bool)
        truth_crop[cell.truth_yx] = True
        neg_crop = act_crop & ~truth_crop

        py, px = np.nonzero(truth_crop)
        ny, nx = np.nonzero(neg_crop)
        if ny.size > neg_per_fold:
            pick = rng.choice(ny.size, size=neg_per_fold, replace=False)
            ny, nx = ny[pick], nx[pick]

        p_idx = fp_idx_map[py + sy.start, px + sx.start]
        n_idx = fp_idx_map[ny + sy.start, nx + sx.start]
        p_idx = p_idx[p_idx >= 0]
        n_idx = n_idx[n_idx >= 0]

        pos_fp_indices.append(p_idx)
        neg_fp_indices.append(n_idx)
        vis_feats_pos.append(np.column_stack([tip_fp[p_idx], relay_fp[p_idx]]))
        vis_feats_neg.append(np.column_stack([tip_fp[n_idx], relay_fp[n_idx]]))

    pos_all = np.concatenate(pos_fp_indices)
    neg_all = np.concatenate(neg_fp_indices)
    y = np.concatenate([np.ones(pos_all.size, dtype=np.int8), np.zeros(neg_all.size, dtype=np.int8)])
    idx_all = np.concatenate([pos_all, neg_all])
    vis_mat = np.vstack([np.vstack(vis_feats_pos), np.vstack(vis_feats_neg)])

    rows = []
    for j, name in enumerate(STATIC_FEATURE_NAMES):
        col = np.asarray(X_fp[idx_all, j], dtype=np.float32)
        fin = np.isfinite(col)
        if fin.sum() < 50 or len(np.unique(y[fin])) < 2 or np.ptp(col[fin]) == 0:
            auc = 0.5
        else:
            auc = float(roc_auc_score(y[fin], col[fin]))
        sym_auc = max(auc, 1.0 - auc)
        rows.append(
            {
                "feature": name,
                "group": "static_multiphysics",
                "n_valid_eval": int(fin.sum()),
                "auc": round(auc, 6),
                "symmetric_auc": round(sym_auc, 6),
                "limit": auc_limit,
                "passed": bool(sym_auc <= auc_limit),
            }
        )

    for k, name in enumerate(VISIBLE_FEATURE_NAMES):
        col = vis_mat[:, k]
        fin = np.isfinite(col)
        if fin.sum() < 50 or len(np.unique(y[fin])) < 2 or np.ptp(col[fin]) == 0:
            auc = 0.5
        else:
            auc = float(roc_auc_score(y[fin], col[fin]))
        sym_auc = max(auc, 1.0 - auc)
        rows.append(
            {
                "feature": name,
                "group": "fold_visible_coulomb",
                "n_valid_eval": int(fin.sum()),
                "auc": round(auc, 6),
                "symmetric_auc": round(sym_auc, 6),
                "limit": auc_limit,
                "passed": bool(sym_auc <= auc_limit),
            }
        )

    worst = max(rows, key=lambda r: r["symmetric_auc"])
    failed = [r for r in rows if not r["passed"]]
    report = {
        "protocol_rule": "Rule 4 single-feature holdout leakage canary",
        "evaluator_version": "gems57-pooled-hide-v2 (draw20 primary 4-quadrant split)",
        "n_withheld_positives_tested": int(pos_all.size),
        "n_active_negatives_sampled": int(neg_all.size),
        "auc_limit": auc_limit,
        "features_tested": len(rows),
        "max_symmetric_auc": worst["symmetric_auc"],
        "max_symmetric_auc_feature": worst["feature"],
        "failed_features": [r["feature"] for r in failed],
        "all_passed": len(failed) == 0,
        "ir90_46_preflight_note": (
            "Initial pre-training canary flagged collinear r>2.0 px cut-end tip cone at AUC=0.906243 "
            "due to synthetic 12-px segment holes in mode='all'; replaced before any model training "
            "with off-axis r>4.5 px Mode-II wing-crack lobes on major trunks (>=2.5 km)."
        ),
        "features": rows,
    }
    if failed:
        raise RuntimeError(f"Leakage canary failed (> {auc_limit}): {failed}")
    return report


def build_classical_ridge_surface(X_fp: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Comparator C1: simple isotropic standardized average of tmi_hg + grav_hg + det_elev_slope."""
    raw = (
        _rank01(np.asarray(X_fp[:, STATIC_FEATURE_NAMES.index("b03_tmi_hg_log")]))
        + _rank01(np.asarray(X_fp[:, STATIC_FEATURE_NAMES.index("b18_grav_hg_log")]))
        + _rank01(np.asarray(X_fp[:, STATIC_FEATURE_NAMES.index("b19_det_elev_slope")]))
    ) / np.float32(3.0)
    out = np.zeros(footprint.shape, dtype=np.float32)
    out[footprint] = np.clip(raw, 0.0, 1.0)
    return out


def build_exp1_unsupervised_surface(X_fp: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Experiment 1 (H90-1a): Zero-label multi-domain odd-step + demagnetization trough operator."""
    idx = {name: i for i, name in enumerate(STATIC_FEATURE_NAMES)}

    pot_raw = (
        0.25 * _rank01(np.asarray(X_fp[:, idx["rtp_odd_step_ratio"]]))
        + 0.25 * _rank01(np.asarray(X_fp[:, idx["grav_odd_step_ratio"]]))
        + 0.20 * _rank01(np.asarray(X_fp[:, idx["gallardo_crossgrad_collin"]]))
        + 0.15 * _rank01(np.asarray(X_fp[:, idx["cover_potfield_coupling"]]))
        + 0.15 * _rank01(np.asarray(X_fp[:, idx["b06_tc_zero_prox"]]))
    )
    s_pot = _rank01(pot_raw)

    has_lid = np.asarray(X_fp[:, idx["lid_valid"]]) > 0.5
    morph_base = (
        0.40 * _rank01(np.asarray(X_fp[:, idx["elev_odd_step_ratio"]]))
        + 0.30 * _rank01(np.asarray(X_fp[:, idx["elev_lap_dipole"]]))
        + 0.30 * _rank01(np.asarray(X_fp[:, idx["b19_det_elev_slope"]]))
    )
    morph_lid = (
        0.30 * _rank01(np.asarray(X_fp[:, idx["lid_scarp_dipole"]]))
        + 0.30 * _rank01(np.asarray(X_fp[:, idx["lid_tect_vs_fluv"]]))
        + 0.20 * _rank01(np.asarray(X_fp[:, idx["lid_face_asymmetry"]]))
        + 0.20 * morph_base
    )
    s_morph = _rank01(np.where(has_lid, morph_lid, morph_base))

    hydro_raw = (
        0.28 * _rank01(np.asarray(X_fp[:, idx["demag_up150_deficit"]]))
        + 0.22 * _rank01(np.asarray(X_fp[:, idx["rad_alteration_grad"]]))
        + 0.20 * _rank01(np.asarray(X_fp[:, idx["b17_cond_grad"]]))
        + 0.15 * _rank01(np.asarray(X_fp[:, idx["gdr_geotherm_halo_near"]]))
        + 0.15 * _rank01(np.asarray(X_fp[:, idx["transtension_index"]]))
    )
    s_hydro = _rank01(hydro_raw)

    stack = np.sort(np.column_stack([s_pot, s_morph, s_hydro]), axis=1)
    second_best = stack[:, 1]
    top_best = stack[:, 2]
    pixel_comb = top_best * (np.float32(0.20) + np.float32(0.80) * second_best)

    grid_p = np.zeros(footprint.shape, dtype=np.float32)
    grid_p[footprint] = pixel_comb
    worm800, aniso800 = steerable_line_anisotropy(grid_p, footprint, half_len_px=8, n_taps_half=3, n_angles=8)
    final_fp = np.clip(
        0.55 * pixel_comb + 0.30 * worm800[footprint] + 0.15 * np.maximum(aniso800[footprint], 0.0),
        0.0,
        1.0,
    ).astype(np.float32)
    out = np.zeros(footprint.shape, dtype=np.float32)
    out[footprint] = final_fp
    return out


def _predict_proba_chunked(model: HistGradientBoostingClassifier, X: np.ndarray, chunk: int = 800_000) -> np.ndarray:
    n = X.shape[0]
    out = np.empty(n, dtype=np.float32)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        out[s:e] = model.predict_proba(np.asarray(X[s:e], dtype=np.float32))[:, 1].astype(np.float32)
    return out


def _build_stage2_features_on_mask(
    p_joint_fp: np.ndarray,
    p_pot_fp: np.ndarray,
    p_morph_fp: np.ndarray,
    p_hydro_fp: np.ndarray,
    X_fp: np.ndarray,
    footprint: np.ndarray,
    allowed_2d: np.ndarray,
) -> np.ndarray:
    """Compute 16 Stage-2 2D multi-scale & steerable worm features sequentially (low RAM)."""
    n_fp = int(footprint.sum())
    S2 = np.empty((n_fp, len(STAGE2_FEATURE_NAMES)), dtype=np.float32)
    S2[:, 0] = p_joint_fp
    S2[:, 1] = p_pot_fp
    S2[:, 2] = p_morph_fp
    S2[:, 3] = p_hydro_fp

    dom_sorted = np.sort(np.column_stack([p_pot_fp, p_morph_fp, p_hydro_fp]), axis=1)
    S2[:, 4] = dom_sorted[:, 1]
    S2[:, 5] = np.cbrt(np.maximum(p_pot_fp * p_morph_fp * p_hydro_fp, 0.0)).astype(np.float32)
    del dom_sorted

    pj_2d = np.zeros(footprint.shape, dtype=np.float32)
    pj_2d[footprint] = p_joint_fp
    pj_2d[~allowed_2d] = 0.0

    g1_5 = ndi.gaussian_filter(pj_2d, sigma=1.5, mode="constant", cval=0.0)
    S2[:, 6] = g1_5[footprint]
    g6 = ndi.gaussian_filter(pj_2d, sigma=6.0, mode="constant", cval=0.0)
    S2[:, 9] = (g1_5 - g6)[footprint]
    del g1_5, g6

    g4 = ndi.gaussian_filter(pj_2d, sigma=4.0, mode="constant", cval=0.0)
    S2[:, 7] = g4[footprint]
    del g4

    g10 = ndi.gaussian_filter(pj_2d, sigma=10.0, mode="constant", cval=0.0)
    S2[:, 8] = g10[footprint]
    del g10

    w8, a8 = steerable_line_anisotropy(pj_2d, allowed_2d, half_len_px=8, n_taps_half=3, n_angles=8)
    S2[:, 10] = w8[footprint]
    S2[:, 11] = a8[footprint]
    del w8, a8

    w18, a18 = steerable_line_anisotropy(pj_2d, allowed_2d, half_len_px=18, n_taps_half=4, n_angles=8)
    S2[:, 12] = w18[footprint]
    S2[:, 13] = a18[footprint]
    del pj_2d, w18, a18

    S2[:, 14] = np.asarray(X_fp[:, STATIC_FEATURE_NAMES.index("b15_depth_base_log")], dtype=np.float32)
    S2[:, 15] = np.asarray(X_fp[:, STATIC_FEATURE_NAMES.index("lid_valid")], dtype=np.float32)
    return S2


def fit_predict_exp2_and_exp3(
    X_fp: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    cache_dir: Path | None = None,
    *,
    seed: int = 90701,
) -> dict:
    """Memory-lean nested single-quadrant LOQO Stage-1 + Stage-2 (Exp 2) and simulated-split
    Coulomb tip/relay Stage-3 (Exp 3). Peak RSS < 950 MB.

    Each Stage-1 base ensemble E_k (k in 0..3) is trained strictly on eroded quadrant k.
    - Stage-2 training on quadrant r != q uses average({E_s : s not in {q, r}}) (strictly OOF wrt q and r).
    - Stage-2 testing on held-out quadrant q uses average({E_s : s != q}) (strictly OOF wrt q).
    """
    fp = np.asarray(footprint, dtype=bool)
    cat = np.asarray(catalogue, dtype=bool)
    quad_2d = quadrant_ids(fp)
    quad_fp = quad_2d[fp]
    cat_fp = cat[fp]
    n_fp = int(fp.sum())

    eroded_quad_2d = np.zeros((4, *fp.shape), dtype=bool)
    d_cat_within_quad_fp = np.full(n_fp, 999.0, dtype=np.float32)

    for q in range(4):
        eq = ndi.binary_erosion(quad_2d == q, iterations=DOMAIN_ERODE) & fp
        eroded_quad_2d[q] = eq
        cat_q = cat & eq
        dq = ndi.distance_transform_edt(~cat_q).astype(np.float32)
        q_mask_fp = eq[fp]
        d_cat_within_quad_fp[q_mask_fp] = dq[fp][q_mask_fp]

    eroded_quad_fp = np.stack([eroded_quad_2d[q][fp] for q in range(4)], axis=0)

    # 1. Fit 4 Single-Quadrant Stage-1 Ensembles E_0..E_3 (disk-mmap backed if cache_dir provided)
    quad_s1_arrays: list[np.ndarray] = []
    for k in range(4):
        cache_s1 = (Path(cache_dir) / f"h90_s1_quad{k}_v1.npy") if cache_dir is not None else None
        if cache_s1 is not None and cache_s1.is_file():
            print(f"        [Stage 1] Loaded cached quadrant-{k} ensemble ({k + 1}/4)", flush=True)
            quad_s1_arrays.append(np.load(cache_s1, mmap_mode="r"))
            continue

        print(f"        [Stage 1] Fitting single-quadrant ensemble E_{k} ({k + 1}/4)...", flush=True)
        rng_k = np.random.default_rng(seed + 101 * (k + 1))
        tr_fp = eroded_quad_fp[k]
        pos_idx = np.flatnonzero(tr_fp & cat_fp)
        neg_pool = np.flatnonzero(tr_fp & ~cat_fp & (d_cat_within_quad_fp > 3.0))
        n_neg = min(neg_pool.size, max(pos_idx.size * 6, 60_000))
        neg_idx = rng_k.choice(neg_pool, size=n_neg, replace=False) if neg_pool.size > n_neg else neg_pool

        tr_idx = np.concatenate([pos_idx, neg_idx])
        X_sub = np.asarray(X_fp[tr_idx], dtype=np.float32)
        y_tr = np.concatenate([np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_idx.size, dtype=np.int8)])

        preds_4 = np.empty((4, n_fp), dtype=np.float32)
        m_joint = HistGradientBoostingClassifier(
            max_iter=110,
            max_leaf_nodes=31,
            min_samples_leaf=70,
            learning_rate=0.06,
            l2_regularization=2.0,
            max_bins=128,
            random_state=seed + k,
        )
        m_joint.fit(X_sub, y_tr)
        preds_4[0] = _predict_proba_chunked(m_joint, X_fp)
        del m_joint

        for dom_i, sl in enumerate((DOMAIN_SLICES["potfield"], DOMAIN_SLICES["morpho"], DOMAIN_SLICES["hydrostrain"]), 1):
            m_dom = HistGradientBoostingClassifier(
                max_iter=75,
                max_leaf_nodes=23,
                min_samples_leaf=90,
                learning_rate=0.06,
                l2_regularization=2.5,
                max_bins=128,
                random_state=seed + 20 + 4 * k + dom_i,
            )
            m_dom.fit(X_sub[:, sl], y_tr)
            preds_4[dom_i] = _predict_proba_chunked(m_dom, X_fp[:, sl])
            del m_dom
        del X_sub
        if cache_s1 is not None:
            np.save(cache_s1, preds_4)
            del preds_4
            gc.collect()
            quad_s1_arrays.append(np.load(cache_s1, mmap_mode="r"))
        else:
            quad_s1_arrays.append(preds_4)
        gc.collect()

    # 2. Nested Stage-2 Spatial-Worm Models M2^{(-q)} (cached if cache_dir provided)
    s2_cache_path = (Path(cache_dir) / "h90_s2_cache_v1.npz") if cache_dir is not None else None
    if s2_cache_path is not None and s2_cache_path.is_file():
        print("        [Stage 2] Loaded cached Stage-2 OOF & production surfaces", flush=True)
        z2 = np.load(s2_cache_path)
        exp2_oof_fp = z2["exp2_oof_fp"]
        prod_exp2_fp = z2["prod_exp2_fp"]
        s2_prod_compact = z2["s2_prod_compact"]
        s2_compact_by_fold = {q: z2[f"compact_q{q}"] for q in range(4)}
        del quad_s1_arrays
        gc.collect()
    else:
        s3_keep_cols = [
            STAGE2_FEATURE_NAMES.index("worm_along_800m"),
            STAGE2_FEATURE_NAMES.index("worm_aniso_1800m"),
            STAGE2_FEATURE_NAMES.index("second_best_domain"),
            STAGE2_FEATURE_NAMES.index("ctx_depth_base"),
        ]
        exp2_oof_fp = np.zeros(n_fp, dtype=np.float32)
        s2_compact_by_fold = {}
        stage2_models: list[tuple[HistGradientBoostingClassifier, IsotonicRegression]] = []

        for q in range(4):
            print(f"        [Stage 2] Fitting spatial-worm context model for held-out quadrant {q + 1}/4...", flush=True)
            rng_q = np.random.default_rng(seed + 500 + q)
            other_quads = [r for r in range(4) if r != q]

            s1_tr = [np.zeros(n_fp, dtype=np.float32) for _ in range(4)]
            for r in other_quads:
                rem = [s for s in other_quads if s != r]
                r_mask = quad_fp == r
                for ch in range(4):
                    s1_tr[ch][r_mask] = 0.5 * (
                        np.asarray(quad_s1_arrays[rem[0]][ch, r_mask], dtype=np.float32)
                        + np.asarray(quad_s1_arrays[rem[1]][ch, r_mask], dtype=np.float32)
                    )

            train_allowed_2d = fp & (quad_2d != q)
            S2_tr_all = _build_stage2_features_on_mask(
                s1_tr[0], s1_tr[1], s1_tr[2], s1_tr[3], X_fp, fp, train_allowed_2d
            )
            del s1_tr

            tr_eroded_fp = np.zeros(n_fp, dtype=bool)
            for r in other_quads:
                tr_eroded_fp |= eroded_quad_fp[r]

            pos_s2 = np.flatnonzero(tr_eroded_fp & (d_cat_within_quad_fp <= 1.0))
            neg_pool_s2 = np.flatnonzero(tr_eroded_fp & (d_cat_within_quad_fp > 3.0))
            n_neg_s2 = min(neg_pool_s2.size, max(pos_s2.size * 4, 80_000))
            neg_s2 = rng_q.choice(neg_pool_s2, size=n_neg_s2, replace=False) if neg_pool_s2.size > n_neg_s2 else neg_pool_s2

            r_cal = other_quads[-1]
            fit_mask_pos = quad_fp[pos_s2] != r_cal
            fit_mask_neg = quad_fp[neg_s2] != r_cal

            fit_idx = np.concatenate([pos_s2[fit_mask_pos], neg_s2[fit_mask_neg]])
            y_fit = np.concatenate(
                [np.ones(int(fit_mask_pos.sum()), dtype=np.int8), np.zeros(int(fit_mask_neg.sum()), dtype=np.int8)]
            )
            cal_idx = np.concatenate([pos_s2[~fit_mask_pos], neg_s2[~fit_mask_neg]])
            y_cal = np.concatenate(
                [np.ones(int((~fit_mask_pos).sum()), dtype=np.int8), np.zeros(int((~fit_mask_neg).sum()), dtype=np.int8)]
            )

            m2 = HistGradientBoostingClassifier(
                max_iter=95,
                max_leaf_nodes=23,
                min_samples_leaf=100,
                learning_rate=0.05,
                l2_regularization=3.0,
                max_bins=128,
                random_state=seed + 700 + q,
            )
            m2.fit(S2_tr_all[fit_idx], y_fit)

            raw_cal = _predict_proba_chunked(m2, S2_tr_all[cal_idx])
            iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
            iso.fit(raw_cal, y_cal)
            stage2_models.append((m2, iso))

            s1_test_q = [
                (
                    np.asarray(quad_s1_arrays[other_quads[0]][ch], dtype=np.float32)
                    + np.asarray(quad_s1_arrays[other_quads[1]][ch], dtype=np.float32)
                    + np.asarray(quad_s1_arrays[other_quads[2]][ch], dtype=np.float32)
                )
                / np.float32(3.0)
                for ch in range(4)
            ]
            test_allowed_2d = fp & (quad_2d == q)
            S2_test_q = _build_stage2_features_on_mask(
                s1_test_q[0], s1_test_q[1], s1_test_q[2], s1_test_q[3], X_fp, fp, test_allowed_2d
            )
            del s1_test_q

            q_mask_fp = quad_fp == q
            raw_q = _predict_proba_chunked(m2, S2_test_q[q_mask_fp])
            exp2_oof_fp[q_mask_fp] = iso.predict(raw_q).astype(np.float32)

            compact_q = S2_tr_all[:, s3_keep_cols].copy()
            compact_q[q_mask_fp] = S2_test_q[q_mask_fp][:, s3_keep_cols]
            s2_compact_by_fold[q] = compact_q
            del S2_tr_all, S2_test_q
            gc.collect()

        s1_prod = [
            (
                np.asarray(quad_s1_arrays[0][ch], dtype=np.float32)
                + np.asarray(quad_s1_arrays[1][ch], dtype=np.float32)
                + np.asarray(quad_s1_arrays[2][ch], dtype=np.float32)
                + np.asarray(quad_s1_arrays[3][ch], dtype=np.float32)
            )
            * np.float32(0.25)
            for ch in range(4)
        ]
        del quad_s1_arrays
        gc.collect()

        S2_prod = _build_stage2_features_on_mask(s1_prod[0], s1_prod[1], s1_prod[2], s1_prod[3], X_fp, fp, fp)
        del s1_prod
        prod_exp2_fp = np.mean(
            [iso.predict(_predict_proba_chunked(m2, S2_prod)).astype(np.float32) for m2, iso in stage2_models],
            axis=0,
        ).astype(np.float32)
        s2_prod_compact = S2_prod[:, s3_keep_cols].copy()
        del S2_prod
        if s2_cache_path is not None:
            np.savez(
                s2_cache_path,
                exp2_oof_fp=exp2_oof_fp,
                prod_exp2_fp=prod_exp2_fp,
                s2_prod_compact=s2_prod_compact,
                compact_q0=s2_compact_by_fold[0],
                compact_q1=s2_compact_by_fold[1],
                compact_q2=s2_compact_by_fold[2],
                compact_q3=s2_compact_by_fold[3],
            )
        gc.collect()

    # 3. Stage-3 Simulated-Split Coulomb Tip/Relay Synthesis (Exp 3)
    seg_all, n_seg_all = segments(cat, max_len_px=12)[:2]
    seg_sizes = np.bincount(seg_all.ravel(), minlength=n_seg_all + 1)
    all_seg_ids = np.arange(1, n_seg_all + 1)

    stage3_models: dict[int, tuple[HistGradientBoostingClassifier, IsotonicRegression]] = {}
    for q in range(4):
        print(f"        [Stage 3] Fitting Coulomb tip/relay synthesis model for held-out quadrant {q + 1}/4...", flush=True)
        other_quads = [r for r in range(4) if r != q]
        comp_q = s2_compact_by_fold[q]

        X3_chunks = []
        y3_chunks = []
        quad3_chunks = []

        for sim_draw in (0, 1):
            rng_s3 = np.random.default_rng(seed + 1200 + 17 * q + sim_draw)
            tr_domain_2d = np.zeros(fp.shape, dtype=bool)
            for r in other_quads:
                tr_domain_2d |= eroded_quad_2d[r]

            clipped = np.isin(all_seg_ids, np.unique(seg_all[~tr_domain_2d & cat]))
            elig_segs = all_seg_ids[~clipped]
            perm = rng_s3.permutation(elig_segs)
            target_hide = 0.20 * float((cat & tr_domain_2d).sum())
            k_pick = int(np.searchsorted(np.cumsum(seg_sizes[perm]), target_hide)) + 1
            sim_hid_ids = perm[: min(k_pick, perm.size)]
            sim_hid_2d = np.isin(seg_all, sim_hid_ids) & tr_domain_2d
            sim_vis_2d = (cat & tr_domain_2d) & ~sim_hid_2d

            _, d_clip_fp, tip_fp, relay_fp = compute_fold_visible_coulomb_features(sim_vis_2d, fp)

            elig_tr_fp = tr_domain_2d[fp] & (d_clip_fp > 2.0)
            d_hid_fp = ndi.distance_transform_edt(~sim_hid_2d).astype(np.float32)[fp]
            pos3 = np.flatnonzero(elig_tr_fp & (d_hid_fp <= 1.5))
            neg3_pool = np.flatnonzero(elig_tr_fp & (d_hid_fp > 3.5))
            n_neg3 = min(neg3_pool.size, max(pos3.size * 5, 45_000))
            neg3 = rng_s3.choice(neg3_pool, size=n_neg3, replace=False) if neg3_pool.size > n_neg3 else neg3_pool

            idx3 = np.concatenate([pos3, neg3])
            y3 = np.concatenate([np.ones(pos3.size, dtype=np.int8), np.zeros(neg3.size, dtype=np.int8)])

            s2_v = exp2_oof_fp[idx3]
            t_v = tip_fp[idx3]
            r_v = relay_fp[idx3]
            X3_draw = np.column_stack(
                [
                    s2_v,
                    comp_q[idx3, 0],
                    comp_q[idx3, 1],
                    comp_q[idx3, 2],
                    comp_q[idx3, 3],
                    t_v,
                    r_v,
                    t_v * s2_v,
                    r_v * s2_v,
                ]
            ).astype(np.float32)
            X3_chunks.append(X3_draw)
            y3_chunks.append(y3)
            quad3_chunks.append(quad_fp[idx3])

        X3_all = np.vstack(X3_chunks)
        y3_all = np.concatenate(y3_chunks)
        q3_all = np.concatenate(quad3_chunks)

        r_cal = other_quads[-1]
        fit_m = q3_all != r_cal
        m3 = HistGradientBoostingClassifier(
            max_iter=90,
            max_leaf_nodes=19,
            min_samples_leaf=120,
            learning_rate=0.05,
            l2_regularization=4.0,
            max_bins=128,
            random_state=seed + 1500 + q,
        )
        m3.fit(X3_all[fit_m], y3_all[fit_m])
        iso3 = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        iso3.fit(_predict_proba_chunked(m3, X3_all[~fit_m]), y3_all[~fit_m])
        stage3_models[q] = (m3, iso3)
        del X3_all, y3_all, q3_all
        gc.collect()

    exp2_oof_surface_2d = np.zeros(fp.shape, dtype=np.float32)
    exp2_oof_surface_2d[fp] = np.clip(exp2_oof_fp, 0.0, 1.0)

    exp2_prod_surface_2d = np.zeros(fp.shape, dtype=np.float32)
    exp2_prod_surface_2d[fp] = np.clip(prod_exp2_fp, 0.0, 1.0)

    d_cat_full_2d, _, tip_full_fp, relay_full_fp = compute_fold_visible_coulomb_features(cat, fp)
    X3_prod = np.column_stack(
        [
            prod_exp2_fp,
            s2_prod_compact[:, 0],
            s2_prod_compact[:, 1],
            s2_prod_compact[:, 2],
            s2_prod_compact[:, 3],
            tip_full_fp,
            relay_full_fp,
            tip_full_fp * prod_exp2_fp,
            relay_full_fp * prod_exp2_fp,
        ]
    ).astype(np.float32)
    prod_exp3_fp = np.mean(
        [iso3.predict(_predict_proba_chunked(m3, X3_prod)).astype(np.float32) for m3, iso3 in stage3_models.values()],
        axis=0,
    ).astype(np.float32)
    del X3_prod, s2_prod_compact
    exp3_prod_surface_2d = np.zeros(fp.shape, dtype=np.float32)
    exp3_prod_surface_2d[fp] = np.clip(prod_exp3_fp, 0.0, 1.0)
    exp3_prod_surface_2d[d_cat_full_2d <= 2.0] = 0.0
    gc.collect()

    return {
        "eroded_quad_2d": eroded_quad_2d,
        "exp2_oof_fp": exp2_oof_fp,
        "exp2_oof_surface_2d": exp2_oof_surface_2d,
        "exp2_prod_surface_2d": exp2_prod_surface_2d,
        "exp3_prod_surface_2d": exp3_prod_surface_2d,
        "s2_compact_by_fold": s2_compact_by_fold,
        "stage3_models": stage3_models,
        "d_cat_full_2d": d_cat_full_2d,
    }


def predict_exp3_cell_surface_crop(
    cell: Cell,
    ctx: HoldoutContext,
    sup_out: dict,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute Exp 3 continuous probability crop and d_vis crop for one holdout cell on-the-fly."""
    fp = ctx.grid.footprint
    q = cell.fold
    quad_fp = ctx.quad[fp]
    q_mask_fp = quad_fp == q

    vis = ctx.visible(cell.key)
    d_vis_2d, _, tip_fp, relay_fp = compute_fold_visible_coulomb_features(vis, fp)

    s2_fp_q = sup_out["exp2_oof_fp"][q_mask_fp]
    comp_q = sup_out["s2_compact_by_fold"][q][q_mask_fp]
    t_v = tip_fp[q_mask_fp]
    r_v = relay_fp[q_mask_fp]

    X3_cell_q = np.column_stack(
        [
            s2_fp_q,
            comp_q[:, 0],
            comp_q[:, 1],
            comp_q[:, 2],
            comp_q[:, 3],
            t_v,
            r_v,
            t_v * s2_fp_q,
            r_v * s2_fp_q,
        ]
    ).astype(np.float32)

    m3_q, iso3_q = sup_out["stage3_models"][q]
    p3_q = iso3_q.predict(_predict_proba_chunked(m3_q, X3_cell_q)).astype(np.float32)

    tmp_fp = np.zeros(int(fp.sum()), dtype=np.float32)
    tmp_fp[q_mask_fp] = p3_q
    surf_2d = np.zeros(fp.shape, dtype=np.float32)
    surf_2d[fp] = tmp_fp
    surf_2d[d_vis_2d <= 2.0] = 0.0

    sy, sx = cell.bbox
    return surf_2d[sy, sx].copy(), d_vis_2d[sy, sx].copy()
