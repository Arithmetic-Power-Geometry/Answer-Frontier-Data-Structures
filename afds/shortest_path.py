"""Exact small-graph AFDS shortest-path laboratory."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple
import math
import networkx as nx
import numpy as np
from scipy.optimize import linprog

Edge = Tuple[int, int]
Path = Tuple[int, ...]

@dataclass(frozen=True)
class FrontierEntry:
    path: Path
    original_length: float
    pairwise_radius: float
    global_radius: float
    witness: Dict[Edge, float]

def canonical_edge(u: int, v: int) -> Edge:
    return (u, v) if u <= v else (v, u)

def path_edges(path: Sequence[int]) -> Tuple[Edge, ...]:
    return tuple(canonical_edge(path[i], path[i + 1]) for i in range(len(path) - 1))

def path_length(graph: nx.Graph, path: Sequence[int]) -> float:
    return float(sum(graph[u][v]["weight"] for u, v in zip(path[:-1], path[1:])))

def enumerate_simple_paths(graph: nx.Graph, source: int, target: int, cutoff: int | None = None) -> List[Path]:
    paths = [tuple(p) for p in nx.all_simple_paths(graph, source, target, cutoff=cutoff)]
    paths.sort(key=lambda p: (path_length(graph, p), p))
    return paths

def pairwise_transition_radius(graph: nx.Graph, current: Sequence[int], alternative: Sequence[int]) -> float:
    """Exact pairwise tie radius with nonnegative perturbed edge weights.

    Under |delta_e| <= epsilon, edges used only by current can be increased
    by epsilon without a state-space bound, while edges used only by the
    alternative can be decreased by at most min(epsilon, w_e).  Hence the
    maximum reducible path-length gap is

        |A| epsilon + sum_{e in B} min(epsilon, w_e),

    where A=current\\alternative and B=alternative\\current.
    """
    gap = path_length(graph, alternative) - path_length(graph, current)
    if gap <= 0:
        return 0.0
    ce=set(path_edges(current)); ae=set(path_edges(alternative))
    a=ce-ae; b=ae-ce
    if not a and not b:
        return math.inf

    # Monotone piecewise-linear water filling.  Binary search is robust at
    # breakpoints and also handles A=empty, where feasibility can fail.
    def reduction(eps: float) -> float:
        return len(a)*eps + sum(min(eps, float(graph[u][v]["weight"])) for u,v in b)

    if not a:
        cap=sum(float(graph[u][v]["weight"]) for u,v in b)
        if cap + 1e-12 < gap:
            return math.inf
        hi=max([float(graph[u][v]["weight"]) for u,v in b], default=0.0)
    else:
        hi=max(1.0, gap/max(1,len(a)))
        while reduction(hi) < gap:
            hi*=2.0
    lo=0.0
    for _ in range(80):
        mid=(lo+hi)/2.0
        if reduction(mid)>=gap: hi=mid
        else: lo=mid
    return hi

def _incidence(path: Sequence[int], edges: Sequence[Edge]) -> np.ndarray:
    pe = set(path_edges(path))
    return np.array([1.0 if e in pe else 0.0 for e in edges], dtype=float)

def global_transition_radius(graph: nx.Graph, all_paths: Sequence[Path], target_path: Sequence[int]):
    edges = sorted(canonical_edge(u, v) for u, v in graph.edges())
    m = len(edges)
    base = np.array([graph[u][v]["weight"] for u, v in edges], dtype=float)
    target_inc = _incidence(target_path, edges)
    c = np.zeros(m + 1)
    c[-1] = 1.0
    A_ub, b_ub = [], []
    for j in range(m):
        row = np.zeros(m + 1); row[j] = 1.0; row[-1] = -1.0
        A_ub.append(row); b_ub.append(0.0)
        row = np.zeros(m + 1); row[j] = -1.0; row[-1] = -1.0
        A_ub.append(row); b_ub.append(0.0)
    for other in all_paths:
        if tuple(other) == tuple(target_path):
            continue
        coeff = target_inc - _incidence(other, edges)
        row = np.zeros(m + 1); row[:m] = coeff
        A_ub.append(row)
        b_ub.append(-float(coeff @ base))
    # Preserve the admissible shortest-path state space: perturbed edge
    # weights must remain nonnegative, i.e. delta_e >= -w_e.
    bounds = [(-float(w), None) for w in base] + [(0.0, None)]
    result = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub),
                     bounds=bounds, method="highs")
    if not result.success:
        return math.inf, {}
    epsilon = float(result.x[-1])
    witness = {edge: float(delta) for edge, delta in zip(edges, result.x[:m]) if abs(delta) > 1e-10}
    return epsilon, witness


def global_transition_lp_certificate(graph: nx.Graph, all_paths: Sequence[Path], target_path: Sequence[int]):
    """Expose primal/dual HiGHS data for AFDS optimality-certificate research.

    This is diagnostic infrastructure, not yet a dynamic reuse theorem.
    """
    edges = sorted(canonical_edge(u, v) for u, v in graph.edges())
    m = len(edges)
    base = np.array([graph[u][v]["weight"] for u, v in edges], dtype=float)
    target_inc = _incidence(target_path, edges)
    c = np.zeros(m + 1); c[-1] = 1.0
    A_ub, b_ub, labels = [], [], []
    for j, edge in enumerate(edges):
        row=np.zeros(m+1); row[j]=1.0; row[-1]=-1.0
        A_ub.append(row); b_ub.append(0.0); labels.append(("upper_abs", edge))
        row=np.zeros(m+1); row[j]=-1.0; row[-1]=-1.0
        A_ub.append(row); b_ub.append(0.0); labels.append(("lower_abs", edge))
    for other in all_paths:
        if tuple(other)==tuple(target_path): continue
        coeff=target_inc-_incidence(other,edges)
        row=np.zeros(m+1); row[:m]=coeff
        A_ub.append(row); b_ub.append(-float(coeff@base)); labels.append(("path",tuple(other)))
    bounds=[(-float(w),None) for w in base]+[(0.0,None)]
    result=linprog(c,A_ub=np.array(A_ub),b_ub=np.array(b_ub),bounds=bounds,method="highs")
    if not result.success:
        return {"success":False,"message":result.message}
    return {
        "success":True,"radius":float(result.fun),"edges":edges,
        "primal":[float(x) for x in result.x],
        "inequality_residual":[float(x) for x in result.ineqlin.residual],
        "inequality_marginal":[float(x) for x in result.ineqlin.marginals],
        "inequality_labels":labels,
        "lower_residual":[float(x) for x in result.lower.residual],
        "lower_marginal":[float(x) for x in result.lower.marginals],
        "upper_residual":[float(x) for x in result.upper.residual],
        "upper_marginal":[float(x) for x in result.upper.marginals],
    }

def cached_primal_dual_radius_certificate(cert: dict, new_graph: nx.Graph,
                                         all_paths: Sequence[Path], target_path: Sequence[int],
                                         tol: float = 1e-8) -> bool:
    """Check a previously stored LP certificate without solving the old LP again."""
    if not cert.get("success"): return False
    edges=cert["edges"];m=len(edges);x=np.array(cert["primal"],float);eps=float(x[-1]);delta=x[:m]
    base=np.array([new_graph[u][v]["weight"] for u,v in edges],float)
    if np.any(base+delta < -tol) or np.any(np.abs(delta)>eps+tol):return False
    tinc=_incidence(target_path,edges)
    for other in all_paths:
        if tuple(other)==tuple(target_path):continue
        if float((tinc-_incidence(other,edges))@(base+delta))>tol:return False
    A=[];b=[]
    for j in range(m):
        row=np.zeros(m+1);row[j]=1;row[-1]=-1;A.append(row);b.append(0.)
        row=np.zeros(m+1);row[j]=-1;row[-1]=-1;A.append(row);b.append(0.)
    for other in all_paths:
        if tuple(other)==tuple(target_path):continue
        coeff=tinc-_incidence(other,edges);row=np.zeros(m+1);row[:m]=coeff
        A.append(row);b.append(-float(coeff@base))
    A=np.array(A);b=np.array(b);y=np.array(cert["inequality_marginal"],float);z=np.array(cert["lower_marginal"],float)
    cv=np.zeros(m+1);cv[-1]=1.
    if np.any(y>tol) or np.any(z < -tol):return False
    if np.max(np.abs(A.T@y+z-cv))>1e-7:return False
    lower=np.r_[-base,0.]
    return abs(float(b@y+lower@z)-eps)<=1e-7

def stored_primal_dual_radius_certificate(old_graph: nx.Graph, new_graph: nx.Graph,
                                          all_paths: Sequence[Path], target_path: Sequence[int],
                                          tol: float = 1e-8):
    """Conservative exact certificate that a stored AFDS radius is unchanged.

    Reuses the old optimal primal point and old HiGHS dual marginals.  It
    certifies only when (i) the old primal remains feasible for the updated LP
    and (ii) the old dual remains feasible and attains the same objective.
    Otherwise it returns False and the caller must re-solve.
    """
    cert=global_transition_lp_certificate(old_graph,all_paths,target_path)
    if not cert.get("success"): return False
    edges=cert["edges"]; m=len(edges); x=np.array(cert["primal"],float)
    eps=float(x[-1]); delta=x[:m]
    base=np.array([new_graph[u][v]["weight"] for u,v in edges],float)
    # primal: nonnegative adjusted weights and absolute-value envelope
    if np.any(base+delta < -tol) or np.any(np.abs(delta) > eps+tol): return False
    tinc=_incidence(target_path,edges)
    for other in all_paths:
        if tuple(other)==tuple(target_path): continue
        oinc=_incidence(other,edges)
        if float((tinc-oinc)@(base+delta)) > tol: return False

    # Rebuild updated LP.  A and c do not change for fixed topology/path set;
    # only path RHS values and variable lower bounds move with base weights.
    A=[]; b=[]
    for j in range(m):
        row=np.zeros(m+1);row[j]=1;row[-1]=-1;A.append(row);b.append(0.)
        row=np.zeros(m+1);row[j]=-1;row[-1]=-1;A.append(row);b.append(0.)
    for other in all_paths:
        if tuple(other)==tuple(target_path):continue
        coeff=tinc-_incidence(other,edges);row=np.zeros(m+1);row[:m]=coeff
        A.append(row);b.append(-float(coeff@base))
    A=np.array(A); b=np.array(b)
    y=np.array(cert["inequality_marginal"],float)
    z=np.array(cert["lower_marginal"],float)
    # SciPy minimization convention: y<=0 for A_ub x<=b, z>=0 for lower bounds.
    cvec=np.zeros(m+1);cvec[-1]=1.
    if np.any(y>tol) or np.any(z < -tol): return False
    # No finite upper variable bounds in this LP.
    if np.max(np.abs(A.T@y + z - cvec)) > 1e-7: return False
    lower=np.r_[-base,0.]
    dual_value=float(b@y + lower@z)
    return abs(dual_value-eps) <= 1e-7

def frontier_certificate(graph: nx.Graph, all_paths: Sequence[Path], target_path: Sequence[int],
                         tol: float = 1e-8):
    """Return exact LP radius plus active competitors and post-witness slacks.

    Active competitors are paths tied with the target at the optimum.
    This is evidence for deriving safe update certificates; no locality
    theorem is assumed here.
    """
    radius, witness = global_transition_radius(graph, all_paths, target_path)
    if not math.isfinite(radius):
        return {"radius": radius, "witness": witness, "active_competitors": [], "min_inactive_slack": math.inf}
    def adjusted_length(p):
        return path_length(graph, p) + sum(witness.get(e, 0.0) for e in path_edges(p))
    lt = adjusted_length(target_path)
    active=[]; inactive=[]
    for other in all_paths:
        if tuple(other)==tuple(target_path): continue
        slack=adjusted_length(other)-lt
        if abs(slack)<=tol: active.append(tuple(other))
        else: inactive.append(slack)
    return {
        "radius": radius,
        "witness": witness,
        "active_competitors": active,
        "min_inactive_slack": min(inactive) if inactive else math.inf,
    }

def answer_frontier(graph: nx.Graph, source: int, target: int, k: int = 5, cutoff: int | None = None):
    paths = enumerate_simple_paths(graph, source, target, cutoff=cutoff)
    if not paths:
        raise nx.NetworkXNoPath(f"No path from {source} to {target}")
    current = paths[0]
    current_len = path_length(graph, current)
    alternatives = [p for p in paths[1:] if path_length(graph, p) > current_len + 1e-10]
    entries = []
    for p in alternatives:
        pr = pairwise_transition_radius(graph, current, p)
        gr, witness = global_transition_radius(graph, paths, p)
        entries.append(FrontierEntry(p, path_length(graph, p), pr, gr, witness))
    entries.sort(key=lambda e: (e.global_radius, e.original_length, e.path))
    return current, entries[:k]
