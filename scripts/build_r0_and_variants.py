"""
Build synthetic demonstration of R0 and 3 CONCENTRATION variants.
Because real parent R0 (h33-h33-2-b2, 37654 dots) and catalogue are UNVERIFIED (not in repo),
this script creates a SYNTHETIC stand-in that satisfies all structural gates so the
validator, ledger, and release pipeline can be CI-tested.
Real competition run must replace SYNTHETIC blocks with pinned sources — see IRREGULARITIES.md.

AXIS for this session: CONCENTRATION
We move 10%, 15%, 20% of dots from lowest-prior km-scale blocks to highest-prior blocks.
Block size: 1 km (10 px at 100 m). Report block-density CV before/after.

Synthesis design:
- Footprint 2000x2585 (5.17M px) EPSG:32611, transform 100m, origin 360000,4450000.
- Footprint mask: inner rectangle with rounded corners + 2 holes to mimic null outside.
- Catalogue synthetic: 200 random polyline faults (buffered 1px), ~3% of footprint.
- Prior field synthetic: Gaussian smoothed random + distance-to-catalogue term to mimic interaction prior.
- R0 dots: 37654 unit-mass dots sampled weighted by prior-derived field, excluding catalogue 2px buffer.
"""
import numpy as np
import rasterio
from rasterio.transform import from_origin
import hashlib
import os
import json
from pathlib import Path
from datetime import date

# Config — matches registry/data_manifest.json synthetic entry
COLS, ROWS = 2000, 2585
CRS = "EPSG:32611"
TRANSFORM = from_origin(360000, 4450000, 100, 100)  # y origin top, pixel 100m
WEST, NORTH = 360000, 4450000
N_DOTS_R0 = 37654
RNG_SEED = 42
BLOCK_PX = 10  # 1 km = 10 px at 100m
CATALOGUE_BUFFER_PX = 2  # R0 excludes 2px
TODAY = date(2026, 10, 23).isoformat().replace("-","")  # for naming
TODAY_DASH = "2026-10-23"
PARENT_ID = "h33-h33-2-b2"
OUTDIR = Path("releases")
SYNTH_DIR = Path("synthetic_inputs")
SYNTH_DIR.mkdir(exist_ok=True)
OUTDIR.mkdir(exist_ok=True)

rng = np.random.default_rng(RNG_SEED)

def make_footprint():
    """Synthetic footprint: mostly inside, with border and two lakes as outside."""
    mask = np.ones((ROWS, COLS), dtype=bool)
    # Border 20px outside as null
    mask[:20, :] = False
    mask[-20:, :] = False
    mask[:, :20] = False
    mask[:, -20:] = False
    # Two circular holes (lakes) as outside
    rr, cc = np.ogrid[:ROWS, :COLS]
    # Lake 1 center ~ (600,800) radius 80px
    lake1 = (rr-600)**2 + (cc-800)**2 < 80**2
    lake2 = (rr-1800)**2 + (cc-1400)**2 < 120**2
    mask[lake1] = False
    mask[lake2] = False
    # Irregular edge: cut off NW corner triangle
    # Keep count ~5.17M - borders - lakes ≈ 5M, close enough
    print(f"Footprint inside: {mask.sum()} / {ROWS*COLS} ({100*mask.mean():.1f}%)")
    return mask

def make_catalogue(footprint):
    """Synthetic catalogue: random walk faults."""
    cat = np.zeros((ROWS, COLS), dtype=bool)
    n_faults = 200
    for i in range(n_faults):
        # random start inside footprint
        for _ in range(100):
            r0 = rng.integers(50, ROWS-50)
            c0 = rng.integers(50, COLS-50)
            if footprint[r0,c0]:
                break
        r, c = r0, c0
        length = rng.integers(40, 180)  # 4-18 km
        angle = rng.uniform(0, 2*np.pi)
        for step in range(length):
            if 0<=r<ROWS and 0<=c<COLS:
                cat[r,c]=True
                # buffer 1px to make fault visible (2px wide)
                for dr in [-1,0,1]:
                    for dc in [-1,0,1]:
                        rr2, cc2 = r+dr, c+dc
                        if 0<=rr2<ROWS and 0<=cc2<COLS:
                            if rng.random()<0.5:
                                cat[rr2,cc2]=True
            # walk with jitter
            angle += rng.normal(0, 0.25)
            r = int(r + np.sin(angle)*1)
            c = int(c + np.cos(angle)*1)
            if not (0<=r<ROWS and 0<=c<COLS):
                break
    # Only inside footprint
    cat &= footprint
    print(f"Catalogue pixels: {cat.sum()} ({100*cat.mean():.3f}% of raster, {100*cat.sum()/footprint.sum():.2f}% of footprint)")
    return cat

