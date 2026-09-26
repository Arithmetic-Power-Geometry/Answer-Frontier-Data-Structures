from __future__ import annotations
import json,random,math
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths,path_length,global_transition_radius,stored_primal_dual_radius_certificate
OUT=Path(__file__).resolve().parents[1]/"artifacts";OUT.mkdir(exist_ok=True)
def mk(n,r):
 g=nx.Graph();g.add_nodes_from(range(n))
 for i in range(n-1):g.add_edge(i,i+1,weight=r.randint(2,12))
 for i in range(n):
  for j in range(i+2,n):
   if r.random()<.38:g.add_edge(i,j,weight=r.randint(2,12))
 return g
def main():
 r=random.Random(20260926); tested=certified=violations=0;first=None
 for n in (5,6,7):
  for _ in range(20):
   g=mk(n,r);ps=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
   if len(ps)<2 or len(ps)>50:continue
   l0=path_length(g,ps[0])
   if abs(path_length(g,ps[1])-l0)<1e-10:continue
   targets=[p for p in ps[1:4] if path_length(g,p)>l0+1e-10]
   for p in targets:
    old,_=global_transition_radius(g,ps,p)
    for u,v in list(g.edges())[:5]:
     for d in (-1,1):
      if g[u][v]["weight"]+d<0:continue
      h=g.copy();h[u][v]["weight"]+=d;tested+=1
      ok=stored_primal_dual_radius_certificate(g,h,ps,p)
      if ok:
       certified+=1;new,_=global_transition_radius(h,ps,p)
       if not math.isfinite(new) or abs(new-old)>1e-7:
        violations+=1
        if first is None:first={"n":n,"edge":[u,v],"delta":d,"old":old,"new":new,"target":p}
 out={"updates_tested":tested,"certified_reuse":certified,"certified_fraction":certified/tested if tested else 0,
      "certified_violations":violations,"first_violation":first,
      "claim":"Only certified cases may skip re-solving; uncertified cases require exact LP recomputation."}
 (OUT/"primal_dual_certificate_test.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
 if violations:raise SystemExit("certificate falsified")
if __name__=="__main__":main()
