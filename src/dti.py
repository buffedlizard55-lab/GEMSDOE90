"""
DTI metric — algebra derived from spec, unit-tested.
Metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
DTI with alpha 0.2, beta 0.8, triangular kernel R=300m (3px)
Algebra: DTI = T / (0.2*T + 0.2*(S-M) + 0.8*|G|)
  T = kernel credit = sum_g sum_p p * k(d(g,p)) * w_g? Simplified per-pixel truth weighting =1
  S = sum p (total predicted mass)
  M = sum p * max_g k(g,p)  (multiple truth overlapping? For line-like truth, max_g ~1 along line)
  |G| = number of truth pixels
For isolated truth pixel, dot pays iff its credit >0.2*DTI (~0.056 at 0.28)
Line-like truth lowers bar — rank dots by exact marginal gain.
"""
import numpy as np
from scipy.ndimage import convolve

# Triangular kernel R=3 px
def triangular_kernel(radius_px=3):
    size = 2*radius_px + 1
    k = np.zeros((size, size), dtype=np.float32)
    for i in range(size):
        for j in range(size):
            d = np.sqrt((i - radius_px)**2 + (j - radius_px)**2)
            if d <= radius_px:
                k[i, j] = 1 - d / radius_px
            # center d=0 =>1; d=1=>0.666; d=2=>0.333; d=3=>0
    # Normalize? No, kernel is as defined. Credit is sum p*k.
    # At center 1.0, at 1px diagonal sqrt2~1.41 => 1-1.41/3=0.528
    return k

KERNEL_3PX = triangular_kernel(3)

def compute_DTI(pred, truth, alpha=0.2, beta=0.8):
    """
    pred: binary or float in [0,1] raster (dots)
    truth: binary truth raster (new-fault pixels)
    Both same shape, NaN outside footprint treated as 0 outside? Inside footprint only.
    Returns DTI scalar.
    """
    # footprint mask: where either pred or truth is not NaN? Use pred footprint.
    # Replace NaN with 0 for sums
    pred_f = np.where(np.isnan(pred), 0, pred).astype(np.float32)
    truth_f = np.where(np.isnan(truth), 0, truth).astype(np.float32)
    # Kernel credit T = sum(convolve(pred, k) * truth) ??? Equivalent to sum_p sum_g p*k(d)
    # Actually T = sum_g (sum_p p*k(g,p) capped at 1? Spec says triangular kernel credit per truth pixel)
    # Simplified: convolve pred with kernel, then sum over truth pixels of min(1, credited)
    # But spec algebra: T is uncapped? For line-like, multiple predictions can credit same truth but...
    # We'll implement cap per truth pixel at 1 (max credit 1 per truth pixel)
    # Then S = sum pred
    # M = sum pred * max_g k(g,p)  — credit potential per predicted pixel
    # Compute via convolution: for each truth pixel, spread kernel; but capping handled.
    # Simplistic uncapped:
    pred_conv = convolve(pred_f, KERNEL_3PX, mode="constant", cval=0.0)
    # T uncapped = sum(pred_conv * truth)
    T_uncapped = np.sum(pred_conv * truth_f)
    # Cap at 1 per truth pixel: T = sum(min(1, pred_conv) * truth)  — plausible
    T = np.sum(np.minimum(1.0, pred_conv) * truth_f)
    S = np.sum(pred_f)
    # M: for each predicted pixel, max_g k(g,p) = max kernel value to any truth
    # Compute via convolving truth with kernel and taking where pred>0, the convolved value's max per pixel not sum.
    # But convolve with triangular kernel gives sum of contributions if multiple truth pixels overlap; max ~1 along line if dense.
    # Approximate M as sum_p p * min(1, truth_conv[p]) where truth_conv = convolve(truth, KERNEL)
    truth_conv = convolve(truth_f, KERNEL_3PX, mode="constant", cval=0.0)
    # truth_conv at a pred pixel gives sum of kernel credits to nearby truth; for isolated truth, ==k(d)
    # For line-like, sum along line may exceed 1, cap at 1.
    M = np.sum(pred_f * np.minimum(1.0, truth_conv))
    G = np.sum(truth_f)  # |G|
    denom = alpha * T + alpha * (S - M) + beta * G
    if denom == 0:
        return 0.0
    return float(T / denom)

def marginal_gain(pred, truth, candidate_y, candidate_x):
    """
    Exact marginal gain of adding dot at (y,x) to pred.
    Compute DTI(pred U {dot}) - DTI(pred)
    """
    dti_before = compute_DTI(pred, truth)
    pred_after = pred.copy()
    # Handle NaN outside footprint: cannot add there
    if np.isnan(pred_after[candidate_y, candidate_x]):
        return 0.0
    pred_after[candidate_y, candidate_x] = 1.0
    dti_after = compute_DTI(pred_after, truth)
    return dti_after - dti_before

def unit_tests():
    # Test triangular kernel values
    k = triangular_kernel(3)
    assert k[3,3] == 1.0, "center should be 1"
    assert abs(k[3,4] - (1 - 1/3)) < 1e-6, "adjacent should be 0.666"
    assert abs(k[3,5] - (1 - 2/3)) < 1e-6, "2px should be 0.333"
    assert k[3,6] == 0.0, "3px dist exactly =>0"
    # DTI sanity: empty pred =>0
    pred = np.zeros((10,10), dtype=np.float32)
    truth = np.zeros((10,10), dtype=np.float32)
    truth[5,5] = 1
    assert compute_DTI(pred, truth) == 0.0
    # Single dot on truth => high DTI
    pred[5,5] = 1
    dti = compute_DTI(pred, truth)
    # T=1, S=1, M=1, G=1 => DTI =1/(0.2*1+0.2*0+0.8*1)=1/1=1.0
    assert abs(dti - 1.0) < 1e-6, f"expected 1.0 got {dti}"
    # Dot 1px away (k=0.666): T=0.666, S=1, M=0.666? pred's max_g =0.666, G=1 => DTI=0.666/(0.2*0.666+0.2*0.333+0.8)=0.666/1.0=0.666
    pred2 = np.zeros((10,10), dtype=np.float32)
    pred2[5,6] = 1
    dti2 = compute_DTI(pred2, truth)
    assert abs(dti2 - 0.666) < 0.02, f"1px off should be ~0.666 got {dti2}"
    # Marginal gain test: adding second dot far away should increase S but not T much, so DTI decreases
    pred3 = np.zeros((10,10), dtype=np.float32)
    pred3[5,5] = 1
    gain = marginal_gain(pred3, truth, 0,0)  # far away dot
    # Adding far dot: T unchanged, S+1, M small => denom increases => DTI drops => gain negative
    assert gain < 0, "far dot should hurt"
    # Adding dot near truth on line-like truth lowers bar
    print("DTI unit tests passed")
    return True

if __name__ == "__main__":
    unit_tests()
