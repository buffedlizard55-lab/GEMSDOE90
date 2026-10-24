"""Localized multi-physics, steerable odd-step, shallow hydrothermal demagnetization,
and strictly fold-visible Coulomb fault-tip/relay feature extraction for Lane H90.

Leakage safety contract:
- Static features (36 channels) read ONLY geophysical, topographic, 3DEP 1 m LiDAR,
  GeoDAWN radiometric/upward-continued, and GDR 1391 well/spring temperature &
  geothermometer coordinates/values.
- The ``dist_known_fault_px`` column present in ``gdr_wellspring_in_footprint.csv``
  and ``gdr_volcanic_vents_in_footprint.csv`` is NEVER read (logged as IR90-43).
- Zero prior submission rasters (e.g. R0, H19-5, D2.8) are ever read here.
- Fold-visible structural features (3 channels, used only in Experiment 3) are
  computed strictly from the supplied ``visible_faults`` boolean mask.
"""

from __future__ import annotations

import csv
import gc
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

STATIC_FEATURE_NAMES: tuple[str, ...] = (
    # Domain A: Potential-field basement juxtaposition & steerable odd-step polarity (0..14)
    "b02_rtp_hp8",
    "b03_tmi_hg_log",
    "b06_tc_zero_prox",
    "b09_tmi_vg_signed",
    "b05_grav_slope_log",
    "b11_grav_vg_signed",
    "b13_grav_hp8",
    "b18_grav_hg_log",
    "b15_depth_base_log",
    "b15_basement_grad",
    "rtp_odd_step_ratio",
    "grav_odd_step_ratio",
    "gallardo_crossgrad_collin",
    "analytic_sig_scale_ratio",
    "cover_potfield_coupling",
    # Domain B: 3DEP 1 m LiDAR & 100 m topographic odd-scarp morphometry (15..25)
    "b12_det_elev_hp6",
    "b19_det_elev_slope",
    "elev_odd_step_ratio",
    "elev_lap_dipole",
    "lid_valid",
    "lid_step_max",
    "lid_scarp_dipole",
    "lid_face_asymmetry",
    "lid_coh100",
    "lid_ex_ratio",
    "lid_tect_vs_fluv",
    # Domain C: Hydrothermal demagnetization trough, K/Th alteration, MT clay-cap & strain (26..35)
    "demag_up150_deficit",
    "rad_k_th_alteration",
    "rad_alteration_grad",
    "b17_cond_surf",
    "b17_cond_grad",
    "gdr_geotherm_halo_near",
    "gdr_geotherm_halo_meso",
    "b04_strain_2ndinv",
    "transtension_index",
    "seismicity_aniso",
)

DOMAIN_SLICES: dict[str, slice] = {
    "potfield": slice(0, 15),
    "morpho": slice(15, 26),
    "hydrostrain": slice(26, 36),
}

VISIBLE_FEATURE_NAMES: tuple[str, ...] = (
    "vis_coulomb_tip_cone",
    "vis_relay_bridge",
)

FORBIDDEN_CSV_COLUMNS = frozenset({"dist_known_fault_px"})


