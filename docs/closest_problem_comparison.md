# Closest-problem comparison

AFDS should be compared by **query semantics** before runtime.

| Problem family | Input/query asks for | Native output | AFDS distinction |
|---|---|---|---|
| Dynamic shortest path | shortest answer after graph update | updated distance/path/tree | AFDS also maintains nearby alternative answers under an intervention metric |
| k simple shortest paths | paths with next-smallest original lengths | length-ordered alternatives | AFDS orders alternatives by minimum intervention required to make them globally optimal |
| Replacement paths | shortest path after a specified path edge/node fails | replacement answer | intervention/failure is supplied by caller; AFDS discovers nearest alternative-answer transitions |
| Distance-sensitivity oracle | distance/path under a specified failure | failure-conditioned answer | AFDS maintains an inverse map from alternative answers to minimum interventions/witnesses |
| Inverse shortest path | make a predetermined path shortest with minimum modification | modification for supplied target path | AFDS frontier discovers/ranks multiple target alternatives rather than requiring one target |
| Parametric/sensitivity analysis | behavior under prescribed parameter changes/ranges | breakpoints/ranges/sensitivities | AFDS treats minimum intervention to alternative answers as maintained state |
| AFDS shortest-path laboratory | current answer plus top-k alternative paths by global transition cost | path, exact radius, intervention witness, reusable certificate | proposed abstraction under study |

## Conservative novelty statement

The individual ingredients above are established research areas. The candidate contribution is their organization into a dynamic answer-frontier abstraction and, in the shortest-path laboratory, exact maintenance of alternative-answer transition radii/witnesses with a cached primal-dual reuse certificate.

This table is a research-positioning aid, not a proof that no equivalent formulation exists in the literature.
