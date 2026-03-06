#include "graphalg.h"
#include <math.h>
#include <cstdint>
#include <limits>

namespace MTC {
namespace accessibility {
Graphalg::Graphalg(
        int numnodes, vector< vector<int64_t> > edges, vector<double> edgeweights,
        bool twoway) {
    this->numnodes = numnodes;

    int num = omp_get_max_threads();

    FILE_LOG(logINFO) << "Generating contraction hierarchies with "
                      << num << " threads.\n";

    ch = CH::ContractionHierarchies(num);

    vector<CH::Node> nv;

    for (int i = 0 ; i < numnodes ; i++) {
        // CH allows you to pass in a node id, and an x and a y, and then
        // never uses it - to be clear, we don't pass it in anymore
        CH::Node n(i, 0, 0);
        nv.push_back(n);
    }

    FILE_LOG(logINFO) << "Setting CH node vector of size "
                      << nv.size() << "\n";

    ch.SetNodeVector(nv);

    vector<CH::Edge> ev;

    for (int i = 0 ; i < edges.size() ; i++) {
        CH::Edge e(edges[i][0], edges[i][1], i,
            edgeweights[i]*DISTANCEMULTFACT, true, twoway);
        ev.push_back(e);
    }

    FILE_LOG(logINFO) << "Setting CH edge vector of size "
                      << ev.size() << "\n";

    ch.SetEdgeVector(ev);
    ch.RunPreprocessing();
}


std::vector<NodeID> Graphalg::Route(int src, int tgt, int threadNum) {
    std::vector<NodeID> ResultingPath;

    CH::Node src_node(src, 0, 0);
    CH::Node tgt_node(tgt, 0, 0);

    ch.computeShortestPath(
        src_node,
        tgt_node,
        ResultingPath,
        threadNum);

    return ResultingPath;
}


double Graphalg::Distance(int src, int tgt, int threadNum) {
    CH::Node src_node(src, 0, 0);
    CH::Node tgt_node(tgt, 0, 0);

    unsigned int length = ch.computeLengthofShortestPath(
        src_node,
        tgt_node,
        threadNum);

    return static_cast<double>(length) / static_cast<double>(DISTANCEMULTFACT);
}


void Graphalg::Range(int src, double maxdist, int threadNum,
                     DistanceVec &ResultingNodes) {
    CH::Node src_node(src, 0, 0);

    std::vector<std::pair<NodeID, unsigned> > tmp;

    ch.computeReachableNodesWithin(
        src_node,
        maxdist*DISTANCEMULTFACT,
        tmp,
        threadNum);

    for (int i = 0 ; i < tmp.size() ; i++) {
        std::pair<NodeID, float> node;
        node.first = tmp[i].first;
        node.second = tmp[i].second/DISTANCEMULTFACT;
        ResultingNodes.push_back(node);
    }
}


DistanceVec
Graphalg::KNearest(int src, int k, double max_radius, int threadNum) {
    // When max_radius <= 0 (unlimited), use iterative radius doubling so we
    // only traverse a small local neighbourhood rather than the whole network.
    // Start at 500 m and double until k non-self neighbours are found or the
    // safe overflow cap (4 000 km) is reached.
    const double UNLIMITED_CAP = 4000000.0;
    const double INITIAL_RADIUS = 500.0;

    auto collect = [&](double radius) -> DistanceVec {
        DistanceVec nodes;
        Range(src, radius, threadNum, nodes);
        // Remove source node (distance == 0)
        nodes.erase(
            std::remove_if(nodes.begin(), nodes.end(),
                           [src](const std::pair<NodeID, float> &p) {
                               return static_cast<int>(p.first) == src;
                           }),
            nodes.end());
        return nodes;
    };

    DistanceVec all_nodes;
    if (max_radius <= 0.0) {
        double r = INITIAL_RADIUS;
        while (r <= UNLIMITED_CAP) {
            all_nodes = collect(r);
            if (static_cast<int>(all_nodes.size()) >= k) break;
            if (r >= UNLIMITED_CAP) break;
            r = std::min(r * 2.0, UNLIMITED_CAP);
        }
    } else {
        all_nodes = collect(max_radius);
    }

    // Partial sort: only fully sort the first k elements — O(n log k) vs O(n log n)
    int take = std::min(k, static_cast<int>(all_nodes.size()));
    std::partial_sort(all_nodes.begin(), all_nodes.begin() + take, all_nodes.end(),
                      [](const std::pair<NodeID, float> &a,
                         const std::pair<NodeID, float> &b) {
                          return a.second < b.second;
                      });
    all_nodes.resize(take);

    return all_nodes;
}


DistanceMap
Graphalg::NearestPOI(const POIKeyType &category, int src, double maxdist, int number,
                     int threadNum) {
    DistanceMap dm;

    std::vector<CH::BucketEntry> ResultingNodes;
    ch.getNearestWithUpperBoundOnDistanceAndLocations(
        category,
        src,
        maxdist*DISTANCEMULTFACT,
        number,
        ResultingNodes,
        threadNum);

    for (int i = 0 ; i < ResultingNodes.size() ; i++) {
        dm[ResultingNodes[i].node] =
            static_cast<float>(ResultingNodes[i].distance) /
            static_cast<float>(DISTANCEMULTFACT);
    }

    return dm;
}
}  // namespace accessibility
}  // namespace MTC
