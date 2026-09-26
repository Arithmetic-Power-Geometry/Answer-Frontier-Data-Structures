import networkx as nx
from afds.shortest_path import enumerate_simple_paths, pairwise_transition_radius, global_transition_radius, path_length

def test_pairwise_formula_simple_diamond():
    g = nx.Graph()
    g.add_edge(0,1,weight=1); g.add_edge(1,3,weight=1)
    g.add_edge(0,2,weight=2); g.add_edge(2,3,weight=2)
    paths = enumerate_simple_paths(g,0,3)
    p0, p1 = paths[0], paths[1]
    assert path_length(g,p0) == 2
    assert path_length(g,p1) == 4
    assert abs(pairwise_transition_radius(g,p0,p1) - 0.5) < 1e-9

def test_global_radius_at_least_pairwise():
    g = nx.Graph()
    for u,v,w in [(0,1,1),(1,4,1),(0,2,1),(2,3,1),(3,4,1),(0,3,3),(3,1,1)]:
        g.add_edge(u,v,weight=w)
    paths = enumerate_simple_paths(g,0,4)
    p0 = paths[0]
    for p in paths[1:]:
        if path_length(g,p) <= path_length(g,p0):
            continue
        pair = pairwise_transition_radius(g,p0,p)
        glob,_ = global_transition_radius(g,paths,p)
        assert glob + 1e-8 >= pair
