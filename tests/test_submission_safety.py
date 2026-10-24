import numpy as np
import pytest
from src.uniqueness import compare
from src.validate import validate
from test_prune_and_validate import make_tif

@pytest.mark.parametrize('value', [np.inf, -np.inf, np.nan, -0.001, 1.001])
def test_invalid_values(tmp_path, value):
    a = np.zeros((5, 5)); a[2, 2] = value
    assert not validate(make_tif(tmp_path/'a.tif', a), make_tif(tmp_path/'s.tif', np.zeros((5,5))))['pass']

def test_registry_duplicate_and_unknown():
    a = np.arange(100).reshape(10,10); d = a % 9 == 0; m = np.ones_like(d)
    assert compare(a,d,a,d,m)['duplicate']
    assert not compare(a*0,d,a,d,m)['pass']
    assert not compare(a,d*0,-a,d,m)['pass']

def test_registry_distinct():
    a = np.arange(400).reshape(20,20); d = a == 0; r = a == 399
    assert compare(a,d,-a,r,np.ones_like(d))['pass']

def test_shape_mismatch():
    with pytest.raises(ValueError):
        compare(np.zeros((2,2)),np.zeros((3,3)),np.zeros((2,2)),np.zeros((2,2)),np.ones((2,2)))