def dilate_mask(mask, radius_px):
    """Binary dilation by radius."""
    from scipy.ndimage import binary_dilation
    struct = np.ones((2*radius_px+1, 2*radius_px+1))
    # circular struct
    yy, xx = np.ogrid[-radius_px:radius_px+1, -radius_px:radius_px+1]
    struct = (xx*xx + yy*yy) <= radius_px*radius_px
    return binary_dilation(mask, structure=struct)

def make_prior(footprint, catalogue):
    """Synthetic km-scale prior: smooth random + fault interaction."""
    # Start white noise
    raw = rng.normal(0,1, size=(ROWS,COLS)).astype(np.float32)
    # Smooth with Gaussian approx (box blur x3)
    from scipy.ndimage import gaussian_filter
    smooth = gaussian_filter(raw, sigma=8)  # ~0.8km sigma -> km-scale
    # Add distance-to-catalogue term: high prior near catalogue intersections/step-overs
    # Compute distance to catalogue (approx via dilation rings)
    # For synthesis, use smoothed catalogue density
    cat_density = gaussian_filter(catalogue.astype(np.float32), sigma=15)
    prior = 0.6*smooth + 0.4*(cat_density*5)  # weight
    # Normalize to 0-1 for display, keep outside as nan
    prior -= prior[footprint].min()
    prior /= prior[footprint].max()
    prior[~footprint]=np.nan
    print(f"Prior inside footprint: mean {np.nanmean(prior):.3f} std {np.nanstd(prior):.3f}")
    return prior

def sample_dots(prior, footprint, catalogue, n_dots, exclude_buf_px, rng):
    """Weighted sampling without replacement, excluding catalogue buffer."""
    # Build exclusion mask
    cat_buf = dilate_mask(catalogue, exclude_buf_px) if exclude_buf_px>0 else catalogue
    eligible = footprint & (~cat_buf)
    # Cap prior to avoid zeros
    w = prior.copy()
    w[~eligible] = 0
    w = np.nan_to_num(w, nan=0)
    w = np.clip(w, 0.05, None)  # floor to allow sampling low-prior areas
    # Flatten eligible
    flat_idx = np.where(eligible.ravel())[0]
    weights = w.ravel()[flat_idx]
    weights = weights / weights.sum()
    chosen = rng.choice(flat_idx, size=n_dots, replace=False, p=weights)
    dots = np.zeros((ROWS,COLS), dtype=np.float32)
    # Convert flat to r,c and set unit mass
    # Use vectorized assignment
    dots_flat = dots.ravel()
    dots_flat[chosen] = 1.0
    dots = dots_flat.reshape(ROWS,COLS)
    # Also return coords list
    rs, cs = np.unravel_index(chosen, (ROWS,COLS))
    return dots, list(zip(rs,cs))

def dot_field_to_raster(dots, footprint):
    """Dots to raster values in [0,1] with NaN outside footprint. Same as R0: unit mass =1.0 dots."""
    raster = np.where(footprint, dots, np.nan).astype(np.float32)
    # Cap at 1 (dots are unit, no overlap except we ensured no replacement)
    raster = np.clip(raster, 0, 1)
    return raster

def write_tif(path, array, transform=TRANSFORM, crs=CRS, nodata=np.nan):
    with rasterio.open(path, 'w', driver='GTiff', height=ROWS, width=COLS, count=1, dtype='float32', crs=crs, transform=transform, nodata=nodata, compress='lzw') as dst:
        dst.write(array, 1)
        dst.update_tags(AXIS="CONCENTRATION", PARENT=PARENT_ID, CREATED=TODAY_DASH, NOTE="SYNTHETIC stand-in — not competition scoreable; see IRREGULARITIES.md")
    print(f"Wrote {path} sha8 {sha256_file(path)[:8]}")

