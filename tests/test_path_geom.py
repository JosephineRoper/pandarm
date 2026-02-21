import pandarm.network as pdna

net = pdna.Network.from_hdf5("tests/uci_net.h5")
o_node = 3710893961
d_node = 6556054235

def test_shortest_path_multi_geom():
    geom = net.shortest_path_geoms([o_node], [d_node])

    assert (
        round(geom.union_all().length, 3)
        == 0.017
    )


def test_shortest_path_single_geom():
    geom = net.shortest_path_geometry(o_node, d_node)

    assert round(geom.union_all().length, 3) == 0.017
