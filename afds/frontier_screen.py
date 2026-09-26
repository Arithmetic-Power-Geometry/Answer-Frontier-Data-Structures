"""Exact safe fixed-witness screening bound for one-edge graph updates.

This does NOT claim the LP optimum is unchanged. It certifies only that the
stored optimal witness remains feasible against every competitor after a
single base-weight update. Exact optimum preservation still requires a lower
bound / dual certificate.
"""
from __future__ import annotations
import math
from afds.shortest_path import path_edges, path_length

def fixed_witness_safe_interval(graph, all_paths, target, witness, edge):
    """Return (negative_limit, positive_limit) for base-weight change eta.

    For each competitor Q, at the stored witness the slack is
      s_Q = L_w(Q)-L_w(P) >= 0.
    A base update eta on edge e changes this slack by
      eta * (1[e in Q]-1[e in P]).
    Intersect all half-lines preserving s_Q >= 0.
    """
    pe=set(path_edges(target))
    def adjlen(p):
        return path_length(graph,p)+sum(witness.get(e,0.0) for e in path_edges(p))
    tp=adjlen(target)
    lo=-math.inf; hi=math.inf
    for q in all_paths:
        if tuple(q)==tuple(target): continue
        slack=adjlen(q)-tp
        coeff=(1 if edge in set(path_edges(q)) else 0)-(1 if edge in pe else 0)
        if coeff>0: lo=max(lo,-slack/coeff)
        elif coeff<0: hi=min(hi,slack/(-coeff))
    return lo,hi

def fixed_witness_remains_feasible(graph, all_paths, target, witness, edge, eta, tol=1e-10):
    lo,hi=fixed_witness_safe_interval(graph,all_paths,target,witness,edge)
    return eta>=lo-tol and eta<=hi+tol
