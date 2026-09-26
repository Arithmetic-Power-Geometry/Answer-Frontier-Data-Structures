from __future__ import annotations
import json,random,math
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths,path_length,global_transition_radius,global_transition_lp_certificate,cached_primal_dual_radius_certificate
OUT=Path(__file__).resolve().parents[1]/"artifacts";OUT.mkdir(exist_ok=True)
def mk(n,r):
 g=nx.Graph();g.add_nodes_from(range(n))
 for i in range(n-1):g.add_edge(i,i+1,weight=r.randint(4,20))
 for i in range(n):
  for j in range(i+2,n):
   if r.random()<.42:g.add_edge(i,j,weight=r.randint(4,20))
 return g
def main():
 r=random.Random(20260926);tested=accepted=viol=0;by={str(d):{"tested":0,"accepted":0} for d in (-3,-2,-1,1,2,3)}
 for n in (5,6,7,8):
  for _ in range(12):
   g=mk(n,r);ps=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
   if len(ps)<2 or len(ps)>60:continue
   l0=path_length(g,ps[0])
   if abs(path_length(g,ps[1])-l0)<1e-10:continue
   for p in [q for q in ps[1:4] if path_length(g,q)>l0+1e-10]:
    old,_=global_transition_radius(g,ps,p);cert=global_transition_lp_certificate(g,ps,p)
    for u,v in list(g.edges())[:4]:
     for d in (-3,-2,-1,1,2,3):
      if g[u][v]["weight"]+d<0:continue
      h=g.copy();h[u][v]["weight"]+=d;tested+=1;by[str(d)]["tested"]+=1
      if cached_primal_dual_radius_certificate(cert,h,ps,p):
       accepted+=1;by[str(d)]["accepted"]+=1;new,_=global_transition_radius(h,ps,p)
       if not math.isfinite(new) or abs(new-old)>1e-7:viol+=1
 out={"updates_tested":tested,"certified":accepted,"certified_fraction":accepted/tested if tested else 0,
      "violations":viol,"by_update_magnitude":by}
 (OUT/"certificate_magnitude_stress.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
 if viol:raise SystemExit("certificate falsified")
if __name__=="__main__":main()
