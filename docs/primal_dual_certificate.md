# Cached Primal-Dual Radius Certificate

## Setting

Fix a graph topology, an enumerated feasible path family \(\mathcal P\), and a target path \(P\).
For edge-weight vector \(w\), the AFDS global transition radius is the optimum of the LP

\[
\min_{\Delta,\epsilon}\ \epsilon
\]

subject to

\[
|\Delta_e|\le \epsilon,
\qquad
w_e+\Delta_e\ge 0,
\]

and, for every \(Q\in\mathcal P\),

\[
L_{w+\Delta}(P)\le L_{w+\Delta}(Q).
\]

Let \((\Delta^*,\epsilon^*)\) be an optimal primal solution for the old weights \(w\), and let
\((y^*,z^*)\) denote corresponding optimal dual multipliers for the inequality system and variable lower bounds.

## Theorem — Cached primal-dual reuse

After a weight-only update \(w\mapsto w'\), suppose:

1. the graph topology and enumerated path family are unchanged;
2. the stored primal point \((\Delta^*,\epsilon^*)\) is feasible for the updated LP;
3. the stored dual multipliers are feasible for the updated dual; and
4. their updated dual objective value equals \(\epsilon^*\).

Then

\[
d^*_{w'}(P)=\epsilon^*.
\]

Hence the old global transition radius is exactly reusable and the updated LP need not be solved.

### Proof

Updated primal feasibility gives, by weak duality,

\[
d^*_{w'}(P)\le \epsilon^*.
\]

Updated dual feasibility with dual objective \(\epsilon^*\) gives

\[
d^*_{w'}(P)\ge \epsilon^*.
\]

Therefore

\[
d^*_{w'}(P)=\epsilon^*.
\]

No assumption about preservation of the old active path set is required.

## Scope

The implemented certificate is sufficient, not necessary: rejection means only that exact reuse was not certified.

The current implementation applies to **weight-only updates with fixed topology and fixed enumerated path family**. Edge insertion/deletion can change the variable set and feasible path family and therefore requires rebuilding the LP/certificate unless a separate structural certificate is proved.

## Falsification evidence

The theorem is algebraic; experiments test the implementation rather than establish the theorem.

Current implementation checks include:

- 1,520 random update/target cases: 637 certified, 0 violations.
- 2,616 updates with magnitudes \(-3,-2,-1,+1,+2,+3\): 1,040 certified, 0 violations.
- exhaustive weighted K4 study: 389 graph instances, 7,196 update/target cases, 1,654 certified, 0 violations.
- cached scaling benchmark: 1,206 full LP solves versus 670 incremental LP solves, 536 certified reuses, 0 frontier mismatches, approximately 1.50x wall-clock speedup in that benchmark.

These measurements are benchmark-specific and are not universal performance guarantees.
