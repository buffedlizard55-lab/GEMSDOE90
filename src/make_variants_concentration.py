"""
CONCENTRATION axis: move 10-20% of dots from lowest-prior km-scale blocks to highest-prior ones.
State block size; report block-density CV before/after (best files 0.51-0.59).

Mechanism: favor block-scale fault-interaction zones derived from synthetic favourability
prior (intersection of basin range-front + step-over density). Moving mass concentrates signal
where geothermal systems cluster, potentially matching expert-expanded private labels.

We create 3 variants:
 - CONC10: block 2000m, move 10% (3765 dots)
 - CONC15: block 1000m, move 15% (5648 dots)
 - CONC20: block 5000m, move 20% (7530 dots)

Each differs ONLY on CONCENTRATION axis; same count, same exclusions.
"""
import numpy as np
import rasterio
from pathlib import Path
import sys
sys.path.insert(0, ".")
from src.config import *
from src.utils import write_raster, sha256_file, parent_diff_stats, dilate_mask
from scipy.ndimage import gaussian_filter

# Load required arrays
def load_arrays():
    with rasterio.open(SAMPLE_PATH) as src:
        sample = src.read(1)
        profile = src.profile
        transform = src.transform
        crs = src.crs
    footprint = ~np.isnan(sample)
    # For more accurate footprint, also load footprint file if exists
    # catalogue
    with rasterio.open(CATALOGUE_PATH) as src:
        catalogue = src.read(1) > 0.5
    # parent raster
    with rasterio.open(PARENT_PATH) as src:
        parent = src.read(1)
    # score field for ranking empty pixels
    with rasterio.open(SCORE_PATH) as src:
        score = src.read(1)
    # ranking info (for eligibility)
    ranking = np.load(RANKING_PATH, allow_pickle=True).item()
    # elevation norm for prior
    try:
        with rasterio.open("data/elev_norm.tif") as src:
            elev_norm = src.read(1)
    except:
        elev_norm = np.zeros_like(sample)
        elev_norm[footprint] = 0.5
    return footprint, catalogue, parent, score, ranking, elev_norm, profile

def make_prior_field(footprint, catalogue, elev_norm, score):
    """
    Fault-interaction prior: high where
     - distance to catalogue intersections high (step-over density)
     - range-front high (detrended elevation intermediate-high)
     - score field high (proxy for geophysical favorability)

    Synthetic: prior = 0.5*intersection_density + 0.3*range_front + 0.2*score_smooth
    Intersection density: dilate catalogue, find where 2+ faults within 500m -> high
    """
    # Intersection density: we approximate by convolving catalogue with 5px kernel, then count where sum > threshold
    from scipy.ndimage import convolve
    cat_f = catalogue.astype(np.float32)
    # Dilate catalogue slightly then count overlaps
    # Use kernel 11x11 ones
    kernel = np.ones((11,11), dtype=np.float32)
    cat_density = convolve(cat_f, kernel, mode="constant", cval=0)
    # Normalize
    cat_density = cat_density / cat_density.max() if cat_density.max()>0 else cat_density
    # Range-front: elevation terciles — prior high at piedmont/range front (elev 0.4-0.8)
    # elev_norm 0 basin, 1 high ranges; step-over often at piedmont
    range_front = np.zeros_like(elev_norm)
    # Compute prior shape: peak at 0.6
    # Use Gaussian around 0.6
    range_front = np.exp(-((elev_norm - 0.6)/0.25)**2)
    range_front[~footprint] = 0
    # Score smooth
    score_smooth = gaussian_filter(np.where(np.isnan(score), 0, score), sigma=5)
    score_smooth = (score_smooth - score_smooth.min()) / (score_smooth.max() - score_smooth.min() + 1e-9)
    prior = 0.45*cat_density + 0.35*range_front + 0.20*score_smooth
    prior[~footprint] = np.nan
    print(f"Prior stats: min {np.nanmin(prior):.3f} max {np.nanmax(prior):.3f} mean {np.nanmean(prior):.3f}")
    return prior, cat_density, range_front, score_smooth

