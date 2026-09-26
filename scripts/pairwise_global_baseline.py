from __future__ import annotations
import json, random, math
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths,path_length,pairwise_transition_radius,global_transition_radius
OUT=Path(__file__).resolve().parents[1]/"artifacts"; OUT.mkdir(exist_ok=True)
def mk(n,r):
 g=nx.Graph();g.add_nodes_from(range(n))
 for i in range(n-1):g.add_edge(i,i+1,weight=r.randint(2,15))
 for i in range(n):
  for j in range(i+2,n):
   if r.random()<.38:g.add_edge(i,j,weight=r.randint(2,15))
 return g
def main():
 r=random.Random(20260926); vals=[]; graphs=0
 for n in (5,6,7):
  for _ in range(30):
   g=mk(n,r); ps=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
   if len(ps)<2 or len(ps)>60:continue
   l0=path_length(g,ps[0])
   if abs(path_length(g,ps[1])-l0)<1e-10:continue
   used=False
   for p in ps[1:]:
    if path_length(g,p)<=l0+1e-10:continue
    a=pairwise_transition_radius(g,ps[0],p); b,_=global_transition_radius(g,ps,p)
    if math.isfinite(a) and math.isfinite(b):
     if b+1e-8<a: raise RuntimeError("global radius below pairwise radius")
     vals.append((a,b));used=True
   graphs+=int(used)
 strict=[(a,b) for a,b in vals if b>a+1e-8]
 rel=[(b-a)/b for a,b in strict if b>1e-12]
 out={"graphs_compared":graphs,"alternatives_compared":len(vals),
 "strict_separations":len(strict),"separation_rate":len(strict)/len(vals) if vals else 0,
 "mean_relative_underestimate_when_strict":sum(rel)/len(rel) if rel else 0,
 "max_relative_underestimate":max(rel,default=0),
 "max_global_pairwise_ratio":max((b/a for a,b in vals if a>1e-12),default=1),
 "global_ge_pairwise_verified":True}
 (OUT/"pairwise_global_baseline.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=="__main__":main()
