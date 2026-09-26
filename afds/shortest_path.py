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
    l0 = path_length(graph, current)
    lp = path_length(graph, alternative)
    gap = lp - l0
    if gap <= 0:
        return 0.0
    diff = set(path_edges(current)).symmetric_difference(path_edges(alternative))
    if not diff:
        return math.inf
    return gap / len(diff)

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
