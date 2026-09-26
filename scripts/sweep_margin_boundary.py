"""Empirically locate the sharp margin-certificate boundary."""
from __future__ import annotations
import json, random, math
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths, answer_frontier, frontier_certificate, path_edges, canonical_edge
OUT=Path(__file__).resolve().parents[1]/"artifacts"; OUT.mkdir(exist_ok=True)
RATIOS=(0.25,0.5,0.75,0.99,1.01,1.25,1.5,2.0)
SEED=20260926
def mk(n,r):
 g=nx.Graph(); g.add_nodes_from(range(n))
 for i in range(n-1): g.add_edge(i,i+1,weight=r.randint(4,20))
 for i in range(n):
  for j in range(i+2,n):
   if r.random()<.3:g.add_edge(i,j,weight=r.randint(4,20))
 return g
def main():
 r=random.Random(SEED); stats={str(a):{"tested":0,"violations":0,"first":None} for a in RATIOS}
 for n in (5,6,7):
  for rep in range(18):
   g=mk(n,r); paths=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
   if len(paths)<3:continue
   p0,front=answer_frontier(g,0,n-1,k=min(4,len(paths)-1),cutoff=n-1)
   for ent in front:
    cert=frontier_certificate(g,paths,ent.path); sig=cert["min_inactive_slack"]
    if not math.isfinite(sig) or sig<=1e-7:continue
    protected=set(path_edges(ent.path))
    for q in cert["active_competitors"]:protected.update(path_edges(q))
    candidates=[(u,v) for u,v in g.edges() if canonical_edge(u,v) not in protected]
    if not candidates:continue
    u,v=candidates[0]
    for a in RATIOS:
     eta=min(a*sig,1.0)
     for sign in (-1,1):
      nw=g[u][v]["weight"]+sign*eta
      if nw<0:continue
      h=g.copy();h[u][v]["weight"]=nw
      hp,_=answer_frontier(h,0,n-1,k=min(4,len(paths)-1),cutoff=n-1)
      if tuple(hp)!=tuple(p0):continue
      np=enumerate_simple_paths(h,0,n-1,cutoff=n-1)
      nc=frontier_certificate(h,np,ent.path)
      z=stats[str(a)];z["tested"]+=1
      if abs(nc["radius"]-cert["radius"])>1e-7:
       z["violations"]+=1
       if z["first"] is None:z["first"]={"n":n,"edge":[u,v],"ratio":a,"sigma":sig,"eta":sign*eta,"old":cert["radius"],"new":nc["radius"]}
 (OUT/"margin_boundary_sweep.json").write_text(json.dumps(stats,indent=2))
 print(json.dumps(stats,indent=2))
if __name__=="__main__":main()
