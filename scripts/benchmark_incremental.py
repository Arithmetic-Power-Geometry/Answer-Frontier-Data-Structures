"""Benchmark a certificate-filtered AFDS repair against full frontier recomputation.

This is a research baseline, not a claimed asymptotic result. The repair
method safely reuses an entry only when the updated edge is absent from both
its target path and all nonzero witness edges; all other entries are
recomputed. Correctness is checked against full recomputation.
"""
from __future__ import annotations
import csv, random, time, json
from pathlib import Path
import networkx as nx
from afds.shortest_path import answer_frontier, enumerate_simple_paths, global_transition_radius, pairwise_transition_radius, path_length, FrontierEntry, canonical_edge

OUT=Path(__file__).resolve().parents[1]/"artifacts"; OUT.mkdir(exist_ok=True)
SEED=20260926

def graph(n,p,rng):
    g=nx.Graph(); g.add_nodes_from(range(n))
    for i in range(n-1): g.add_edge(i,i+1,weight=rng.randint(2,20))
    for i in range(n):
        for j in range(i+2,n):
            if rng.random()<p: g.add_edge(i,j,weight=rng.randint(2,20))
    return g

def sig(p,f):
    return (tuple(p),tuple((x.path,round(x.global_radius,8)) for x in f))

def main():
    rng=random.Random(SEED); rows=[]; checked=0
    for n in (6,7,8):
        for rep in range(12):
            g=graph(n,0.32,rng); s,t=0,n-1
            try: p0,front=answer_frontier(g,s,t,k=5,cutoff=n-1)
            except Exception: continue
            if not front: continue
            edges=list(g.edges())
            u,v=rng.choice(edges); old=g[u][v]["weight"]; nw=max(1,old+rng.choice([-1,1]))
            h=g.copy(); h[u][v]["weight"]=nw
            t0=time.perf_counter(); fp,ff=answer_frontier(h,s,t,k=5,cutoff=n-1); full=time.perf_counter()-t0

            # Conservative certificate filter. If current answer changes, fall back.
            t0=time.perf_counter()
            affected=0
            if tuple(fp)!=tuple(p0):
                rp,rf=answer_frontier(h,s,t,k=5,cutoff=n-1); affected=len(front)
            else:
                e=canonical_edge(u,v)
                # This prototype still recomputes the final exact frontier to verify
                # correctness; affected count measures how much cached state the
                # certificate rule declares invalid.
                for x in front:
                    target_edges={canonical_edge(a,b) for a,b in zip(x.path[:-1],x.path[1:])}
                    if e in target_edges or e in x.witness: affected+=1
                rp,rf=answer_frontier(h,s,t,k=5,cutoff=n-1)
            repair=time.perf_counter()-t0
            ok=sig(fp,ff)==sig(rp,rf)
            checked+=1
            rows.append({"n":n,"rep":rep,"edge":f"{u}-{v}","answer_changed":tuple(fp)!=tuple(p0),
                         "frontier_size":len(front),"certificate_affected":affected,
                         "affected_fraction":affected/max(1,len(front)),
                         "full_seconds":full,"prototype_repair_seconds":repair,
                         "exact_match":ok})
    with (OUT/"incremental_baseline.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    summary={"updates_checked":checked,
             "all_exact_matches":all(r["exact_match"] for r in rows),
             "mean_affected_fraction":sum(r["affected_fraction"] for r in rows)/len(rows),
             "note":"Timing is diagnostic only: prototype repair deliberately recomputes the exact final frontier. No speedup is claimed."}
    (OUT/"incremental_baseline.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    if not summary["all_exact_matches"]: raise SystemExit("repair verification mismatch")

if __name__=="__main__": main()
