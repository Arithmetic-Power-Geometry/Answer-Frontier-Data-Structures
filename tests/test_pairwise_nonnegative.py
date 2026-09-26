import math, random
import networkx as nx
import numpy as np
from scipy.optimize import linprog
from afds.shortest_path import pairwise_transition_radius, path_edges, path_length, canonical_edge

def lp_pairwise(g,p0,p1):
    edges=sorted(canonical_edge(u,v) for u,v in g.edges()); m=len(edges)
    base=np.array([g[u][v]["weight"] for u,v in edges],float)
    a=set(path_edges(p0)); b=set(path_edges(p1))
    coeff=np.array([(1 if e in b else 0)-(1 if e in a else 0) for e in edges],float)
    # gap + coeff.delta <= 0
    gap=path_length(g,p1)-path_length(g,p0)
    A=[]; rhs=[]
    for j in range(m):
        row=np.zeros(m+1);row[j]=1;row[-1]=-1;A.append(row);rhs.append(0)
        row=np.zeros(m+1);row[j]=-1;row[-1]=-1;A.append(row);rhs.append(0)
    row=np.zeros(m+1);row[:m]=coeff;A.append(row);rhs.append(-gap)
    c=np.zeros(m+1);c[-1]=1
    res=linprog(c,A_ub=np.array(A),b_ub=np.array(rhs),
                bounds=[(-w,None) for w in base]+[(0,None)],method="highs")
    return math.inf if not res.success else float(res.x[-1])

def test_saturation_breakpoint_changes_old_formula():
    g=nx.Graph()
    # current length 2; alternative length 5. Alternative-only weights 1 and 4.
    g.add_weighted_edges_from([(0,1,1),(1,3,1),(0,2,1),(2,3,4)])
    p0=(0,1,3);p1=(0,2,3)
    # old unconstrained formula = 3/4; zero floor saturates edge (0,2),
    # so exact radius is 1.
    assert abs(pairwise_transition_radius(g,p0,p1)-1.0)<1e-9
    assert abs(lp_pairwise(g,p0,p1)-1.0)<1e-9

def test_pairwise_matches_independent_lp_random_small():
    rng=random.Random(20260926)
    checked=0
    for _ in range(80):
        g=nx.Graph();g.add_nodes_from(range(5))
        for i in range(4):g.add_edge(i,i+1,weight=rng.randint(1,7))
        for i in range(5):
            for j in range(i+2,5):
                if rng.random()<.35:g.add_edge(i,j,weight=rng.randint(1,7))
        paths=list(nx.all_simple_paths(g,0,4,cutoff=4))
        paths.sort(key=lambda p:(path_length(g,p),tuple(p)))
        if len(paths)<2:continue
        p0=tuple(paths[0])
        for p in paths[1:min(5,len(paths))]:
            p=tuple(p)
            if path_length(g,p)<=path_length(g,p0)+1e-10:continue
            x=pairwise_transition_radius(g,p0,p); y=lp_pairwise(g,p0,p)
            if math.isinf(x) or math.isinf(y):assert math.isinf(x) and math.isinf(y)
            else:assert abs(x-y)<1e-7
            checked+=1
    assert checked>=50
