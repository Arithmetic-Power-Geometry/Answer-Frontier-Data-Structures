from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from afds.shortest_path import answer_frontier, enumerate_simple_paths, pairwise_transition_radius, global_transition_radius, path_length

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
OUT.mkdir(exist_ok=True)
SEED = 20260926

def make_graph(n: int, edge_prob: float, max_w: int, rng: random.Random) -> nx.Graph:
    g = nx.Graph()
    g.add_nodes_from(range(n))
    for i in range(n - 1):
        g.add_edge(i, i + 1, weight=rng.randint(1, max_w))
    for i in range(n):
        for j in range(i + 2, n):
            if rng.random() < edge_prob:
                g.add_edge(i, j, weight=rng.randint(1, max_w))
    return g

def path_key(path):
    return "-".join(map(str, path))

def analyze_graph(g: nx.Graph, graph_id: int, source: int, target: int) -> Tuple[Dict, List[Dict]]:
    paths = enumerate_simple_paths(g, source, target, cutoff=len(g.nodes) - 1)
    if len(paths) < 3:
        return {}, []
    lengths = [path_length(g, p) for p in paths]
    if abs(lengths[0] - lengths[1]) < 1e-10:
        return {}, []
    p0 = paths[0]
    rows = []
    for rank, p in enumerate(paths[1:], start=2):
        if path_length(g, p) <= lengths[0] + 1e-10:
            continue
        pr = pairwise_transition_radius(g, p0, p)
        gr, witness = global_transition_radius(g, paths, p)
        rows.append({
            "graph_id": graph_id,
            "path_rank_by_length": rank,
            "current_path": path_key(p0),
            "alternative_path": path_key(p),
            "current_length": lengths[0],
            "alternative_length": path_length(g, p),
            "length_gap": path_length(g, p) - lengths[0],
            "pairwise_radius": pr,
            "global_radius": gr,
            "pairwise_global_gap": gr - pr,
            "witness_nonzero_edges": len(witness),
        })
    if not rows:
        return {}, []
    ordered_global = sorted(rows, key=lambda r: (r["global_radius"], r["alternative_length"], r["alternative_path"]))
    nearest = ordered_global[0]
    second_shortest = min(rows, key=lambda r: (r["alternative_length"], r["alternative_path"]))
    summary = {
        "graph_id": graph_id,
        "n": g.number_of_nodes(),
        "m": g.number_of_edges(),
        "num_simple_paths": len(paths),
        "current_path": path_key(p0),
        "current_length": lengths[0],
        "second_shortest_path": second_shortest["alternative_path"],
        "nearest_transition_path": nearest["alternative_path"],
        "length_transition_separation": second_shortest["alternative_path"] != nearest["alternative_path"],
        "pairwise_global_separation": any(r["pairwise_global_gap"] > 1e-8 for r in rows),
    }
    return summary, rows

def find_answer_silent_frontier_change(g: nx.Graph, source: int, target: int):
    try:
        before_path, before_frontier = answer_frontier(g, source, target, k=3, cutoff=len(g.nodes)-1)
    except Exception:
        return None
    if not before_frontier:
        return None
    before_sig = [(x.path, round(x.global_radius, 9)) for x in before_frontier]
    for u, v, data in list(g.edges(data=True)):
        old = data["weight"]
        for delta in (-2, -1, 1, 2):
            nw = old + delta
            if nw <= 0:
                continue
            h = g.copy()
            h[u][v]["weight"] = nw
            try:
                after_path, after_frontier = answer_frontier(h, source, target, k=3, cutoff=len(h.nodes)-1)
            except Exception:
                continue
            if tuple(after_path) != tuple(before_path):
                continue
            after_sig = [(x.path, round(x.global_radius, 9)) for x in after_frontier]
            if after_sig != before_sig:
                return {
                    "edge": f"{u}-{v}",
                    "old_weight": old,
                    "new_weight": nw,
                    "current_path": path_key(before_path),
                    "before_frontier": [(path_key(p), r) for p, r in before_sig],
                    "after_frontier": [(path_key(p), r) for p, r in after_sig],
                }
    return None

