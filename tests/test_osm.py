import numpy as np
import osmnx as ox
import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

import pandarm as pdna


@pytest.fixture(scope="module")
def osm_network():
    irvine = ox.geocode_to_gdf("irvine, ca")
    with pytest.warns(UserWarning, match="Geometry is in a geographic CRS"):
        network = pdna.Network.from_gdf(irvine)
    return network


def test_osm_network_download(osm_network):
    # this is a liberal test because the network can evolve over time
    assert osm_network.nodes_df.shape[0] >= 42691

    assert_array_equal(np.array(["x", "y", "geometry"]), osm_network.nodes_df.columns)
    assert_array_equal(np.array(["from", "to", "length", "geometry"]), osm_network.edges_df.columns)


def test_save_hdf_with_geoms(osm_network, tmpfile):
    osm_network.save_hdf5(tmpfile)

    with pd.HDFStore(tmpfile) as store:
        assert store["nodes"].shape[0] >= 42691

    with pytest.no_crs_warning:
        roundtrip_net = pdna.Network.from_hdf5(tmpfile)

    assert_frame_equal(osm_network.nodes_df, roundtrip_net.nodes_df)
