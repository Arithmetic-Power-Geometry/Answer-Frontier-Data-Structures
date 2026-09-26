"""Compare ordinary k-shortest/path-length ordering with AFDS intervention ordering."""
from __future__ import annotations
import csv,json,random,statistics
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths,path_length,global_transition_radius

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"artifacts";OUT.mkdir(exist_ok=True)
SEED=20260926
def make_graph(n,p,r):
 g=nx.Graph();g.add_nodes_from(range(n))
 for i in range(n-1):g.add_edge(i,i+1,weight=r.randint(2,20))
 for i in range(n):
  for j in range(i+2,n):
   if r.random()<p:g.add_edge(i,j,weight=r.randint(2,20))
 return g
def main():
 r=random.Random(SEED);rows=[];graphs=0
 for n in (5,6,7,8):
  for rep in range(40):
   g=make_graph(n,r.choice((.25,.35,.45,.55)),r)
   paths=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
   if len(paths)<3 or len(paths)>80:continue
   l0=path_length(g,paths[0])
   if abs(path_length(g,paths[1])-l0)<1e-10:continue
   alts=[p for p in paths[1:] if path_length(g,p)>l0+1e-10]
   if len(alts)<2:continue
   vals=[]
   for length_rank,p in enumerate(alts,1):
    rad,_=global_transition_radius(g,paths,p)
    vals.append((p,path_length(g,p),rad,length_rank))
   vals=[z for z in vals if z[2]<float("inf")]
   if len(vals)<2:continue
   graphs+=1
   byaf=sorted(vals,key=lambda z:(z[2],z[1],z[0]))
   nearest=byaf[0]; second=vals[0]
   afrank_second=next(i+1 for i,z in enumerate(byaf) if z[0]==second[0])
   lengthrank_nearest=nearest[3]
   regret=second[2]-nearest[2]
   rows.append({"n":n,"rep":rep,"num_paths":len(paths),"num_alternatives":len(vals),
    "same_top1":second[0]==nearest[0],"nearest_afds_length_rank":lengthrank_nearest,
    "second_shortest_afds_rank":afrank_second,"second_shortest_radius":second[2],
    "nearest_afds_radius":nearest[2],"absolute_intervention_regret":regret,
    "relative_intervention_regret":regret/nearest[2] if nearest[2]>1e-12 else 0.0})
 with (OUT/"kshortest_vs_afds.csv").open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 dis=[x for x in rows if not x["same_top1"]]
 summary={"seed":SEED,"graphs_compared":graphs,
  "top1_agreement_count":sum(x["same_top1"] for x in rows),
  "top1_disagreement_count":len(dis),
  "top1_disagreement_rate":len(dis)/len(rows) if rows else 0,
  "mean_nearest_afds_length_rank":statistics.mean(x["nearest_afds_length_rank"] for x in rows) if rows else None,
  "max_nearest_afds_length_rank":max((x["nearest_afds_length_rank"] for x in rows),default=None),
  "mean_absolute_regret_on_disagreement":statistics.mean(x["absolute_intervention_regret"] for x in dis) if dis else 0,
  "mean_relative_regret_on_disagreement":statistics.mean(x["relative_intervention_regret"] for x in dis) if dis else 0,
  "max_relative_regret":max((x["relative_intervention_regret"] for x in rows),default=0),
  "interpretation":"Descriptive comparison only: k-shortest optimizes path length; AFDS orders alternatives by minimum global intervention radius."}
 (OUT/"kshortest_vs_afds.json").write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