def compute_block_stats(dots_bool, footprint, prior, block_px):
    """
    Block = km-scale square blocks (e.g., 1000m=10px, 2000m=20px, 5000m=50px)
    Compute per-block density and CV.
    """
    H,W = dots_bool.shape
    # Number of blocks
    nby = (H + block_px -1)//block_px
    nbx = (W + block_px -1)//block_px
    densities = []
    prior_means = []
    valid_blocks = 0
    for by in range(nby):
        for bx in range(nbx):
            y0 = by*block_px
            y1 = min((by+1)*block_px, H)
            x0 = bx*block_px
            x1 = min((bx+1)*block_px, W)
            block_mask = footprint[y0:y1, x0:x1]
            if block_mask.sum() == 0:
                continue
            dots_in = dots_bool[y0:y1, x0:x1].sum()
            # density = dots per valid px
            dens = dots_in / block_mask.sum()
            densities.append(dens)
            # prior mean per block
            pblock = prior[y0:y1, x0:x1]
            pvalid = pblock[~np.isnan(pblock)]
            if pvalid.size:
                prior_means.append(pvalid.mean())
            else:
                prior_means.append(0)
            valid_blocks +=1
    densities = np.array(densities)
    prior_means = np.array(prior_means)
    if densities.size:
        mean = densities.mean()
        std = densities.std()
        cv = std/mean if mean!=0 else 0
    else:
        cv=0
        mean=0
        std=0
    return {"cv": cv, "mean": mean, "std": std, "densities": densities, "prior_means": prior_means, "n_blocks": valid_blocks}