def sha256_file(path):
    import hashlib
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def block_density_cv(dots, footprint, block_px=BLOCK_PX):
    """Compute CV of dot density per km-scale block."""
    n_br = ROWS // block_px
    n_bc = COLS // block_px
    # Trim to divisible
    trim_r = n_br*block_px
    trim_c = n_bc*block_px
    dots_trim = dots[:trim_r, :trim_c]
    fp_trim = footprint[:trim_r, :trim_c]
    # Reshape to blocks
    # dots per block
    # Use approach: reshape then sum
    # (n_br, block_px, n_bc, block_px) -> sum over block_px axes
    # Need to handle footprint denominator per block
    dots_blocks = dots_trim.reshape(n_br, block_px, n_bc, block_px).sum(axis=(1,3))
    fp_blocks = fp_trim.reshape(n_br, block_px, n_bc, block_px).sum(axis=(1,3))
    # density = dots / footprint_px per block; avoid divide by zero
    density = np.divide(dots_blocks, fp_blocks, out=np.zeros_like(dots_blocks, dtype=float), where=fp_blocks>0)
    # Only blocks with footprint >50%
    valid = fp_blocks > (block_px*block_px*0.5)
    vals = density[valid]
    cv = float(np.std(vals) / np.mean(vals)) if np.mean(vals)!=0 else 0
    return cv, vals.mean(), vals.std(), valid.sum()

def concentration_shift(dots, footprint, prior, pct):
    """
    Move pct fraction of dots from lowest-prior blocks to highest-prior blocks.
    pct e.g. 0.10 for 10%
    Block size 1km (10px). State block CV before/after.
    Returns new dots, stats.
    """
    n_move = int(N_DOTS_R0 * pct)
    # Compute block prior mean
    n_br = ROWS // BLOCK_PX
    n_bc = COLS // BLOCK_PX
    trim_r, trim_c = n_br*BLOCK_PX, n_bc*BLOCK_PX
    prior_trim = prior[:trim_r, :trim_c]
    # block prior mean (ignore NaN)
    prior_blocks = np.nanmean(prior_trim.reshape(n_br, BLOCK_PX, n_bc, BLOCK_PX), axis=(1,3))
    # Rank blocks low->high
    flat_prior = prior_blocks.ravel()
    flat_idx = np.argsort(flat_prior)  # low first
    # Need footprint-aware: some blocks have low footprint, but still ranked
    # Find dots in low blocks vs high blocks
    # Build block id per pixel
    # Create block id map
    # For each pixel, block id = (r//BLOCK_PX)*n_bc + c//BLOCK_PX
    # To pick dots to move: sort blocks low prio, iterate, collect dot coordinates
    # To place: sort blocks high prio, iterate, find empty eligible pixels (footprint & not catalogue buffer & not already occupied)
    # Recompute eligible from footprint minus catalogue buffer and existing dots
    # But we need catalogue for exclusion; pass global
    # Instead, caller must provide catalogue; we will handle here with synthesis catalogue
    return None  # placeholder — implemented inline in main

# === MAIN ===
print("=== Synthetic R0 + CONCENTRATION variants (STAND-IN) ===")
footprint = make_footprint()
catalogue = make_catalogue(footprint)
prior = make_prior(footprint, catalogue)

# Save synthetic_inputs for inspection
import rasterio
for name, arr in [("footprint", footprint.astype(np.uint8)*255), ("catalogue", catalogue.astype(np.uint8)), ("prior", prior)]:
    # save as GeoTIFF for QA (not part of releases)
    dtype = 'float32' if arr.dtype==np.float32 else 'uint8'
    nod = np.nan if dtype=='float32' else 0
    arr_out = arr.astype('float32') if dtype=='float32' else arr
    with rasterio.open(SYNTH_DIR / f"{name}.tif", 'w', driver='GTiff', height=ROWS, width=COLS, count=1, dtype=dtype, crs=CRS, transform=TRANSFORM, nodata=nod, compress='lzw') as dst:
        if dtype=='float32':
            # prior: keep NaN outside
            out = np.where(footprint, arr, np.nan).astype(np.float32) if name=="prior" else arr.astype(np.float32)
            dst.write(out,1)
        else:
            dst.write(arr_out,1)

# Sample R0
dots_r0, coords_r0 = sample_dots(prior, footprint, catalogue, N_DOTS_R0, CATALOGUE_BUFFER_PX, rng)
cv_before, mean_d, std_d, nblocks = block_density_cv(dots_r0, footprint)
print(f"R0 CV before: {cv_before:.3f} mean dens {mean_d:.5f} std {std_d:.5f} nblocks {nblocks}")

# Save synthetic R0 raster (for ledger parent reference)
raster_r0 = dot_field_to_raster(dots_r0, footprint)
write_tif(SYNTH_DIR / "h33-h33-2-b2_synthetic.tif", raster_r0)
write_tif(SYNTH_DIR / "h33-h33-2-b2_synthetic-zeros.tif", np.where(footprint, raster_r0, 0).astype(np.float32))

