"""Deterministic search for small AFDS theorem witnesses.

Enumerates connected undirected graph topologies and small positive integer
weights in increasing n, then records the first witness for each separation.
The search is intentionally bounded so CI remains auditable and fast.
"""
from __future__ import annotations
import itertools, json
from pathlib import Path
import networkx as nx
from afds.shortest_path import (
    enumerate_simple_paths, path_length, pairwise_transition_radius,
    global_transition_radius, answer_frontier,
)

OUT=Path(__file__).resolve().parents[1]/"artifacts"
OUT.mkdir(exist_ok=True)

def encode_graph(g):
    return [{"u":u,"v":v,"w":g[u][v]["weight"]} for u,v in sorted(g.edges())]

def frontier_sig(g,s,t,k=3):
    p0,f=answer_frontier(g,s,t,k=k,cutoff=len(g)-1)
    return tuple(p0), [(tuple(x.path),round(x.global_radius,10)) for x in f]

def inspect(g,s,t):
    paths=enumerate_simple_paths(g,s,t,cutoff=len(g)-1)
    if len(paths)<3: return {}
    ls=[path_length(g,p) for p in paths]
    if abs(ls[0]-ls[1])<1e-10: return {}
    p0=paths[0]
    alts=[]
    for p in paths[1:]:
        if path_length(g,p)<=ls[0]+1e-10: continue
        pair=pairwise_transition_radius(g,p0,p)
        glob,wit=global_transition_radius(g,paths,p)
        alts.append((p,path_length(g,p),pair,glob,wit))
    if len(alts)<2: return {}
    bylen=sorted(alts,key=lambda z:(z[1],z[0]))
    byglob=sorted(alts,key=lambda z:(z[3],z[1],z[0]))
    out={}
    if bylen[0][0]!=byglob[0][0]:
        out["length_transition"]={
            "current":p0,"second_shortest":bylen[0][0],
            "second_shortest_length":bylen[0][1],
            "second_shortest_global_radius":bylen[0][3],
            "nearest_transition":byglob[0][0],
            "nearest_transition_length":byglob[0][1],
            "nearest_transition_global_radius":byglob[0][3],
        }
    strict=[z for z in alts if z[3]>z[2]+1e-8]
    if strict:
        z=max(strict,key=lambda z:z[3]-z[2])
        out["pairwise_global"]={
            "current":p0,"alternative":z[0],"length":z[1],
            "pairwise_radius":z[2],"global_radius":z[3],
            "strict_gap":z[3]-z[2],
        }
    try:
        bp,bf=frontier_sig(g,s,t)
        for u,v in list(g.edges()):
            old=g[u][v]["weight"]
            for d in (-1,1):
                nw=old+d
                if nw<=0: continue
                h=g.copy(); h[u][v]["weight"]=nw
                ap,af=frontier_sig(h,s,t)
                if ap==bp and af!=bf:
                    out["answer_silent"]={
                        "current":bp,"updated_edge":[u,v],
                        "old_weight":old,"new_weight":nw,
                        "before":bf,"after":af,
                    }
                    raise StopIteration
    except StopIteration:
        pass
    except Exception:
        pass
    return out

def candidates(n,max_edges=7):
    all_edges=list(itertools.combinations(range(n),2))
    for m in range(n-1,min(max_edges,len(all_edges))+1):
        for es in itertools.combinations(all_edges,m):
            base=nx.Graph(); base.add_nodes_from(range(n)); base.add_edges_from(es)
            if not nx.is_connected(base): continue
            if not nx.has_path(base,0,n-1): continue
            # Deterministic compact weight family: enough variation to expose
            # structural witnesses without exploding CI search.
            for weights in itertools.product((1,2,3), repeat=m):
                g=nx.Graph(); g.add_nodes_from(range(n))
                for (u,v),w in zip(es,weights): g.add_edge(u,v,weight=w)
                yield g

def main():
    found={}
    examined=0
    for n in range(3,6):
        for g in candidates(n):
            examined+=1
            hit=inspect(g,0,n-1)
            for key,val in hit.items():
                if key not in found:
                    found[key]={
                        "n":n,"m":g.number_of_edges(),"source":0,"target":n-1,
                        "edges":encode_graph(g),"witness":val,
                    }
            if len(found)==3:
                break
        if len(found)==3: break
    result={"graphs_examined":examined,"witnesses":found}
    (OUT/"minimal_witnesses.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    rows=[]
    for kind,x in found.items():
        rows.append({"separation":kind,"n":x["n"],"m":x["m"],"edges":json.dumps(x["edges"]),"witness":json.dumps(x["witness"])})
    import csv
    with (OUT/"minimal_witnesses.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["separation","n","m","edges","witness"]); w.writeheader(); w.writerows(rows)
    print(json.dumps(result,indent=2))
    if len(found)<3:
        raise SystemExit("Bounded search did not find all three required witnesses.")

if __name__=="__main__":
    main()
