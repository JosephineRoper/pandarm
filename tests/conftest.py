import pathlib
import tempfile

import pytest


def pytest_configure(config):  # noqa: ARG001
    pytest.no_crs_warning = pytest.warns(UserWarning, match="No CRS was passed to geometry input")

    pytest.h5_osm_sample = pathlib.Path(__file__).parent / "osm_sample.h5"


@pytest.fixture
def tmpfile(request):
    fname = pathlib.Path(tempfile.NamedTemporaryFile().name)

    def cleanup():
        if fname.exists():
            fname.unlink()

    request.addfinalizer(cleanup)

    return fname
