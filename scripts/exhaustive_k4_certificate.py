from __future__ import annotations
import itertools,json,math
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths,path_length,global_transition_radius,global_transition_lp_certificate,cached_primal_dual_radius_certificate
OUT=Path(__file__).resolve().parents[1]/"artifacts";OUT.mkdir(exist_ok=True)
def main():
 edges=list(itertools.combinations(range(4),2));graphs=updates=certified=viol=0
 first=None
 # Exhaust all connected K4-subgraphs with present-edge weights in {1,2}; require >=4 edges.
 for mask in range(1<<len(edges)):
  chosen=[edges[i] for i in range(len(edges)) if mask>>i&1]
  if len(chosen)<4:continue
  for ws in itertools.product((1,2),repeat=len(chosen)):
   g=nx.Graph();g.add_nodes_from(range(4))
   for e,w in zip(chosen,ws):g.add_edge(*e,weight=w)
   if not nx.is_connected(g):continue
   ps=enumerate_simple_paths(g,0,3,cutoff=3)
   if len(ps)<2:continue
   l0=path_length(g,ps[0])
   if abs(path_length(g,ps[1])-l0)<1e-10:continue
   targets=[p for p in ps[1:] if path_length(g,p)>l0+1e-10]
   if not targets:continue
   graphs+=1
   for p in targets:
    old,_=global_transition_radius(g,ps,p);cert=global_transition_lp_certificate(g,ps,p)
    for u,v in chosen:
     for d in (-1,1):
      if g[u][v]["weight"]+d<0:continue
      h=g.copy();h[u][v]["weight"]+=d;updates+=1
      if cached_primal_dual_radius_certificate(cert,h,ps,p):
       certified+=1;new,_=global_transition_radius(h,ps,p)
       if not math.isfinite(new) or abs(new-old)>1e-7:
        viol+=1
        if first is None:first={"edges":list(g.edges(data="weight")),"target":p,"edge":[u,v],"delta":d,"old":old,"new":new}
 out={"graphs_examined":graphs,"updates_tested":updates,"certified":certified,
      "certified_fraction":certified/updates if updates else 0,"violations":viol,"first_violation":first}
 (OUT/"exhaustive_k4_certificate.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
 if viol:raise SystemExit("certificate falsified")
if __name__=="__main__":main()
