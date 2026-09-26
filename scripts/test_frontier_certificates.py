"""Falsification lab for active-constraint AFDS frontier certificates."""
from __future__ import annotations
import json, random
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths, answer_frontier, frontier_certificate, canonical_edge, path_edges

OUT=Path(__file__).resolve().parents[1]/"artifacts"; OUT.mkdir(exist_ok=True)
SEED=20260926

def graph(n,p,r):
    g=nx.Graph(); g.add_nodes_from(range(n))
    for i in range(n-1): g.add_edge(i,i+1,weight=r.randint(2,15))
    for i in range(n):
        for j in range(i+2,n):
            if r.random()<p: g.add_edge(i,j,weight=r.randint(2,15))
    return g

def main():
    r=random.Random(SEED)
    trials=safe_candidates=violations=0
    counterexample=None
    active_counts=[]; margins=[]
    for n in (5,6,7):
      for rep in range(20):
        g=graph(n,.35,r); paths=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
        if len(paths)<3: continue
        p0,front=answer_frontier(g,0,n-1,k=min(5,len(paths)-1),cutoff=n-1)
        for ent in front:
          cert=frontier_certificate(g,paths,ent.path)
          active_counts.append(len(cert["active_competitors"]))
          if cert["min_inactive_slack"]<1e100: margins.append(cert["min_inactive_slack"])
          cert_edges=set(path_edges(ent.path))
          for q in cert["active_competitors"]: cert_edges.update(path_edges(q))
          cert_edges.update(cert["witness"].keys())
          for u,v in g.edges():
            e=canonical_edge(u,v)
            if e in cert_edges: continue
            # Conservative test: small +/-1 update, current answer must stay fixed.
            for d in (-1,1):
              nw=g[u][v]["weight"]+d
              if nw<0: continue
              h=g.copy(); h[u][v]["weight"]=nw
              try:
                hp,hf=answer_frontier(h,0,n-1,k=min(5,len(paths)-1),cutoff=n-1)
              except Exception: continue
              if tuple(hp)!=tuple(p0): continue
              trials+=1; safe_candidates+=1
              newpaths=enumerate_simple_paths(h,0,n-1,cutoff=n-1)
              nc=frontier_certificate(h,newpaths,ent.path)
              # Falsify the naive claim "outside certificate edges => radius unchanged".
              if abs(nc["radius"]-cert["radius"])>1e-8:
                violations+=1
                if counterexample is None:
                  counterexample={"n":n,"edge":[u,v],"delta":d,"target":ent.path,
                                  "old_radius":cert["radius"],"new_radius":nc["radius"],
                                  "active_competitors":cert["active_competitors"],
                                  "min_inactive_slack":cert["min_inactive_slack"]}
    summary={"tested_outside_certificate_updates":trials,
             "naive_certificate_violations":violations,
             "naive_certificate_survived":violations==0,
             "mean_active_competitors":sum(active_counts)/len(active_counts) if active_counts else 0,
             "min_observed_inactive_slack":min(margins) if margins else None,
             "first_counterexample":counterexample,
             "interpretation":"A zero violation count is evidence only within this bounded falsification lab, not a theorem."}
    (OUT/"certificate_falsification.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
