import pandarm.network as pdna

net = pdna.Network.from_hdf5("tests/uci_net.h5")
print(net.nodes_df.sample(1).index)
print(net.nodes_df.sample(1).index)

o_node = 3710893961
d_node = 6556054235

def test_shortest_path_geom():
    geom = net.shortest_path_geoms([o_node], [d_node])

    assert (
        round(geom.union_all().length, 3)
        == 0.017
    )