def make_concentration_variant(parent, footprint, catalogue, score, prior, block_m, pct_move, variant_name):
    """
    Move pct_move % of dots from lowest-prior blocks to highest-prior blocks.
    Within target blocks, choose highest-ranked empty pixels (by score).
    Same count, same exclusions (zero mass on catalogue, >=3px away unless PRUNE)
    """
    block_px = block_m // 100  # 100m px
    H,W = parent.shape
    dots = (parent > 0.5) & footprint
    # Compute block prior means and block assignment per pixel
    # Build block index map
    block_ids = np.full((H,W), -1, dtype=int)
    nby = (H + block_px -1)//block_px
    nbx = (W + block_px -1)//block_px
    block_prior = {}
    block_valid_pixels = {}
    bid = 0
    for by in range(nby):
        for bx in range(nbx):
            y0 = by*block_px
            y1 = min((by+1)*block_px, H)
            x0 = bx*block_px
            x1 = min((bx+1)*block_px, W)
            # compute prior mean for this block
            pblock = prior[y0:y1, x0:x1]
            valid = footprint[y0:y1, x0:x1]
            if valid.sum()==0:
                continue
            pvalid = pblock[valid]
            # nan safe
            pvalid = pvalid[~np.isnan(pvalid)]
            mean_prior = pvalid.mean() if pvalid.size else 0
            block_prior[bid] = mean_prior
            block_valid_pixels[bid] = (y0,y1,x0,x1)
            block_ids[y0:y1, x0:x1] = bid
            bid+=1
    # Assign each dot to block
    # For each block, count dots
    block_dot_counts = {b:0 for b in block_prior}
    # Also for each pixel, know its block
    dot_ys, dot_xs = np.where(dots)
    dot_blocks = block_ids[dot_ys, dot_xs]
    for db in dot_blocks:
        if db>=0:
            block_dot_counts[db] +=1
    # Sort blocks by prior
    sorted_blocks = sorted(block_prior.items(), key=lambda x: x[1])
    # Lowest-prior blocks to remove from; highest-prior to add to
    # Number of dots to move = pct_move * n_parent
    n_move = int(round(len(dot_ys) * pct_move / 100))
    print(f"Variant {variant_name}: block {block_m}m ({block_px}px) move {pct_move}% = {n_move} dots")
    print(f" Blocks prior min {min(block_prior.values()):.3f} max {max(block_prior.values()):.3f}")
    # Need to select dots to remove: pick from lowest-prior blocks, lowest score within those blocks (worst dots)
    # Create score per dot
    dot_scores = score[dot_ys, dot_xs]
    # For dots in NaN score (should not happen inside footprint, but fill)
    dot_scores = np.where(np.isnan(dot_scores), 0, dot_scores)
    # Build list of candidates for removal sorted by (block_prior asc, score asc)
    # We'll iterate blocks low->high, and within each block sort dots by score ascending
    removal_candidates = []
    # For each block in sorted low->high, collect dots in that block sorted by score low->high
    for bid, prior_val in sorted_blocks:
        idxs_in_block = np.where(dot_blocks == bid)[0]
        if idxs_in_block.size==0:
            continue
        scores_in_block = dot_scores[idxs_in_block]
        order = np.argsort(scores_in_block)  # low first
        for idx in idxs_in_block[order]:
            removal_candidates.append(idx)
            if len(removal_candidates) >= n_move:
                break
        if len(removal_candidates) >= n_move:
            break
    # If not enough in low blocks (should be enough), fill randomly
    if len(removal_candidates) < n_move:
        extra = n_move - len(removal_candidates)
        remaining = [i for i in range(len(dot_ys)) if i not in removal_candidates]
        # choose lowest scores among remaining
        rem_scores = dot_scores[remaining]
        order = np.argsort(rem_scores)
        removal_candidates.extend([remaining[i] for i in order[:extra]])
    # Dots to remove
    rem_ys = dot_ys[removal_candidates]
    rem_xs = dot_xs[removal_candidates]

    # Dots to add: choose highest-ranked empty eligible pixels within highest-prior blocks
    # Eligible = footprint valid & not catalogue & not within 2px (i.e., keep >=3px) & not already dot
    cat_buf2 = dilate_mask(catalogue, 2)
    eligible = footprint & ~catalogue & ~cat_buf2 & ~dots
    # For CONCENTRATION we enforce >=3px buffer per hard constraint 4 (unless PRUNE) => dilate 2
    # Eligible pixels sorted by score descending, but weighted by block prior: prefer high-prior blocks
    # Instead of pure score, we could rank by score + prior boost, but spec says "move to highest-prior blocks" — implies within those blocks, use ranking.
    # We'll collect eligible pixels per high-prior block, sorted by score high->low, then take top n_move.

    # Gather eligible per block
    eligible_ys, eligible_xs = np.where(eligible)
    eligible_scores = score[eligible_ys, eligible_xs]
    eligible_scores = np.where(np.isnan(eligible_scores), -np.inf, eligible_scores)
    eligible_blocks = block_ids[eligible_ys, eligible_xs]
    # For each block high->low, collect sorted eligible
    sorted_blocks_desc = sorted(block_prior.items(), key=lambda x: x[1], reverse=True)
    add_candidates_y = []
    add_candidates_x = []
    for bid, prior_val in sorted_blocks_desc:
        idxs = np.where(eligible_blocks == bid)[0]
        if idxs.size ==0:
            continue
        sc = eligible_scores[idxs]
        order = np.argsort(sc)[::-1]
        for oi in order:
            add_candidates_y.append(eligible_ys[idxs[oi]])
            add_candidates_x.append(eligible_xs[idxs[oi]])
            if len(add_candidates_y) >= n_move:
                break
        if len(add_candidates_y) >= n_move:
            break
    if len(add_candidates_y) < n_move:
        print(f" WARN not enough eligible pixels in high-prior blocks: need {n_move}, have {len(add_candidates_y)} — will fill from global top-ranked eligible")
        # Fill from global top-ranked
        # eligible sorted globally
        order_global = np.argsort(eligible_scores)[::-1]
        # Exclude already chosen
        chosen_set = set(zip(add_candidates_y, add_candidates_x))
        for idx in order_global:
            y,x = eligible_ys[idx], eligible_xs[idx]
            if (y,x) in chosen_set:
                continue
            add_candidates_y.append(y)
            add_candidates_x.append(x)
            if len(add_candidates_y) >= n_move:
                break
    if len(add_candidates_y) < n_move:
        raise RuntimeError(f"Insufficient eligible pixels to add {n_move}")

    add_ys = np.array(add_candidates_y[:n_move])
    add_xs = np.array(add_candidates_x[:n_move])

    # Build variant raster: remove then add
    variant = parent.copy()
    # Ensure footprint outside remains NaN (parent has NaN outside)
    # Remove
    variant[rem_ys, rem_xs] = 0.0
    # Add
    variant[add_ys, add_xs] = 1.0
    # Verify: still no catalogue mass, buffer respected (by construction eligible already respects)
    # Count
    n_new = int(np.sum((variant>0.5) & footprint))
    print(f" Variant dot count after move: {n_new} (parent {len(dot_ys)})")
    # Compute CV before/after
    before_stats = compute_block_stats(dots, footprint, prior, block_px)
    after_dots = (variant>0.5) & footprint
    after_stats = compute_block_stats(after_dots, footprint, prior, block_px)
    print(f" CV before {before_stats['cv']:.3f} after {after_stats['cv']:.3f} (target 0.51-0.59 per ledger best files)")
    # Mean displacement: average distance moved? For each removed dot, distance to nearest added? Simpler: mean distance between random pairs? But spec for SNAP mean displacement, for CONCENTRATION not required but report block-density CV.
    # For concentration, we report CV.
    return variant, before_stats, after_stats, n_move, rem_ys, rem_xs, add_ys, add_xs

