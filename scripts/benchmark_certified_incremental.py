from __future__ import annotations
import json,random,time
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths,path_length,global_transition_radius,stored_primal_dual_radius_certificate
OUT=Path(__file__).resolve().parents[1]/"artifacts";OUT.mkdir(exist_ok=True)
def mk(n,r):
 g=nx.Graph();g.add_nodes_from(range(n))
 for i in range(n-1):g.add_edge(i,i+1,weight=r.randint(3,15))
 for i in range(n):
  for j in range(i+2,n):
   if r.random()<.35:g.add_edge(i,j,weight=r.randint(3,15))
 return g
def main():
 r=random.Random(20260926);cases=solves_full=solves_inc=reused=mismatch=0;tfull=tinc=0.
 for n in (5,6,7):
  for _ in range(15):
   g=mk(n,r);ps=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
   if len(ps)<3 or len(ps)>45:continue
   l0=path_length(g,ps[0])
   if abs(path_length(g,ps[1])-l0)<1e-10:continue
   targets=[p for p in ps[1:4] if path_length(g,p)>l0+1e-10]
   old={tuple(p):global_transition_radius(g,ps,p)[0] for p in targets}
   for u,v in list(g.edges())[:4]:
    h=g.copy();h[u][v]["weight"]+=1;cases+=1
    t=time.perf_counter();inc={}
    for p in targets:
     if stored_primal_dual_radius_certificate(g,h,ps,p):
      inc[tuple(p)]=old[tuple(p)];reused+=1
     else:
      inc[tuple(p)]=global_transition_radius(h,ps,p)[0];solves_inc+=1
    tinc+=time.perf_counter()-t
    t=time.perf_counter();full={}
    for p in targets:
     full[tuple(p)]=global_transition_radius(h,ps,p)[0];solves_full+=1
    tfull+=time.perf_counter()-t
    if any(abs(inc[k]-full[k])>1e-7 for k in full):mismatch+=1
 out={"update_cases":cases,"full_lp_solves":solves_full,"incremental_lp_solves":solves_inc,
      "certified_reuses":reused,"lp_solve_reduction":1-solves_inc/solves_full if solves_full else 0,
      "frontier_mismatches":mismatch,"incremental_seconds":tinc,"full_recompute_seconds":tfull,
      "speedup_full_over_incremental":tfull/tinc if tinc else None,
      "note":"Full recomputation is performed only after the incremental path for independent validation; its solves are not included in incremental_lp_solves."}
 (OUT/"incremental_certificate_benchmark.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
 if mismatch:raise SystemExit("incremental result mismatch")
if __name__=="__main__":main()
