import networkx as nx
from afds.shortest_path import enumerate_simple_paths, frontier_certificate, canonical_edge
from afds.frontier_screen import fixed_witness_safe_interval, fixed_witness_remains_feasible

def test_counterexample_is_rejected_by_full_slack_screen():
    g=nx.Graph();g.add_weighted_edges_from([(0,1,1),(0,2,1),(0,3,1),(1,2,3),(1,3,2)])
    paths=enumerate_simple_paths(g,0,3); target=(0,2,1,3)
    c=frontier_certificate(g,paths,target)
    e=canonical_edge(0,1)
    lo,hi=fixed_witness_safe_interval(g,paths,target,c["witness"],e)
    assert not fixed_witness_remains_feasible(g,paths,target,c["witness"],e,-1)
