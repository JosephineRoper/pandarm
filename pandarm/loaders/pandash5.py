import geopandas as gpd
import pandas as pd
import shapely


def remove_nodes(network, rm_nodes):
    """
    Create DataFrames of nodes and edges that do not include specified nodes.

    Parameters
    ----------
    network : pandarm.Network
    rm_nodes : array_like
        A list, array, Index, or Series of node IDs that should *not*
        be saved as part of the Network.

    Returns
    -------
    nodes, edges : pandas.DataFrame

    """
    rm_nodes = set(rm_nodes)
    ndf = network.nodes_df
    edf = network.edges_df

    nodes_to_keep = ~ndf.index.isin(rm_nodes)
    edges_to_keep = ~(edf["from"].isin(rm_nodes) | edf["to"].isin(rm_nodes))

    return ndf.loc[nodes_to_keep], edf.loc[edges_to_keep]


def network_to_pandas_hdf5(network, filename, rm_nodes=None, complevel=None, complib=None):
    """
    Save a Network's data to a Pandas HDFStore.

    Parameters
    ----------
    network : pandarm.Network
    filename : str
    rm_nodes : array_like
        A list, array, Index, or Series of node IDs that should *not*
        be saved as part of the Network.

    """
    if rm_nodes is not None:
        nodes, edges = remove_nodes(network, rm_nodes)
    else:
        nodes, edges = network.nodes_df, network.edges_df

    with pd.HDFStore(filename, mode="w", complevel=complevel, complib=complib) as store:
        store["nodes"] = nodes.drop(columns="geometry")

        if isinstance(edges, gpd.GeoDataFrame):
            store["edges"] = edges.drop(columns="geometry")

            # use native encoding for better compression
            ragged = shapely.to_ragged_array(network.edges_df.geometry)
            store["edges_geom_type"] = pd.Series([str(ragged[0])])
            store["edges_coords"] = pd.DataFrame(ragged[1])
            store["edges_offsets"] = pd.Series(ragged[2][0])
        else:
            store["edges"] = edges

        store["two_way"] = pd.Series([network._twoway])
        store["impedance_names"] = pd.Series(network.impedance_names)
        store["crs"] = pd.Series([network.crs])


def network_from_pandas_hdf5(cls, filename):
    """
    Build a Network from data in a Pandas HDFStore.

    Parameters
    ----------
    cls : class
        Class to instantiate, usually pandana.Network.
    filename : str

    Returns
    -------
    network : pandarm.Network

    """
    with pd.HDFStore(filename) as store:
        nodes = store["nodes"]
        edges = store["edges"]
        crs = store["crs"].values[0] if "crs" in store.keys() else None
        if "edges_geom_type" in store:
            geometry = shapely.from_ragged_array(
                shapely.GeometryType(int(store["edges_geom_type"].item())),
                store["edges_coords"].values,
                (store["edges_offsets"].values,),
            )
            edges = gpd.GeoDataFrame(edges, geometry=geometry, crs=crs)
            edge_geom = "geometry"
        two_way = store["two_way"][0]
        imp_names = store["impedance_names"].tolist()
        edge_geom = edges.geometry if "geometry" in edges.columns.values else None

    return cls(
        nodes["x"],
        nodes["y"],
        edges["from"],
        edges["to"],
        edges[imp_names],
        twoway=two_way,
        edge_geom=edge_geom,
        crs=crs,
    )
