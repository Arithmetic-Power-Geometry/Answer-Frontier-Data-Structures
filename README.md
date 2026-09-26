# Answer-Frontier Data Structures (AFDS)

**Status:** validated research prototype / reproducibility laboratory

Answer-Frontier Data Structures (AFDS) study a dynamic data-structure abstraction that maintains not only a current query answer, but also a bounded frontier of nearby alternative answers together with the minimum intervention cost and witness required to reach them.

For a state `x`, query `q`, admissible intervention family `U`, and cost `c`, let `a=q(x)`. The bounded answer frontier is the `k` minimum-cost triples `(a', d(a'), W(a'))` over alternative answers `a' != a`, where

```
d(a') = min { c(u) : u in U and q(u(x)) = a' }.
```

The defining dynamic requirement is that the frontier is maintained as the underlying state changes. This permits **frontier-active, answer-silent updates**: updates for which the current answer is unchanged but the identity, cost, or witness of a nearby alternative changes.

## Novelty boundary

AFDS does **not** claim novelty for dynamic shortest paths, k-shortest paths, replacement paths, distance-sensitivity oracles, single-edge shortest-path sensitivity, inverse shortest paths, parametric shortest paths, graph interdiction, or minimum perturbation/stability radii in isolation.

The research hypothesis tested here is narrower:

> A useful general data-structure interface can maintain the current answer **and** a bounded inverse map from nearby alternative answers to minimum transition costs and witnesses, and can expose frontier changes even when the answer itself does not change.

## First laboratory: weighted shortest paths

For a current unique shortest path `P0` and alternative path `P`, interventions satisfy both `|Delta_e| <= epsilon` and the shortest-path state-space constraint `w_e + Delta_e >= 0`. Let `A=P0\\P`, `B=P\\P0`, and `g=L(P)-L(P0)`. The exact pairwise tie radius is the smallest nonnegative `epsilon` satisfying

```
|A| epsilon + sum_{e in B} min(epsilon, w_e) >= g.
```

When no alternative-only edge reaches the zero-weight floor this reduces to the familiar unconstrained expression `g / |P0 symmetric_difference P|`. The implementation solves the general piecewise-linear (water-filling) form and independently regression-tests it against a two-path linear program.

The repository also computes an exact global-optimality radius for the finite set of enumerated simple paths by linear programming, with the same nonnegative perturbed-weight constraint.

The laboratory searches for:
1. **length-transition separation** — second-shortest need not be nearest transition;
2. **pairwise-global separation** — beating the current answer need not make an alternative globally shortest;
3. **frontier-active, answer-silent updates** — current shortest path stays fixed while its answer frontier changes;
4. **frontier amplification** — one graph update changes multiple frontier entries.

## Run

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/run_experiments.py
```

Generated evidence is written to `artifacts/`: CSV tables, JSON summaries, PNG figures, and a Markdown report.

GitHub Actions runs the same pipeline and uploads the evidence package as a workflow artifact.

## License

Apache License 2.0.

Copyright © 2026 Mohammad Amir Khusru Akhtar


## Evidence and scope

Validated numerical claims, workflow provenance, and limitations are recorded in `docs/evidence_ledger.md`. The closest-problem semantic comparison is recorded in `docs/closest_problem_comparison.md`, and the cached primal-dual reuse theorem is stated in `docs/primal_dual_certificate.md`.

The repository does not claim that AFDS is faster than ordinary shortest-path, replacement-path, distance-sensitivity, or k-shortest algorithms; those solve different query problems. Runtime comparisons in this repository compare exact AFDS global-transition recomputation against exact certified AFDS reuse under the same task definition.
