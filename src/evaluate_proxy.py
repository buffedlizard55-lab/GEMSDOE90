import rasterio, numpy as np, sys
sys.path.insert(0,".")
from src.dti import compute_DTI
from pathlib import Path

def evaluate(raster_path, truth_path="data/hidden_truth.tif"):
    with rasterio.open(raster_path) as src:
        pred = src.read(1)
    with rasterio.open(truth_path) as src:
        truth = src.read(1)
    # footprint is where pred is not NaN (or truth)
    # Replace NaN with 0 for DTI
    pred_f = np.where(np.isnan(pred), 0, pred)
    truth_f = np.where(np.isnan(truth), 0, truth)
    # truth_f is 1 at truth pixels, 0 elsewhere
    dti = compute_DTI(pred_f, truth_f)
    return dti

if __name__=="__main__":
    import glob
    paths = ["releases/h33-h33-2-b2.tif"] + sorted(glob.glob("releases/h33-h33-2-b2-CONC*.tif"))
    # filter out zeros
    paths = [p for p in paths if "zeros" not in p]
    for p in paths:
        dti = evaluate(p)
        print(f"{Path(p).name}: DTI proxy {dti:.4f}")
