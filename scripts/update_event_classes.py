from __future__ import annotations
import json,random
from pathlib import Path
import networkx as nx
from afds.shortest_path import answer_frontier
OUT=Path(__file__).resolve().parents[1]/"artifacts";OUT.mkdir(exist_ok=True)
def mk(n,r):
 g=nx.Graph();g.add_nodes_from(range(n))
 for i in range(n-1):g.add_edge(i,i+1,weight=r.randint(2,15))
 for i in range(n):
  for j in range(i+2,n):
   if r.random()<.4:g.add_edge(i,j,weight=r.randint(2,15))
 return g
def sig(g):
 p,f=answer_frontier(g,0,len(g)-1,k=3,cutoff=len(g)-1)
 return tuple(p),tuple((tuple(x.path),round(x.global_radius,8)) for x in f)
def main():
 r=random.Random(20260926); counts={"silent":0,"frontier_only":0,"answer_and_frontier":0,"answer_only":0};tested=0
 examples={}
 for n in (5,6,7):
  for _ in range(25):
   g=mk(n,r)
   try: bp,bf=sig(g)
   except Exception: continue
   edges=list(g.edges());r.shuffle(edges)
   for u,v in edges[:min(5,len(edges))]:
    old=g[u][v]["weight"]
    for d in (-1,1):
     if old+d<0:continue
     h=g.copy();h[u][v]["weight"]=old+d
     try: ap,af=sig(h)
     except Exception:continue
     ac=ap!=bp;fc=af!=bf
     key=("answer_and_frontier" if ac and fc else "answer_only" if ac else "frontier_only" if fc else "silent")
     counts[key]+=1;tested+=1
     if key not in examples:examples[key]={"n":n,"edge":[u,v],"old":old,"new":old+d,"before_answer":bp,"after_answer":ap,"before_frontier":bf,"after_frontier":af}
 out={"seed":20260926,"updates_tested":tested,"counts":counts,
  "rates":{k:v/tested for k,v in counts.items()} if tested else {},
  "frontier_detects_change_when_answer_silent_rate":counts["frontier_only"]/(counts["frontier_only"]+counts["silent"]) if counts["frontier_only"]+counts["silent"] else 0,
  "examples":examples}
 (OUT/"update_event_classes.json").write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!="examples"},indent=2))
if __name__=="__main__":main()