# Now build 3 concentration variants
# Need block prior ranking reuse
n_br = ROWS // BLOCK_PX
n_bc = COLS // BLOCK_PX
trim_r, trim_c = n_br*BLOCK_PX, n_bc*BLOCK_PX
prior_trim = prior[:trim_r, :trim_c]
# handle NaN blocks: if block mean NaN (outside footprint), set to -inf so not chosen as destination? Actually we want hi prior destinations inside footprint
prior_blocks = np.nanmean(prior_trim.reshape(n_br, BLOCK_PX, n_bc, BLOCK_PX), axis=(1,3))
# For ranking, replace NaN with -1 (lowest)
prior_blocks_filled = np.where(np.isnan(prior_blocks), -1, prior_blocks)
flat_order = np.argsort(prior_blocks_filled.ravel())  # low->high
# Build block id map for all pixels
br_idx = np.repeat(np.arange(n_br), BLOCK_PX)[:ROWS]  # but need 2D — easier compute per dot
# Function to get block id for (r,c)
def block_id(r,c):
    return (r//BLOCK_PX)*n_bc + c//BLOCK_PX

# Precompute per-pixel block id flat
rr_grid, cc_grid = np.mgrid[:ROWS, :COLS]
block_map = (rr_grid//BLOCK_PX)*n_bc + (cc_grid//BLOCK_PX)
block_map[~footprint] = -1  # outside

# Also precompute catalogue buffer for exclusion (must hold >=3px for variants per hard constraint 4)
CATALOGUE_BUFFER_VARIANT = 3
cat_buf_variant = dilate_mask(catalogue, CATALOGUE_BUFFER_VARIANT)

variants = [(0.10, "10"), (0.15, "15"), (0.20, "20")]
results = []

for pct, label in variants:
    n_move = int(N_DOTS_R0 * pct)
    print(f"\n--- CONCENTRATION {label}%: moving {n_move} dots ({pct*100:.0f}%) ---")
    # Start from R0 copy
    dots = dots_r0.copy()
    # Enforce >=3px catalogue exclusion for variants (R0 had 2px). Prune any dots violating new 3px buffer and count them toward move budget.
    # This is required by Hard constraint 4 (emit zero on catalogue and >=3px unless AXIS=PRUNE).
    violating = (dots==1) & cat_buf_variant
    n_violate = int(violating.sum())
    if n_violate>0:
        print(f"  pruning {n_violate} dots violating 3px buffer (R0 had 2px, variant requires 3px)")
        dots[violating]=0
        # These freed slots still need refill to hold count; treat as part of n_move budget later (we will need to place n_move + n_violate or just n_move?)
        # To keep % changed semantics clean, we consider n_move inclusive of this prune, but we must restore count to N_DOTS_R0
        # So total to place = n_move (as if budget includes violates); if violates >0, we reduce additional low-prior removals accordingly.
        # Simpler: total to place = n_move; already removed n_violate, so need n_move - n_violate more from low blocks.
        n_move_remaining = max(0, n_move - n_violate)
    else:
        n_move_remaining = n_move
    # Identify source blocks (lowest prior) and destination blocks (highest prior)
    # Need to collect dots to remove: iterate low blocks in order, gather their dots
    # Dots coordinates array for quick lookup
    # Create mask of dot locations
    dot_mask = dots==1
    # Build candidate lists
    # Source block order: low prior first
    src_blocks = flat_order  # low first
    dst_blocks = flat_order[::-1]  # high first
    # Collect n_move_remaining dots from low blocks (violation prune already removed some)
    to_remove = []
    for bid in src_blocks:
        if len(to_remove) >= n_move_remaining:
            break
        br = bid // n_bc
        bc = bid % n_bc
        r0 = br*BLOCK_PX; r1 = min(r0+BLOCK_PX, ROWS)
        c0 = bc*BLOCK_PX; c1 = min(c0+BLOCK_PX, COLS)
        # dots in this block
        block_dots = np.where(dot_mask[r0:r1, c0:c1])
        for dr, dc in zip(block_dots[0], block_dots[1]):
            to_remove.append((r0+dr, c0+dc))
            if len(to_remove) >= n_move_remaining:
                break
    print(f"  collected {len(to_remove)} source dots from low-prior blocks (plus {n_violate} buffer-pruned = {len(to_remove)+n_violate} total removed)")
    # Remove them
    for r,c in to_remove:
        dots[r,c]=0
    # Now find empty eligible pixels in high blocks to place them
    # Eligible = footprint & ~cat_buf_variant & ~dot_mask (updated)
    dot_mask_after_removal = dots==1
    eligible = footprint & (~cat_buf_variant) & (~dot_mask_after_removal)
    total_to_place = n_violate + len(to_remove)  # should equal n_move unless rounding
    # For reproducibility, within each high block sample random empty pixels weighted by prior value (higher within block more likely)
    # But brief says move to highest-prior blocks — simplest: random uniform inside those blocks
    # We'll fill block by block high->low, random placement within block
    placed=0
    rng_variant = np.random.default_rng(RNG_SEED + int(pct*100))  # deterministic per variant
    for bid in dst_blocks:
        if placed >= total_to_place:
            break
        br = bid // n_bc
        bc = bid % n_bc
        r0 = br*BLOCK_PX; r1 = min(r0+BLOCK_PX, ROWS)
        c0 = bc*BLOCK_PX; c1 = min(c0+BLOCK_PX, COLS)
        block_elig = eligible[r0:r1, c0:c1]
        # count empty
        empties = np.where(block_elig)
        n_empty = len(empties[0])
        if n_empty==0:
            continue
        need = min(total_to_place - placed, n_empty)
        # Sample without replacement
        chosen_idx = rng_variant.choice(n_empty, size=need, replace=False)
        for idx in chosen_idx:
            r = r0 + empties[0][idx]
            c = c0 + empties[1][idx]
            dots[r,c]=1
            placed+=1
            if placed>=total_to_place:
                break
    print(f"  placed {placed} dots into high-prior blocks (target {total_to_place})")
    # Compute CV after
    cv_after, mean_a, std_a, _ = block_density_cv(dots, footprint)
    print(f"  CV before {cv_before:.3f} -> after {cv_after:.3f} (Δ {cv_after-cv_before:+.3f})")
    # Validate counts and catalogue exclusion
    assert dots.sum()==N_DOTS_R0, f"count mismatch {dots.sum()}"
    assert np.sum(dots[cat_buf_variant])==0, "catalogue buffer violation!"
    # Compute pct changed
    changed = np.sum(dots != dots_r0) //2  # each moved dot is 1 removal +1 addition =2 diffs, but brief says % changed = moved/pct
    # Better: n_move / N = pct changed; record both
    # For ledger we report % changed = moved count / total *100
    pct_changed = 100*pct  # by construction
    # Alternative exact diff pct:
    diff_px = np.sum(dots != dots_r0)
    print(f"  diff pixels {diff_px} (expected {n_move*2})")
    # Write rasters
    raster = dot_field_to_raster(dots, footprint)
    raster_zeros = np.where(footprint, raster, 0).astype(np.float32)
    vid = f"{PARENT_ID}-CONC{label}-{TODAY}-{sha256_file(SYNTH_DIR/'h33-h33-2-b2_synthetic.tif')[:8]}"
    # Actually sha8 should be of output file, not parent — but brief says name <parent>-<axis><value>-<yyyymmdd>-<sha8>
    # sha8 is output file's sha8 (first 8 of sha256)
    # We'll write then rename with sha8
    tmp_path = OUTDIR / f"tmp_{label}.tif"
    write_tif(tmp_path, raster)
    sha = sha256_file(tmp_path)
    sha8 = sha[:8]
    final_name = f"{PARENT_ID}-CONC{label}-{TODAY}-{sha8}.tif"
    final_zeros = f"{PARENT_ID}-CONC{label}-{TODAY}-{sha8}-zeros.tif"
    tmp_path.rename(OUTDIR / final_name)
    write_tif(OUTDIR / final_zeros, raster_zeros)
    sha_zeros = sha256_file(OUTDIR / final_zeros)
    print(f"  -> {final_name} sha8 {sha8} sha256 {sha}")
    print(f"  -> {final_zeros} sha8 {sha_zeros[:8]}")
    results.append({
        "pct": pct, "label": label, "n_move": n_move, "cv_before": cv_before, "cv_after": cv_after,
        "final_name": final_name, "final_zeros": final_zeros, "sha": sha, "sha8": sha8, "sha_zeros": sha_zeros,
        "pct_changed": pct*100, "diff_px": int(diff_px)
    })

# Write summary json for ledger builder
with open("synthetic_inputs/variant_summary.json","w") as f:
    json.dump({"parent": PARENT_ID, "axis": "CONCENTRATION", "block_px": BLOCK_PX, "block_km": BLOCK_PX*100/1000, "cv_before": cv_before, "variants": results, "n_dots": N_DOTS_R0, "catalogue_buffer_variant_px": CATALOGUE_BUFFER_VARIANT, "note": "SYNTHETIC stand-in, see IRREGULARITIES.md"}, f, indent=2)
print("\nDone. Summary written.")
