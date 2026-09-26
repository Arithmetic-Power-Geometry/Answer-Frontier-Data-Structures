from __future__ import annotations
import json,random,time
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths,path_length,global_transition_radius,global_transition_lp_certificate,cached_primal_dual_radius_certificate
OUT=Path(__file__).resolve().parents[1]/"artifacts";OUT.mkdir(exist_ok=True)
def mk(n,p,r):
 g=nx.Graph();g.add_nodes_from(range(n))
 for i in range(n-1):g.add_edge(i,i+1,weight=r.randint(3,18))
 for i in range(n):
  for j in range(i+2,n):
   if r.random()<p:g.add_edge(i,j,weight=r.randint(3,18))
 return g
def main():
 r=random.Random(20260926);rows=[];total_full=total_inc=total_reuse=mis=0;tf=ti=0.
 for n in (5,6,7,8):
  for p in (.25,.4,.55):
   full=inc=reuse=cases=0;sf=si=0.
   for _ in range(8):
    g=mk(n,p,r);ps=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
    if len(ps)<3 or len(ps)>55:continue
    l0=path_length(g,ps[0])
    if abs(path_length(g,ps[1])-l0)<1e-10:continue
    targets=[q for q in ps[1:4] if path_length(g,q)>l0+1e-10]
    old={tuple(q):global_transition_radius(g,ps,q)[0] for q in targets}
    cert={tuple(q):global_transition_lp_certificate(g,ps,q) for q in targets}
    for u,v in list(g.edges())[:3]:
     for d in (-1,1):
      if g[u][v]["weight"]+d<0:continue
      h=g.copy();h[u][v]["weight"]+=d;cases+=1
      t=time.perf_counter();got={}
      for q in targets:
       if cached_primal_dual_radius_certificate(cert[tuple(q)],h,ps,q):
        got[tuple(q)]=old[tuple(q)];reuse+=1
       else:got[tuple(q)]=global_transition_radius(h,ps,q)[0];inc+=1
      si+=time.perf_counter()-t
      t=time.perf_counter();truth={tuple(q):global_transition_radius(h,ps,q)[0] for q in targets};full+=len(targets);sf+=time.perf_counter()-t
      if any(abs(got[k]-truth[k])>1e-7 for k in truth):mis+=1
   if full:rows.append({"n":n,"density":p,"cases":cases,"full_solves":full,"incremental_solves":inc,"reuse":reuse,
     "solve_reduction":1-inc/full,"incremental_seconds":si,"full_seconds":sf,"speedup":sf/si if si else None})
   total_full+=full;total_inc+=inc;total_reuse+=reuse;tf+=sf;ti+=si
 out={"rows":rows,"total_full_lp_solves":total_full,"total_incremental_lp_solves":total_inc,"total_certified_reuses":total_reuse,
      "overall_solve_reduction":1-total_inc/total_full if total_full else 0,"frontier_mismatches":mis,
      "incremental_seconds":ti,"full_seconds":tf,"overall_speedup":tf/ti if ti else None}
 (OUT/"cached_certificate_scaling.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
 if mis:raise SystemExit("mismatch")
if __name__=="__main__":main()
