"""Adversarial exhaustive search for failure of active-path locality."""
from __future__ import annotations
import itertools,json,math
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths, frontier_certificate, path_edges, canonical_edge
OUT=Path(__file__).resolve().parents[1]/"artifacts";OUT.mkdir(exist_ok=True)
def main():
 checked=eligible=0; first=None
 for n in (4,5):
  verts=range(n); all_edges=list(itertools.combinations(verts,2))
  for m in range(n, min(len(all_edges),n+2)+1):
   for es in itertools.combinations(all_edges,m):
    topo=nx.Graph();topo.add_nodes_from(verts);topo.add_edges_from(es)
    if not nx.is_connected(topo):continue
    # deterministic bounded weights; enough to attack structure, not prove universality
    for ws in itertools.product((1,2,3),repeat=m):
     g=nx.Graph();g.add_nodes_from(verts)
     for e,w in zip(es,ws):g.add_edge(*e,weight=w)
     paths=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
     if len(paths)<3:continue
     if len(paths)>12:continue
     current=paths[0]
     if len(paths)>1 and abs(sum(g[u][v]["weight"] for u,v in zip(paths[0][:-1],paths[0][1:]))-sum(g[u][v]["weight"] for u,v in zip(paths[1][:-1],paths[1][1:])))<1e-10:continue
     for target in paths[1:min(5,len(paths))]:
      cert=frontier_certificate(g,paths,target)
      if not math.isfinite(cert["radius"]):continue
      protected=set(path_edges(target))
      for q in cert["active_competitors"]:protected.update(path_edges(q))
      for u,v in g.edges():
       e=canonical_edge(u,v)
       if e in protected:continue
       eligible+=1
       for d in (-1,1):
        nw=g[u][v]["weight"]+d
        if nw<0:continue
        h=g.copy();h[u][v]["weight"]=nw
        hp=enumerate_simple_paths(h,0,n-1,cutoff=n-1)
        if not hp or tuple(hp[0])!=tuple(current):continue
        nc=frontier_certificate(h,hp,target);checked+=1
        if abs(nc["radius"]-cert["radius"])>1e-8:
         first={"n":n,"m":m,"edges":[[a,b,g[a][b]["weight"]] for a,b in g.edges()],
                "current":current,"target":target,"updated_edge":[u,v],"delta":d,
                "old_radius":cert["radius"],"new_radius":nc["radius"],
                "active_competitors":cert["active_competitors"],
                "min_inactive_slack":cert["min_inactive_slack"]}
         break
       if first:break
      if first:break
     if first:break
    if first:break
   if first:break
  if first:break
 summary={"checked_updates":checked,"eligible_edges":eligible,"counterexample_found":first is not None,"first_counterexample":first,
          "scope":"bounded exhaustive topology/weights search; not a proof if no counterexample is found"}
 (OUT/"active_locality_adversarial.json").write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
