"""Exact AFDS instance for dynamic one-dimensional total order."""
from __future__ import annotations
from dataclasses import dataclass
from bisect import bisect_left, insort

@dataclass(frozen=True)
class OrderTransition:
    left: float
    right: float
    radius: float

class OrderFrontier:
    """Maintain nearest adjacent order changes under symmetric L-infinity moves.

    For distinct sorted keys x_i, changing total order requires some adjacent
    pair to meet; the minimum radius for pair (x_i,x_{i+1}) is half its gap.
    """
    def __init__(self, values=()):
        self._x=sorted(float(v) for v in values)
        if len(set(self._x))!=len(self._x): raise ValueError("keys must be distinct")

    @property
    def values(self): return tuple(self._x)

    def insert(self,x):
        x=float(x); i=bisect_left(self._x,x)
        if i<len(self._x) and self._x[i]==x: raise ValueError("duplicate key")
        insort(self._x,x)

    def delete(self,x):
        x=float(x); i=bisect_left(self._x,x)
        if i==len(self._x) or self._x[i]!=x: raise KeyError(x)
        self._x.pop(i)

    def frontier(self,k=None):
        z=[OrderTransition(a,b,(b-a)/2.0) for a,b in zip(self._x[:-1],self._x[1:])]
        z.sort(key=lambda t:(t.radius,t.left,t.right))
        return z if k is None else z[:k]

    def nearest(self):
        f=self.frontier(1)
        return f[0] if f else None
