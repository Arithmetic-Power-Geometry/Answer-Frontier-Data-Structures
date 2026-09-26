from __future__ import annotations
import json,networkx as nx
from pathlib import Path
from afds.shortest_path import enumerate_simple_paths,global_transition_lp_certificate
OUT=Path(__file__).resolve().parents[1]/"artifacts";OUT.mkdir(exist_ok=True)
def main():
 g=nx.Graph();g.add_weighted_edges_from([(0,1,1),(0,2,1),(0,3,1),(1,2,3),(1,3,2)])
 ps=enumerate_simple_paths(g,0,3,cutoff=3); target=(0,2,1,3)
 cert=global_transition_lp_certificate(g,ps,target)
 active=[]
 for lab,res,dual in zip(cert["inequality_labels"],cert["inequality_residual"],cert["inequality_marginal"]):
  if abs(res)<1e-8:active.append({"label":lab,"dual":dual})
 out={"radius":cert["radius"],"active_inequalities":active,
      "active_lower_bounds":sum(abs(x)<1e-8 for x in cert["lower_residual"]),
      "nonzero_inequality_duals":sum(abs(x)>1e-10 for x in cert["inequality_marginal"]),
      "nonzero_lower_duals":sum(abs(x)>1e-10 for x in cert["lower_marginal"])}
 (OUT/"lp_certificate_probe.json").write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=="__main__":main()