def clean_band(arr: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Replace non-finite / float32 sentinel values with in-footprint median for filtering."""
    raw = np.asarray(arr, dtype=np.float32)
    valid = footprint & np.isfinite(raw) & (raw > -1e30) & (raw < 1e30)
    med = float(np.median(raw[valid])) if valid.any() else 0.0
    cleaned = np.where(valid, raw, med).astype(np.float32)
    return cleaned, valid


def robust_z(arr: np.ndarray, valid: np.ndarray, clip: float = 8.0) -> np.ndarray:
    """Footprint-valid median/IQR z-score clipped to [-clip, clip]."""
    out = np.zeros(arr.shape, dtype=np.float32)
    if not valid.any():
        return out
    vals = arr[valid]
    med = float(np.median(vals))
    q25, q75 = np.percentile(vals, [25.0, 75.0])
    scale = max(float(q75 - q25) / 1.349, 1e-6)
    z = np.clip((arr - med) / scale, -clip, clip)
    out[valid] = z[valid].astype(np.float32)
    return out


def grad_mag(arr: np.ndarray, sigma: float = 1.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Gaussian-smoothed spatial gradient (gy, gx, hypot)."""
    sm = ndi.gaussian_filter(arr.astype(np.float32), sigma=sigma, mode="nearest") if sigma > 0 else arr.astype(np.float32)
    gy = ndi.sobel(sm, axis=0, mode="nearest") * np.float32(0.125)
    gx = ndi.sobel(sm, axis=1, mode="nearest") * np.float32(0.125)
    return gy, gx, np.hypot(gy, gx).astype(np.float32)


def steerable_odd_even_step_ratio(
    arr: np.ndarray,
    footprint: np.ndarray,
    radius_px: int = 3,
    smooth_sigma: float = 1.0,
) -> np.ndarray:
    """8-azimuth steerable odd-step vs. even-bump/channel discriminator.

    A dipping fault step produces a large anti-symmetric cross-strike difference
    |f(x + r*n) - f(x - r*n)| and a near-zero symmetric second difference
    |f(x + r*n) + f(x - r*n) - 2*f(x)| at the inflection trace, whereas a narrow
    dike, volcanic ridge, or incised gully peaks in the even term.
    """
    sm = ndi.gaussian_filter(arr.astype(np.float32), sigma=smooth_sigma, mode="nearest")
    vals = sm[footprint]
    iqr = float(np.percentile(vals, 75.0) - np.percentile(vals, 25.0)) if vals.size else 1.0
    eps = np.float32(max(iqr * 0.15, 1e-5))

    H, W = sm.shape
    r = int(radius_px)
    padded = np.pad(sm, r, mode="edge")
    center = sm
    best = np.zeros((H, W), dtype=np.float32)

    # 8 cross-strike normal directions covering [0, pi)
    for k in range(8):
        theta = k * (np.pi / 8.0)
        dy = int(round(r * np.sin(theta)))
        dx = int(round(r * np.cos(theta)))
        if dy == 0 and dx == 0:
            continue
        f_plus = padded[r + dy : r + dy + H, r + dx : r + dx + W]
        f_minus = padded[r - dy : r - dy + H, r - dx : r - dx + W]
        odd = np.abs(f_plus - f_minus)
        even = np.abs(f_plus + f_minus - 2.0 * center)
        score = odd / (even + eps)
        np.maximum(best, score, out=best)

    best[~footprint] = 0.0
    return best


def steerable_line_anisotropy(
    field_2d: np.ndarray,
    valid_2d: np.ndarray,
    half_len_px: int,
    n_taps_half: int = 3,
    n_angles: int = 8,
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized 8-azimuth strided 1D line integral along strike & orthogonal anisotropy."""
    arr = np.where(valid_2d, field_2d, 0.0).astype(np.float32)
    H, W = arr.shape
    pad = int(half_len_px)
    padded = np.pad(arr, pad, mode="edge")
    taps = np.linspace(-half_len_px, half_len_px, 2 * n_taps_half + 1)
    inv_w = np.float32(1.0 / len(taps))

    half_n = n_angles // 2
    along_max = np.full((H, W), -1e30, dtype=np.float32)
    aniso = np.zeros((H, W), dtype=np.float32)

    for k_idx in range(half_n):
        t1 = k_idx * np.pi / n_angles
        t2 = (k_idx + half_n) * np.pi / n_angles
        r_a = np.zeros((H, W), dtype=np.float32)
        r_b = np.zeros((H, W), dtype=np.float32)
        for s in taps:
            dy1, dx1 = int(round(s * np.sin(t1))), int(round(s * np.cos(t1)))
            r_a += padded[pad + dy1 : pad + dy1 + H, pad + dx1 : pad + dx1 + W]
            dy2, dx2 = int(round(s * np.sin(t2))), int(round(s * np.cos(t2)))
            r_b += padded[pad + dy2 : pad + dy2 + H, pad + dx2 : pad + dx2 + W]
        r_a *= inv_w
        r_b *= inv_w
        m_a = r_a > along_max
        if m_a.any():
            along_max[m_a] = r_a[m_a]
            aniso[m_a] = r_a[m_a] - r_b[m_a]
        m_b = r_b > along_max
        if m_b.any():
            along_max[m_b] = r_b[m_b]
            aniso[m_b] = r_b[m_b] - r_a[m_b]
    along_max[~valid_2d] = 0.0
    aniso[~valid_2d] = 0.0
    return along_max, aniso


def _parse_float(val: str | None) -> float:
    if val is None or val == "":
        return float("nan")
    try:
        v = float(val)
        return v if np.isfinite(v) else float("nan")
    except ValueError:
        return float("nan")


def rasterize_gdr_hydrothermal_halos(
    wellspring_csv: Path,
    vents_csv: Path,
    footprint: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Build localized (600 m) and district-scale (2.0 km) hydrothermal enthalpy grids.

    Strictly ignores ``dist_known_fault_px`` so zero catalogue proximity leaks in.
    """
    H, W = footprint.shape
    imp_grid = np.zeros((H, W), dtype=np.float32)
    vent_grid = np.zeros((H, W), dtype=np.float32)

    if wellspring_csv.is_file():
        with wellspring_csv.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            allowed_cols = set(reader.fieldnames or ()) - FORBIDDEN_CSV_COLUMNS
            assert "dist_known_fault_px" not in allowed_cols
            for row in reader:
                r = int(round(_parse_float(row.get("row")))) if np.isfinite(_parse_float(row.get("row"))) else -1
                c = int(round(_parse_float(row.get("col")))) if np.isfinite(_parse_float(row.get("col"))) else -1
                if not (0 <= r < H and 0 <= c < W) or not footprint[r, c]:
                    continue
                temp_c = _parse_float(row.get("temp_c"))
                qtz_c = _parse_float(row.get("geothermquartz_c"))
                chalc_c = _parse_float(row.get("geothermchalc_c"))
                cat_c = _parse_float(row.get("geothermcat_c"))
                finite_geo = [v for v in (qtz_c, chalc_c, cat_c) if np.isfinite(v)]
                geotherm_max = max(finite_geo) if finite_geo else float("nan")
                t_excess = max(temp_c - 20.0, 0.0) if np.isfinite(temp_c) else 0.0
                g_excess = max(geotherm_max - 70.0, 0.0) if np.isfinite(geotherm_max) else 0.0
                cls = (row.get("thermalclass") or "").strip().lower()
                cls_bonus = 15.0 if ("hot" in cls or "warm" in cls or "thermal" in cls) else 0.0
                score = float(np.log1p(t_excess + 0.5 * g_excess + cls_bonus))
                if score > imp_grid[r, c]:
                    imp_grid[r, c] = score

    if vents_csv.is_file():
        with vents_csv.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                r = int(round(_parse_float(row.get("row")))) if np.isfinite(_parse_float(row.get("row"))) else -1
                c = int(round(_parse_float(row.get("col")))) if np.isfinite(_parse_float(row.get("col"))) else -1
                if 0 <= r < H and 0 <= c < W and footprint[r, c]:
                    vent_grid[r, c] = 1.0

    near = ndi.gaussian_filter(imp_grid, sigma=6.0, mode="constant", cval=0.0)
    meso = ndi.gaussian_filter(imp_grid, sigma=20.0, mode="constant", cval=0.0) + 0.5 * ndi.gaussian_filter(
        vent_grid, sigma=25.0, mode="constant", cval=0.0
    )
    return robust_z(near, footprint), robust_z(meso, footprint)


def extract_static_features_fp(
    data_dir: Path,
    footprint: np.ndarray,
) -> np.ndarray:
    """Extract all 36 localized static features onto ``X_fp`` of shape ``(N_fp, 36)`` float32.

    Streams one band/group at a time so peak memory stays well under 1.8 GiB.
    """
    fp = np.asarray(footprint, dtype=bool)
    n_fp = int(fp.sum())
    X_fp = np.empty((n_fp, len(STATIC_FEATURE_NAMES)), dtype=np.float32)

    tf_path = data_dir / "training_features.tif"
    lid_path = data_dir / "external" / "lidar_scarp_features_u8.tif"
    rad_path = data_dir / "external" / "geodawn_rad_u8.tif"
    ext_path = data_dir / "external" / "geodawn_extensions_u8.tif"
    ws_csv = data_dir / "external" / "gdr_wellspring_in_footprint.csv"
    vent_csv = data_dir / "external" / "gdr_volcanic_vents_in_footprint.csv"

    with rasterio.open(tf_path) as tf:
        # --- Potential-field bands ---
        rtp, v_rtp = clean_band(tf.read(2), fp)
        tmi_hg, v_thg = clean_band(tf.read(3), fp)
        tc, v_tc = clean_band(tf.read(6), fp)
        tmi_vg, v_tvg = clean_band(tf.read(9), fp)
        grav_slope, v_gs = clean_band(tf.read(5), fp)
        grav_vg, v_gvg = clean_band(tf.read(11), fp)
        grav, v_grav = clean_band(tf.read(13), fp)
        depth_base, v_db = clean_band(tf.read(15), fp)
        grav_hg, v_ghg = clean_band(tf.read(18), fp)

        rtp_hp8 = rtp - ndi.gaussian_filter(rtp, sigma=8.0, mode="nearest")
        X_fp[:, 0] = robust_z(rtp_hp8, v_rtp)[fp]
        del rtp_hp8

        thg_log = np.log1p(np.abs(tmi_hg))
        z_thg = robust_z(thg_log, v_thg)
        X_fp[:, 1] = z_thg[fp]

        tc_zero = np.exp(-np.abs(tc) / np.float32(0.35)).astype(np.float32)
        X_fp[:, 2] = robust_z(tc_zero, v_tc)[fp]
        del tc, tc_zero

        z_tvg = robust_z(tmi_vg, v_tvg)
        X_fp[:, 3] = z_tvg[fp]

        X_fp[:, 4] = robust_z(np.log1p(np.abs(grav_slope)), v_gs)[fp]
        del grav_slope

        X_fp[:, 5] = robust_z(grav_vg, v_gvg)[fp]
        del grav_vg

        grav_hp8 = grav - ndi.gaussian_filter(grav, sigma=8.0, mode="nearest")
        X_fp[:, 6] = robust_z(grav_hp8, v_grav)[fp]
        del grav_hp8

        ghg_log = np.log1p(np.abs(grav_hg))
        z_ghg = robust_z(ghg_log, v_ghg)
        X_fp[:, 7] = z_ghg[fp]
        del ghg_log, grav_hg

        db_pos = np.maximum(depth_base, 0.0)
        z_db = robust_z(np.log1p(db_pos), v_db)
        X_fp[:, 8] = z_db[fp]
        _, _, db_grad = grad_mag(db_pos, sigma=1.5)
        X_fp[:, 9] = robust_z(np.log1p(db_grad), v_db)[fp]
        del depth_base, db_pos, db_grad

        rtp_odd = steerable_odd_even_step_ratio(rtp, fp, radius_px=3, smooth_sigma=1.0)
        X_fp[:, 10] = robust_z(rtp_odd, v_rtp)[fp]
        del rtp_odd

        grav_odd = steerable_odd_even_step_ratio(grav, fp, radius_px=4, smooth_sigma=1.2)
        X_fp[:, 11] = robust_z(grav_odd, v_grav)[fp]
        del grav_odd

        # Gallardo-Meju gravity-magnetic gradient collinearity
        gy_m, gx_m, gm_mag = grad_mag(rtp, sigma=1.5)
        gy_g, gx_g, gg_mag = grad_mag(grav, sigma=1.5)
        cos_gm = np.abs(gy_m * gy_g + gx_m * gx_g) / (gm_mag * gg_mag + np.float32(1e-5))
        collin = cos_gm * np.sqrt(np.maximum(z_thg + 2.0, 0.0) * np.maximum(z_ghg + 2.0, 0.0))
        X_fp[:, 12] = robust_z(collin, v_rtp & v_grav)[fp]
        del gy_m, gx_m, gm_mag, gy_g, gx_g, gg_mag, cos_gm, collin, grav

        # Analytic signal multiscale width ratio
        asig = np.hypot(tmi_hg, tmi_vg).astype(np.float32)
        as_ratio = ndi.gaussian_filter(asig, sigma=3.0, mode="nearest") / (
            ndi.gaussian_filter(asig, sigma=1.0, mode="nearest") + np.float32(1e-3)
        )
        X_fp[:, 13] = robust_z(np.clip(as_ratio, 0.0, 4.0), v_thg & v_tvg)[fp]
        del tmi_hg, tmi_vg, asig, as_ratio

        # Cover x potential-field coupling
        coupling = np.maximum(z_db, -0.5) * (0.5 * z_thg + 0.5 * z_ghg)
        X_fp[:, 14] = robust_z(coupling, fp)[fp]
        del z_db, z_thg, z_ghg, coupling
        gc.collect()

        # Keep local RTP z-score for upward-continuation demagnetization comparison
        rtp_local_z = robust_z(rtp - ndi.gaussian_filter(rtp, sigma=12.0, mode="nearest"), v_rtp)
        del rtp

        # --- Topographic morphometry (bands 12 & 19) ---
        det_elev, v_de = clean_band(tf.read(12), fp)
        det_slope, v_ds = clean_band(tf.read(19), fp)

        de_hp6 = det_elev - ndi.gaussian_filter(det_elev, sigma=6.0, mode="nearest")
        X_fp[:, 15] = robust_z(de_hp6, v_de)[fp]
        del de_hp6

        X_fp[:, 16] = robust_z(np.log1p(np.maximum(det_slope, 0.0)), v_ds)[fp]
        del det_slope

        elev_odd = steerable_odd_even_step_ratio(det_elev, fp, radius_px=3, smooth_sigma=0.8)
        X_fp[:, 17] = robust_z(elev_odd, v_de)[fp]
        del elev_odd

        lap = ndi.laplace(ndi.gaussian_filter(det_elev, sigma=1.0, mode="nearest"), mode="nearest")
        crest = ndi.gaussian_filter(np.maximum(-lap, 0.0), sigma=1.5, mode="nearest")
        toe = ndi.gaussian_filter(np.maximum(lap, 0.0), sigma=1.5, mode="nearest")
        X_fp[:, 18] = robust_z(np.sqrt(crest * toe), v_de)[fp]
        del det_elev, lap, crest, toe
        gc.collect()

        # --- Strain, seismicity, and shallow conductivity ---
        strain2, v_s2 = clean_band(tf.read(4), fp)
        shear, v_sh = clean_band(tf.read(7), fp)
        dilat, v_di = clean_band(tf.read(8), fp)
        deq, v_deq = clean_band(tf.read(10), fp)
        ieq, v_ieq = clean_band(tf.read(16), fp)
        cond, v_co = clean_band(tf.read(17), fp)

    # --- 3DEP 1 m LiDAR scarp stack (preserve NaN outside valid LiDAR for native tree handling) ---
    if lid_path.is_file():
        with rasterio.open(lid_path) as lid:
            ex_max = lid.read(1).astype(np.float32)
            ex_mean = lid.read(2).astype(np.float32)
            step_max = lid.read(3).astype(np.float32)
            lapneg = lid.read(4).astype(np.float32)
            lappos = lid.read(5).astype(np.float32)
            downface = lid.read(6).astype(np.float32)
            upface = lid.read(7).astype(np.float32)
            cross_max = lid.read(8).astype(np.float32)
            relief = lid.read(9).astype(np.float32)
            coh100 = lid.read(10).astype(np.float32)
            lid_val = (lid.read(12) > 0) & fp

        X_fp[:, 19] = lid_val[fp].astype(np.float32)
        nan_mask = ~lid_val
        for idx, arr_u8 in (
            (20, step_max),
            (21, np.sqrt(lapneg * lappos)),
            (22, np.abs(downface - upface) / (downface + upface + np.float32(4.0))),
            (23, coh100),
            (24, ex_mean / (ex_max + np.float32(4.0))),
            (25, (step_max * coh100) / (cross_max + relief + np.float32(8.0))),
        ):
            tmp = robust_z(arr_u8, lid_val)
            tmp[nan_mask] = np.nan
            X_fp[:, idx] = tmp[fp]
        del ex_max, ex_mean, step_max, lapneg, lappos, downface, upface, cross_max, relief, coh100, lid_val
    else:
        X_fp[:, 19] = 0.0
        X_fp[:, 20:26] = np.nan

    # --- GeoDAWN upward-continuation shallow demagnetization & K/Th radiometric alteration ---
    if ext_path.is_file() and rad_path.is_file():
        with rasterio.open(ext_path) as ext_ds:
            thk = ext_ds.read(1).astype(np.float32)
            tmi_up150 = ext_ds.read(4).astype(np.float32)
        with rasterio.open(rad_path) as rad_ds:
            rad_k = rad_ds.read(1).astype(np.float32)
            rad_tc = rad_ds.read(4).astype(np.float32)

        v_up = fp & (tmi_up150 > 0)
        up_local_z = robust_z(tmi_up150 - ndi.gaussian_filter(tmi_up150, sigma=12.0, mode="nearest"), v_up)
        # Shallow magnetite destruction deficit: deep TMI_up150 higher than local RTP, reinforced by -tmi_vg
        demag = (up_local_z - rtp_local_z) * (np.float32(0.5) + np.float32(0.5) * np.maximum(-z_tvg, 0.0))
        X_fp[:, 26] = robust_z(demag, v_up & v_rtp)[fp]
        del tmi_up150, up_local_z, demag

        v_rad = fp & (rad_tc > 0)
        k_th = robust_z(rad_k, v_rad) - robust_z(thk, v_rad)
        k_th_arr = robust_z(k_th, v_rad)
        _, _, kth_grad = grad_mag(np.where(v_rad, k_th_arr, 0.0), sigma=1.5)
        kth_grad_z = robust_z(kth_grad, v_rad)
        k_th_arr[~v_rad] = np.nan
        kth_grad_z[~v_rad] = np.nan
        X_fp[:, 27] = k_th_arr[fp]
        X_fp[:, 28] = kth_grad_z[fp]
        del thk, rad_k, rad_tc, k_th, k_th_arr, kth_grad, kth_grad_z
    else:
        X_fp[:, 26] = 0.0
        X_fp[:, 27:29] = np.nan
    del rtp_local_z, z_tvg
    gc.collect()

    # --- MT conductivity, GDR 1391 geothermometers, geodetic transtension, seismicity ---
    X_fp[:, 29] = robust_z(np.log1p(np.maximum(cond, 0.0)), v_co)[fp]
    _, _, cond_grad = grad_mag(np.log1p(np.maximum(cond, 0.0)), sigma=1.5)
    X_fp[:, 30] = robust_z(cond_grad, v_co)[fp]
    del cond, cond_grad

    halo_near, halo_meso = rasterize_gdr_hydrothermal_halos(ws_csv, vent_csv, fp)
    X_fp[:, 31] = halo_near[fp]
    X_fp[:, 32] = halo_meso[fp]
    del halo_near, halo_meso

    X_fp[:, 33] = robust_z(strain2, v_s2)[fp]
    z_sh = robust_z(shear, v_sh)
    z_di = robust_z(dilat, v_di)
    transtens = np.maximum(z_sh + 0.5, 0.0) * np.maximum(z_di, 0.0)
    X_fp[:, 34] = robust_z(transtens, v_sh & v_di)[fp]
    del strain2, shear, dilat, z_sh, z_di, transtens

    _, _, ieq_grad = grad_mag(ieq, sigma=2.0)
    seis = robust_z(np.log1p(ieq_grad), v_ieq) + 0.5 * robust_z(-deq, v_deq)
    X_fp[:, 35] = robust_z(seis, v_ieq & v_deq)[fp]
    del deq, ieq, ieq_grad, seis
    gc.collect()

    return X_fp


def compute_fold_visible_coulomb_features(
    visible_faults: np.ndarray,
    footprint: np.ndarray,
    max_tip_radius_px: int = 24,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute strictly fold-visible distance + Coulomb forward-tip cone + relay bridge features.

    Returns ``(d_vis_2d, d_vis_clipped_fp, tip_cone_fp, relay_bridge_fp)``.
    Zero withheld fault pixels can ever enter this calculation when called with
    ``ctx.visible(key)``.
    """
    vis = np.asarray(visible_faults, dtype=bool) & footprint
    H, W = footprint.shape
    if not vis.any():
        d_vis = np.full((H, W), 35.0, dtype=np.float32)
        n_fp = int(footprint.sum())
        z = np.zeros(n_fp, dtype=np.float32)
        return d_vis, np.full(n_fp, 35.0, dtype=np.float32), z, z.copy()

    d_vis = ndi.distance_transform_edt(~vis).astype(np.float32)
    d_clipped = np.clip(d_vis, 0.0, 35.0).astype(np.float32)

    # Connected component host lengths (longer host trace => higher tip stress intensity K ~ sqrt(L))
    comp_lbl, n_comp = ndi.label(vis, structure=np.ones((3, 3), dtype=np.int8))
    comp_sizes = np.bincount(comp_lbl.ravel(), minlength=n_comp + 1).astype(np.float32)

    # True morphological endpoints: either degree-1 (1 neighbour), or degree-2 L-cap where the
    # two 8-neighbours are mutually adjacent (excludes straight/diagonal interior pixels!).
    nbr_count = ndi.convolve(vis.astype(np.int16), np.ones((3, 3), dtype=np.int16), mode="constant", cval=0) - 1
    deg1 = vis & (nbr_count == 1)
    deg2_y, deg2_x = np.nonzero(vis & (nbr_count == 2))
    vis_pad = np.pad(vis, 1, mode="constant", constant_values=False)
    is_lcap = np.zeros(deg2_y.size, dtype=bool)
    for k_i, (ry, rx) in enumerate(zip(deg2_y.tolist(), deg2_x.tolist())):
        patch = vis_pad[ry : ry + 3, rx : rx + 3].copy()
        patch[1, 1] = False
        ny, nx = np.nonzero(patch)
        if ny.size == 2 and max(abs(int(ny[0] - ny[1])), abs(int(nx[0] - nx[1]))) == 1:
            is_lcap[k_i] = True
    tip_mask = deg1.copy()
    tip_mask[deg2_y[is_lcap], deg2_x[is_lcap]] = True
    cand_y, cand_x = np.nonzero(tip_mask)

    tips_y = []
    tips_x = []
    tips_ty = []
    tips_tx = []
    tips_w = []

    vis_u8 = vis.astype(np.uint8)
    for y0, x0 in zip(cand_y.tolist(), cand_x.tolist()):
        # Gather visible trace pixels within a 6-px backyard to estimate outward tangent
        y_lo, y_hi = max(0, y0 - 6), min(H, y0 + 7)
        x_lo, x_hi = max(0, x0 - 6), min(W, x0 + 7)
        cid = comp_lbl[y0, x0]
        sub_y, sub_x = np.nonzero(comp_lbl[y_lo:y_hi, x_lo:x_hi] == cid)
        if sub_y.size < 3:
            continue
        dy_back = (sub_y + y_lo - y0).astype(np.float32)
        dx_back = (sub_x + x_lo - x0).astype(np.float32)
        dist_back = np.hypot(dy_back, dx_back)
        mask_b = (dist_back > 0.5) & (dist_back <= 6.5)
        if not mask_b.any():
            continue
        # Mean vector from tip INTO the trace; outward tip vector is its negative
        vy_in = float(np.mean(dy_back[mask_b]))
        vx_in = float(np.mean(dx_back[mask_b]))
        norm = float(np.hypot(vy_in, vx_in))
        if norm < 1.2:
            # Interior bend rather than a true one-sided endpoint
            continue
        # Verify forward 3-px sector has no visible pixel of same component
        ty_out = -vy_in / norm
        tx_out = -vx_in / norm
        yf = int(round(y0 + 2.0 * ty_out))
        xf = int(round(x0 + 2.0 * tx_out))
        if 0 <= yf < H and 0 <= xf < W and vis_u8[yf, xf]:
            continue
        host_len = float(comp_sizes[cid])
        if host_len < 25.0:
            # Restrict tip lobes to major trunks (>= 2.5 km) to avoid synthetic chopped stubs
            continue
        tips_y.append(y0)
        tips_x.append(x0)
        tips_ty.append(ty_out)
        tips_tx.append(tx_out)
        tips_w.append(min(np.sqrt(host_len / 25.0), 2.0))

    tip_cone = np.zeros((H, W), dtype=np.float32)
    relay_bridge = np.zeros((H, W), dtype=np.float32)

    R = int(max_tip_radius_px)
    yy_rel, xx_rel = np.mgrid[-R : R + 1, -R : R + 1].astype(np.float32)
    rr_rel = np.hypot(yy_rel, xx_rel)
    # Exclude r <= 4.5 px so the feature captures meso-scale Mode-II wing-crack splays
    # rather than stitching synthetic 12-px segment cuts in hide-and-recover mode="all" (IR90-46)
    valid_ring = (rr_rel > 4.5) & (rr_rel <= float(R))

    n_tips = len(tips_y)
    for i in range(n_tips):
        y0, x0 = tips_y[i], tips_x[i]
        ty, tx, w_i = tips_ty[i], tips_tx[i], tips_w[i]

        y_lo, y_hi = max(0, y0 - R), min(H, y0 + R + 1)
        x_lo, x_hi = max(0, x0 - R), min(W, x0 + R + 1)
        sy = slice(y_lo - (y0 - R), y_hi - (y0 - R))
        sx = slice(x_lo - (x0 - R), x_hi - (x0 - R))

        dy = yy_rel[sy, sx]
        dx = xx_rel[sy, sx]
        rr = rr_rel[sy, sx]
        ring = valid_ring[sy, sx]
        cos_t = np.where(ring, (dy * ty + dx * tx) / np.maximum(rr, 1e-4), 0.0)
        sin_t_sq = np.maximum(1.0 - cos_t * cos_t, 0.0)
        # Mode-II wing-crack oblique tensile lobe: peaks at ~25-45 deg off-axis, tapered over [4.5, 24] px
        taper_in = np.clip((rr - 4.5) / 3.0, 0.0, 1.0)
        cone = np.where(
            (cos_t > 0.45) & ring,
            (cos_t ** 2) * (0.25 + 3.0 * sin_t_sq) * taper_in * np.exp(-rr / 11.0) * w_i,
            0.0,
        ).astype(np.float32)
        np.maximum(tip_cone[y_lo:y_hi, x_lo:x_hi], cone, out=tip_cone[y_lo:y_hi, x_lo:x_hi])

    # En-echelon relay bridges between opposing tips within [4, 28] px
    if n_tips >= 2:
        ty_arr = np.asarray(tips_y, dtype=np.float32)
        tx_arr = np.asarray(tips_x, dtype=np.float32)
        vy_arr = np.asarray(tips_ty, dtype=np.float32)
        vx_arr = np.asarray(tips_tx, dtype=np.float32)
        w_arr = np.asarray(tips_w, dtype=np.float32)

        for i in range(n_tips):
            dy_ij = ty_arr[i + 1 :] - ty_arr[i]
            dx_ij = tx_arr[i + 1 :] - tx_arr[i]
            dist_ij = np.hypot(dy_ij, dx_ij)
            cand_j = np.flatnonzero((dist_ij >= 4.0) & (dist_ij <= 28.0))
            for idx_rel in cand_j.tolist():
                j = i + 1 + idx_rel
                dij = float(dist_ij[idx_rel])
                uy = float(dy_ij[idx_rel]) / dij
                ux = float(dx_ij[idx_rel]) / dij
                # Tip i points roughly toward j AND tip j points roughly toward i
                f_i = vy_arr[i] * uy + vx_arr[i] * ux
                f_j = -(vy_arr[j] * uy + vx_arr[j] * ux)
                if f_i < 0.45 or f_j < 0.45:
                    continue
                strength = float(f_i * f_j * np.sqrt(w_arr[i] * w_arr[j]) * np.exp(-dij / 18.0))
                pad_b = 5
                by0 = max(0, int(min(tips_y[i], tips_y[j])) - pad_b)
                by1 = min(H, int(max(tips_y[i], tips_y[j])) + pad_b + 1)
                bx0 = max(0, int(min(tips_x[i], tips_x[j])) - pad_b)
                bx1 = min(W, int(max(tips_x[i], tips_x[j])) + pad_b + 1)
                gy, gx = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
                ri = np.hypot(gy - tips_y[i], gx - tips_x[i])
                rj = np.hypot(gy - tips_y[j], gx - tips_x[j])
                excess = np.maximum(ri + rj - dij, 0.0)
                bridge = (strength * np.exp(-excess / 2.5)).astype(np.float32)
                np.maximum(relay_bridge[by0:by1, bx0:bx1], bridge, out=relay_bridge[by0:by1, bx0:bx1])

    tip_cone[~footprint] = 0.0
    relay_bridge[~footprint] = 0.0
    return d_vis, d_clipped[footprint], tip_cone[footprint], relay_bridge[footprint]
