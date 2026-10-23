"""
DTI metric implementation per brief v2 verified facts.
Metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
DTI with alpha 0.2, beta 0.8, triangular kernel R=300m (3 px at 100m).

Algebra (derived; unit-test it):
  DTI = T / (0.2*T + 0.2*(S-M) + 0.8*|G|)
  where T = kernel credit (sum over truth pixels of p * k(dist)),
        S = sum p (total predicted mass),
        M = sum p*max_g k (max kernel credit any truth pixel gives to that pred pixel),
        |G| = number of truth pixels (ground truth fault count)
  k(d) = 1 - d/R for d < R, else 0; triangular, R=3px.

For isolated truth pixel, dot pays iff credit > 0.2*DTI (~0.056 at DTI=0.28).
Line-like truth lowers bar — rank dots by exact marginal gain, not shortcut.
"""
import numpy as np

ALPHA = 0.2
BETA = 0.8
R_PX = 3  # 300m / 100m

def triangular_kernel(dist_px, R=R_PX):
    """dist in pixels, R in pixels."""
    return np.maximum(0, 1 - dist_px / R)

def build_kernel(R=R_PX):
    """2D triangular kernel size 2R+1."""
    sz = 2*R + 1
    k = np.zeros((sz, sz), dtype=np.float32)
    for dy in range(-R, R+1):
        for dx in range(-R, R+1):
            d = np.sqrt(dx*dx + dy*dy)
            if d < R:
                k[dy+R, dx+R] = 1 - d / R
    return k

KERNEL = build_kernel()

def dti_score(pred, truth_mask, footprint_mask=None):
    """
    pred: 2D float array in [0,1], footprint-consistent
    truth_mask: 2D bool/int array, 1=truth fault pixel
    footprint_mask: bool, True=inside footprint (scored). If None, all True where not NaN.
    Returns DTI float.
    """
    if footprint_mask is None:
        footprint_mask = ~np.isnan(pred) if np.issubdtype(pred.dtype, np.floating) else np.ones_like(pred, dtype=bool)
    # Only scored inside footprint
    # S, T, M computed over footprint; G is count of truth pixels inside footprint
    # Truth outside footprint is not present (masked).
    # k is triangular R=3px
    from scipy.signal import convolve2d
    # T: sum over truth pixels of (pred * k) convolved? Equivalent: for each truth pixel, sum pred weighted by k(dist)
    # Efficient: convolve pred*kernel, then sample at truth locations, sum.
    # Need careful with NaN: treat NaN as 0 credit but not counted in S? Actually S sums pred over footprint only.
    pred_f = np.where(footprint_mask, pred, 0).astype(np.float32)
    # Convolve
    # Use mode same
    # Scipy may not be available; fallback to manual?
    try:
        from scipy.signal import convolve2d
        # credit map: for each truth pixel location, the kernel-weighted sum of nearby pred
        credit_map = convolve2d(pred_f, KERNEL, mode='same', boundary='fill', fillvalue=0)
        # M: for each pred pixel, max_g k = max kernel value to any truth pixel
        # That's dilate truth with kernel footprint max
        # For triangular kernel, max_k = max distance kernel value to nearest truth
        # Compute distance to nearest truth via convolution trick: max kernel value = 1 - dist/R if within R
        # Simpler brute for small R: for each pred pixel, look at truth in 7x7 window, take max kernel
        truth_f = (truth_mask & footprint_mask).astype(np.float32)
        # To get max_k map, we can for each offset, shift truth and compute max of kernel value where truth present
        max_k = np.zeros_like(pred_f)
        for dy in range(-R_PX, R_PX+1):
            for dx in range(-R_PX, R_PX+1):
                d = np.sqrt(dx*dx + dy*dy)
                if d >= R_PX:
                    continue
                kval = 1 - d / R_PX
                # shift truth
                shifted = np.roll(np.roll(truth_f, dy, axis=0), dx, axis=1)
                # zero out wraparound
                if dy > 0:
                    shifted[:dy, :] = 0
                elif dy < 0:
                    shifted[dy:, :] = 0
                if dx > 0:
                    shifted[:, :dx] = 0
                elif dx < 0:
                    shifted[:, dx:] = 0
                max_k = np.maximum(max_k, shifted * kval)
        T = np.sum(credit_map * (truth_mask & footprint_mask))
        S = np.sum(pred_f)
        M = np.sum(pred_f * max_k)
        G = np.sum(truth_mask & footprint_mask)
        denom = 0.2*T + 0.2*(S - M) + 0.8*G
        if denom == 0:
            return 0.0
        return float(T / denom)
    except ImportError:
        raise ImportError("scipy required for DTI; pip install scipy")

def marginal_gain_dot(pred_base, truth_mask, footprint_mask, r, c, val=1.0):
    """Exact marginal gain of adding a dot at (r,c) with value val."""
    # pred_base includes existing dots; compute DTI before and after
    # For ranking, we want gain if we add this dot alone to empty? Or to current?
    # Brief: rank dots by exact marginal gain from the metric code, not shortcut.
    # We implement incremental to current pred.
    # T increment = sum over truth within R of val*k(dist)
    # S increment = val
    # M increment = val*max_k (max kernel to nearest truth)
    # But DTI is non-linear, so true marginal = DTI(pred+dot) - DTI(pred)
    # Use before/after DTI directly (expensive but exact for ranking via vectorized).
    # For ranking many dots, compute delta analytically then sort; but for proof we provide exact function.
    pred_after = pred_base.copy()
    pred_after[r, c] = np.clip(pred_after[r, c] + val, 0, 1)
    # handle footprint outside: no gain
    if footprint_mask is not None and not footprint_mask[r, c]:
        return 0.0
    dti_before = dti_score(pred_base, truth_mask, footprint_mask)
    dti_after = dti_score(pred_after, truth_mask, footprint_mask)
    return dti_after - dti_before

# Unit test per brief algebra
def test_algebra():
    """Isolated truth pixel: dot at same pixel should give T=1, S=1, M=1, G=1 => DTI=1/(0.2*1+0.8*1)=1.0"""
    pred = np.zeros((10,10), dtype=np.float32)
    truth = np.zeros((10,10), dtype=bool)
    pred[5,5]=1.0
    truth[5,5]=True
    footprint = np.ones((10,10), dtype=bool)
    score = dti_score(pred, truth, footprint)
    assert abs(score - 1.0) < 1e-6, f"Isolated perfect dot failed: {score}"
    # Dot 300m away (3px) should give T=0, S=1, M=0 => DTI=0
    pred2 = np.zeros((10,10), dtype=np.float32)
    pred2[5,8]=1.0
    score2 = dti_score(pred2, truth, footprint)
    assert abs(score2 - 0.0) < 1e-6, f"Far dot should be 0: {score2}"
    # Adjacent dot 1px away: k=1-1/3=0.666
    pred3 = np.zeros((10,10), dtype=np.float32)
    pred3[5,6]=1.0
    score3 = dti_score(pred3, truth, footprint)
    # T=0.666, S=1, M=0.666, G=1 => DTI=0.666/(0.2*0.666+0.2*(1-0.666)+0.8)=0.666/(0.133+0.066+0.8)=0.666/1.0=0.666
    assert abs(score3 - 0.666) < 0.01, f"1px dot failed: {score3}"
    print("DTI algebra tests passed")

if __name__ == "__main__":
    test_algebra()
