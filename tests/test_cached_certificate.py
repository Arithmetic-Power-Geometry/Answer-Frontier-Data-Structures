import networkx as nx
from afds.shortest_path import (
    enumerate_simple_paths, global_transition_radius,
    global_transition_lp_certificate, cached_primal_dual_radius_certificate,
)
def test_cached_certificate_never_changes_certified_radius():
    g=nx.Graph()
    g.add_weighted_edges_from([(0,1,1),(0,2,1),(0,3,1),(1,2,3),(1,3,2)])
    ps=enumerate_simple_paths(g,0,3,cutoff=3); target=(0,2,1,3)
    old,_=global_transition_radius(g,ps,target)
    cert=global_transition_lp_certificate(g,ps,target)
    for u,v in g.edges():
        for d in (-1,1):
            if g[u][v]["weight"]+d<0: continue
            h=g.copy();h[u][v]["weight"]+=d
            if cached_primal_dual_radius_certificate(cert,h,ps,target):
                new,_=global_transition_radius(h,ps,target)
                assert abs(new-old)<1e-8
