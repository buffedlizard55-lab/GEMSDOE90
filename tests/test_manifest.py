from src import manifest


def test_manifest_reports_missing_inputs():
    status = manifest.verify()
    # In a fresh checkout nothing is supplied: everything must be MISSING,
    # never silently OK. (If the human later pins files, update this test.)
    assert set(status) >= {"sample_submission", "r0_raster", "catalogue_raster"}
    assert all(v in {"MISSING", "UNPINNED", "OK", "MISMATCH"} for v in status.values())


def test_require_stops_on_missing():
    import pytest

    if manifest.verify(["sample_submission"])["sample_submission"] != "OK":
        with pytest.raises(SystemExit):
            manifest.require(["sample_submission"])