def main():
    rng = random.Random(SEED)
    graph_summaries, path_rows, silent_examples = [], [], []
    total_candidates = 180
    accepted = 0
    for gid in range(total_candidates):
        n = rng.choice([5, 6, 7])
        p = rng.choice([0.30, 0.40, 0.50, 0.60])
        g = make_graph(n, p, 9, rng)
        summary, rows = analyze_graph(g, gid, 0, n - 1)
        if not summary:
            continue
        accepted += 1
        graph_summaries.append(summary)
        path_rows.extend(rows)
        if len(silent_examples) < 12:
            ex = find_answer_silent_frontier_change(g, 0, n - 1)
            if ex is not None:
                ex["graph_id"] = gid
                silent_examples.append(ex)

    graphs = pd.DataFrame(graph_summaries)
    paths = pd.DataFrame(path_rows)
    graphs.to_csv(OUT / "graph_summary.csv", index=False)
    paths.to_csv(OUT / "path_frontiers.csv", index=False)
    pd.DataFrame(silent_examples).to_json(OUT / "answer_silent_frontier_changes.json", orient="records", indent=2)

    if len(paths):
        cmp = paths[["graph_id","path_rank_by_length","alternative_length","pairwise_radius","global_radius","alternative_path"]].copy()
        cmp.sort_values(["graph_id","global_radius","alternative_length"]).to_csv(OUT / "frontier_comparison.csv", index=False)

        plt.figure(figsize=(7,5))
        plt.scatter(paths["pairwise_radius"], paths["global_radius"], alpha=0.55)
        maxv = max(float(paths["pairwise_radius"].max()), float(paths["global_radius"].max()))
        plt.plot([0, maxv], [0, maxv])
        plt.xlabel("Pairwise transition radius")
        plt.ylabel("Global-optimality transition radius")
        plt.title("Pairwise vs global answer-frontier radius")
        plt.tight_layout()
        plt.savefig(OUT / "fig_pairwise_vs_global.png", dpi=180)
        plt.close()

        nearest_rows = paths.sort_values(["graph_id","global_radius"]).groupby("graph_id").first().reset_index()
        plt.figure(figsize=(7,5))
        plt.hist(nearest_rows["global_radius"], bins=min(20, max(5, len(nearest_rows)//4)))
        plt.xlabel("Nearest global transition radius")
        plt.ylabel("Graphs")
        plt.title("Distribution of nearest answer transitions")
        plt.tight_layout()
        plt.savefig(OUT / "fig_nearest_transition_distribution.png", dpi=180)
        plt.close()

    metrics = {
        "seed": SEED,
        "candidate_graphs": total_candidates,
        "accepted_unique_shortest_graphs": accepted,
        "graphs_with_length_transition_separation": int(graphs["length_transition_separation"].sum()) if len(graphs) else 0,
        "graphs_with_pairwise_global_separation": int(graphs["pairwise_global_separation"].sum()) if len(graphs) else 0,
        "answer_silent_frontier_change_examples": len(silent_examples),
        "path_alternatives_evaluated": len(paths),
    }
    (OUT / "summary.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    report = ["# AFDS Evidence Report", "", "This report is generated deterministically by scripts/run_experiments.py.", "", "## Summary", "", "| Metric | Value |", "|---|---:|"]
    for k, v in metrics.items():
        report.append(f"| {k} | {v} |")
    report += ["", "## Interpretation", "",
               "- length_transition_separation shows ordinary path-length order can differ from minimum-intervention order.",
               "- pairwise_global_separation shows beating the current answer can underestimate the intervention needed for global optimality.",
               "- answer_silent_frontier_change_examples records updates that keep the shortest path unchanged while the frontier changes.",
               "", "These experiments establish separations inside the formal model; they do not by themselves prove literature-level novelty."]
    (OUT / "REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