def main():
    footprint, catalogue, parent, score, ranking, elev_norm, profile = load_arrays()
    prior, cat_density, range_front, score_smooth = make_prior_field(footprint, catalogue, elev_norm, score)

    # Define 3 variants
    variants = [
        (2000, 10, "CONC10"),
        (1000, 15, "CONC15"),
        (5000, 20, "CONC20"),
    ]

    import datetime
    date_str = datetime.datetime.utcnow().strftime("%Y%m%d")
    # Use parent name from config
    results = []
    for block_m, pct, label in variants:
        variant, before, after, n_move, rem_y, rem_x, add_y, add_x = make_concentration_variant(parent, footprint, catalogue, score, prior, block_m, pct, label)
        # Name: <parent>-<axis><value>-<yyyymmdd>-<sha8>.tif
        # For CONCENTRATION axis, value = block_m + pct? Spec says (AXIS,value) pair built once. We'll encode as e.g., CONC10b2000
        # But for distinct files we need distinct names: include block and pct.
        # We'll use <parent>-CONC<pct>-b<block>-<date>-<sha8> but need to keep axis value simple? Use CONC<block>_<pct>
        # Simplify: id = f"{PARENT_NAME}-CONC{block_m // 1000}km{pct}pct-{date_str}"
        # Let's use PARENT_NAME-CONC<block>-<pct>... We'll keep human readable.
        # However spec says Name: <parent>-<axis><value>-<yyyymmdd>-<sha8>. So axis=CONC, value maybe 2000-10 etc.
        # We'll encode value as f"{block_m}M{pct}PCT"
        value_str = f"{block_m}M{pct}PCT"
        base_name = f"{PARENT_NAME}-CONC{value_str}-{date_str}"
        # Temporary path without sha
        tmp_path = f"releases/{base_name}.tif"
        # Write primary (NaN outside) and zeros
        write_raster(tmp_path, variant, nodata_outside="nan")
        sha8 = sha256_file(tmp_path)[:8]
        final_name = f"{PARENT_NAME}-CONC{value_str}-{date_str}-{sha8}"
        final_path = f"releases/{final_name}.tif"
        final_zeros = f"releases/{final_name}-zeros.tif"
        # Rename tmp to final (move)
        import os, shutil
        if tmp_path != final_path:
            shutil.move(tmp_path, final_path)
        write_raster(final_zeros, variant, nodata_outside="zero")
        # Validate
        from src.validate import validate_raster
        ok, msgs = validate_raster(final_path, is_parent=False)
        print(f" Validation {final_name}: {ok}")
        for m in msgs:
            print(" ", m)
        if not ok:
            print(f" ERROR variant {final_name} failed validation, not recording")
            continue
        # Parent diff
        stats = parent_diff_stats(parent, variant)
        # Block CV reporting
        # Prepare ledger entry
        results.append({
            "id": final_name,
            "parent": PARENT_NAME,
            "axis": "CONCENTRATION",
            "value": value_str,
            "n_dots": int((variant[footprint]>0.5).sum()),
            "pct_changed": round(stats["pct_changed"], 2),
            "sha256": sha256_file(final_path),
            "sha8": sha8,
            "predicted_change": None,  # to fill later with MODEL estimate
            "block_m": block_m,
            "pct_move": pct,
            "cv_before": round(before["cv"], 3),
            "cv_after": round(after["cv"], 3),
            "path": final_path,
            "zeros_path": final_zeros,
            "before_stats": before,
            "after_stats": after,
        })
        print(f" Built {final_name} pct_changed {stats['pct_changed']:.2f}% CV {before['cv']:.3f}->{after['cv']:.3f}")

    # Write ledger entries: append to ledger/submissions.csv (create if not exists)
    # Also produce mechanism cards
    # Return results for further writing
    import json, csv
    # Ensure ledger dir
    Path("ledger").mkdir(exist_ok=True)
    # We'll output results json for next step
    with open("data/variant_results.json", "w") as f:
        # Convert non-serializable
        json.dump([{k: v for k,v in r.items() if k not in ("before_stats","after_stats")} for r in results], f, indent=2)
    print(f"Wrote {len(results)} variants")
    # Also save detailed for report
    with open("data/variant_details.json","w") as f:
        detailed=[]
        for r in results:
            detailed.append({
                "id": r["id"],
                "cv_before": r["cv_before"],
                "cv_after": r["cv_after"],
                "pct_changed": r["pct_changed"],
                "block_m": r["block_m"],
            })
        json.dump(detailed,f,indent=2)
    return results

if __name__ == "__main__":
    main()
