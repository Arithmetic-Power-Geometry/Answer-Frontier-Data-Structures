"""Margin-certificate falsification for AFDS path transition radii.

For a fixed target P and its optimal witness, let sigma be the minimum positive
slack to inactive path constraints. A single edge-weight update of magnitude
eta can alter any target-vs-competitor gap by at most eta. Thus eta < sigma
is a natural *candidate* local certificate when the edge is outside the target
and all active competitors. This lab tries to falsify that candidate by exact
LP recomputation; it does not claim a theorem.
"""
from __future__ import annotations
import json, random, math
from pathlib import Path
import networkx as nx
from afds.shortest_path import enumerate_simple_paths, answer_frontier, frontier_certificate, canonical_edge, path_edges

OUT=Path(__file__).resolve().parents[1]/"artifacts"; OUT.mkdir(exist_ok=True)
SEED=20260926

def make_graph(n,p,r):
    g=nx.Graph(); g.add_nodes_from(range(n))
    for i in range(n-1): g.add_edge(i,i+1,weight=r.randint(3,18))
    for i in range(n):
        for j in range(i+2,n):
            if r.random()<p: g.add_edge(i,j,weight=r.randint(3,18))
    return g

def main():
    r=random.Random(SEED)
    eligible=tested=violations=0; first=None; ratios=[]
    for n in (5,6,7,8):
      for rep in range(35):
        g=make_graph(n,.32,r)
        paths=enumerate_simple_paths(g,0,n-1,cutoff=n-1)
        if len(paths)<3: continue
        p0,front=answer_frontier(g,0,n-1,k=min(5,len(paths)-1),cutoff=n-1)
        for ent in front:
          cert=frontier_certificate(g,paths,ent.path)
          sigma=cert["min_inactive_slack"]
          if not math.isfinite(sigma) or sigma<=1e-7: continue
          protected=set(path_edges(ent.path))
          for q in cert["active_competitors"]: protected.update(path_edges(q))
          # Test edges outside target+active set; witness membership is not used.
          for u,v in g.edges():
            e=canonical_edge(u,v)
            if e in protected: continue
            eligible+=1
            # Stay strictly below half the inactive slack and below 0.5 weight.
            eta=min(0.25*sigma,0.5)
            if eta<=1e-8: continue
            for sign in (-1,1):
              nw=g[u][v]["weight"]+sign*eta
              if nw<0: continue
              h=g.copy(); h[u][v]["weight"]=nw
              hp,hf=answer_frontier(h,0,n-1,k=min(5,len(paths)-1),cutoff=n-1)
              if tuple(hp)!=tuple(p0): continue
              tested+=1
              newpaths=enumerate_simple_paths(h,0,n-1,cutoff=n-1)
              nc=frontier_certificate(h,newpaths,ent.path)
              ratios.append(eta/sigma)
              if abs(nc["radius"]-cert["radius"])>1e-7:
                violations+=1
                if first is None:
                  first={"n":n,"edge":[u,v],"signed_eta":sign*eta,"sigma":sigma,
                         "eta_over_sigma":eta/sigma,"target":ent.path,
                         "old_radius":cert["radius"],"new_radius":nc["radius"],
                         "active_competitors":cert["active_competitors"]}
    summary={"eligible_edges":eligible,"tested_updates":tested,
             "violations":violations,"candidate_survived":tested>0 and violations==0,
             "max_eta_over_sigma":max(ratios) if ratios else None,
             "first_counterexample":first,
             "interpretation":"Bounded falsification evidence only. A proof is required before using this as a certificate theorem."}
    (OUT/"margin_certificate_falsification.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    if tested==0: raise SystemExit("Margin certificate test was vacuous: no eligible updates.")

if __name__=="__main__": main()
