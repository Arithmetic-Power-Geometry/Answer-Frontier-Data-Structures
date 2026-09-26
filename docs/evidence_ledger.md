# AFDS Evidence Ledger

This file records only results produced by repository experiments/CI. It is intended to keep manuscript claims traceable and scoped.

| Question | Evidence | Result | Scope / limitation |
|---|---|---|---|
| Does constrained pairwise radius match an independent LP? | core correctness CI | Passed | Nonnegative perturbed edge weights; tested instances |
| Can pairwise and global transition radii differ? | pairwise/global benchmark | 189 / 735 strict separations (25.71%); mean relative underestimate 17.72%; max 54.46% | Synthetic finite simple-path instances |
| Is nearest-by-length always nearest-by-intervention? | k-shortest baseline | 21 / 122 graphs disagree (17.21%); mean relative intervention regret on disagreements 19.99%; max 100% | Different objectives; not a claim that k-shortest is inferior |
| Can frontier change without current answer changing? | update-event experiment | 507 frontier-only, 231 silent, 8 answer+frontier among 746 ±1 updates; 68.70% of answer-silent updates were frontier-active | Synthetic update distribution only |
| Does cached primal-dual reuse preserve exact radius? | random falsification | 637 / 1,520 certified; 0 violations | Weight-only, fixed topology/path family |
| Does reuse survive larger update magnitudes? | magnitude stress | 1,040 / 2,616 certified (39.76%); 0 violations for deltas -3..+3 | Weight-only, fixed topology/path family |
| Does reuse survive exhaustive small instances? | exhaustive K4 | 389 weighted graph instances; 7,196 update/target cases; 1,654 certified; 0 violations | K4 subgraphs, present-edge weights {1,2}, ±1 updates |
| Does caching reduce exact LP work? | cached scaling | 1,206 full solves vs 670 incremental solves; 536 reuses; 0 mismatches | n=5..8 benchmark |
| Does solve reduction translate to runtime? | cached scaling | 1.50x aggregate wall-clock speedup | Benchmark-specific, Python/SciPy implementation |
| Does benefit persist at larger n? | larger scaling | zero mismatches; 44.4%–74.1% solve reduction; ~1.46x–1.91x speedup across reported n=8..10 cells | path enumeration capped at 100; n=10,density=.28 has only 3 admissible instances |

## Claim discipline

The repository does not claim that AFDS is a faster replacement for ordinary shortest-path, k-shortest-path, replacement-path, or distance-sensitivity algorithms. Those solve different query problems.

The demonstrated computational comparison is against **full recomputation of the same AFDS global-transition LPs** after weight updates.

The cached primal-dual theorem is a sufficient exact-reuse certificate. Rejection does not imply that the radius changed.

Edge insertion/deletion is outside the current cached-certificate theorem because topology and the feasible path family can change.
