import pytest


def pytest_configure(config):  # noqa: ARG001

    pytest.no_crs_warning = pytest.warns(
        UserWarning, match="No CRS was passed to geometry input"
    )
