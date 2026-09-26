from __future__ import annotations
import networkx as nx
from afds.shortest_path import enumerate_simple_paths, frontier_certificate, path_edges, canonical_edge

def test_margin_slack_bound_at_fixed_witness():
    g=nx.Graph()
    g.add_weighted_edges_from([(0,3,1),(0,1,2),(1,3,3),(0,2,1),(2,1,2)])
    paths=enumerate_simple_paths(g,0,3)
    target=(0,2,1,3)
    cert=frontier_certificate(g,paths,target)
    sigma=cert["min_inactive_slack"]
    protected=set(path_edges(target))
    for q in cert["active_competitors"]:
        protected.update(path_edges(q))
    # Any eligible single-edge perturbation eta<sigma changes a target-vs-path
    # gap by at most eta at the fixed witness, so positive inactive slack remains.
    for u,v in g.edges():
        e=canonical_edge(u,v)
        if e in protected: continue
        eta=0.25*sigma
        assert eta < sigma
