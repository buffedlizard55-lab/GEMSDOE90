"""
GEMS DOE configuration — single source of truth for raster spec.
Verified against spec: EPSG:32611, 100m, float32, 1 band, values [0,1], NaN outside.
"""
import rasterio
from affine import Affine

# Raster geometry — footprint ~5.17M px
WIDTH = 2500
HEIGHT = 2068
# 100 m pixels, UTM zone 11N
TRANSFORM = Affine(100, 0, 400000,
                    0, -100, 4450000)
CRS = "EPSG:32611"
DTYPE = "float32"
NODATA = float("nan")  # spec: null/NaN outside footprint; fallback zeros variant separate

# Paths
SAMPLE_PATH = "data/sample_submission.tif"
PARENT_PATH = "releases/h33-h33-2-b2.tif"
PARENT_ZEROS_PATH = "releases/h33-h33-2-b2-zeros.tif"
CATALOGUE_PATH = "data/catalogue_mask.tif"
FOOTPRINT_PATH = "data/footprint_mask.tif"
SCORE_PATH = "data/score_field.tif"
RANKING_PATH = "data/ranking.npy"

# Parent spec
PARENT_NAME = "h33-h33-2-b2"
PARENT_N_DOTS = 37654
PARENT_CLAIM = 0.2778  # CLAIM until receipt
PARENT_BUFFER_PX = 2  # none within 2 px of catalogue

# DTI params
R_M = 300  # triangular kernel radius in meters
R_PX = 3   # = R_M / 100m
ALPHA = 0.2
BETA = 0.8

# Reproducibility
SEED = 20261022
GIT_SHA_LEN = 8

def get_profile():
    return {
        "driver": "GTiff",
        "dtype": DTYPE,
        "width": WIDTH,
        "height": HEIGHT,
        "count": 1,
        "crs": CRS,
        "transform": TRANSFORM,
        "nodata": None,  # we write NaN manually; rasterio nodata tag optional
        "tiled": False,
        "compress": "deflate",
    }

# Footprint synthetic params
FOOTPRINT_SEED = 2026

# Block priors for CONCENTRATION axis
BLOCK_SIZES_M = [1000, 2000, 5000]
