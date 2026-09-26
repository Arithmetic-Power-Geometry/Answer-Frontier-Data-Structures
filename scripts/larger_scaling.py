from __future__ import annotations
import json,random,time
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths,path_length,global_transition_radius,global_transition_lp_certificate,cached_primal_dual_radius_certificate
OUT=Path(__file__).resolve().parents[1]/"artifacts";OUT.mkdir(exist_ok=True)
def mk(n,p,r):
 g=nx.Graph();g.add_nodes_from(range(n))
 for i in range(n-1):g.add_edge(i,i+1,weight=r.randint(5,30))
 for i in range(n):
  for j in range(i+2,n):
   if r.random()<p:g.add_edge(i,j,weight=r.randint(5,30))
 return g
def main():
 r=random.Random(20260926);rows=[];mismatch=0
 for n in (8,9,10):
  for p in (.18,.28):
   full=inc=reuse=0;tf=ti=0.;instances=0
   for _ in range(10):
    g=mk(n,p,r);ps=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
    if len(ps)<3 or len(ps)>100:continue
    l0=path_length(g,ps[0])
    if abs(path_length(g,ps[1])-l0)<1e-10:continue
    targets=[q for q in ps[1:4] if path_length(g,q)>l0+1e-10]
    old={tuple(q):global_transition_radius(g,ps,q)[0] for q in targets}
    cert={tuple(q):global_transition_lp_certificate(g,ps,q) for q in targets};instances+=1
    for u,v in list(g.edges())[:3]:
     h=g.copy();h[u][v]["weight"]+=1
     t=time.perf_counter();got={}
     for q in targets:
      if cached_primal_dual_radius_certificate(cert[tuple(q)],h,ps,q):
       got[tuple(q)]=old[tuple(q)];reuse+=1
      else:got[tuple(q)]=global_transition_radius(h,ps,q)[0];inc+=1
     ti+=time.perf_counter()-t
     t=time.perf_counter();truth={tuple(q):global_transition_radius(h,ps,q)[0] for q in targets};full+=len(targets);tf+=time.perf_counter()-t
     if any(abs(got[k]-truth[k])>1e-7 for k in truth):mismatch+=1
   if full:rows.append({"n":n,"density":p,"instances":instances,"full_solves":full,"incremental_solves":inc,
     "reuse":reuse,"solve_reduction":1-inc/full,"speedup":tf/ti if ti else None})
 out={"rows":rows,"mismatches":mismatch}
 (OUT/"larger_scaling.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
 if mismatch:raise SystemExit("mismatch")
if __name__=="__main__":main()
