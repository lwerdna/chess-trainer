---
DATE_CREATED: 2024-07-09
---
What's white's best move/line?

```chess
fen: r4rk1/1bq2ppp/p1n2b2/1p6/3N1PQ1/3BB3/PPP3PP/R4R1K w - - 0 1
```

<!-- divider -->

The #MateThreat pattern generates three moves:

```chess
fen: r4rk1/1bq2ppp/p1n2b2/1p6/3N1PQ1/3BB3/PPP3PP/R4R1K w - - 0 1
squares: h5 h3 f5
arrows: d3->h7
```

And they are quickly checked:

* `Qh3 g6 (...h6)` and stuck
* `Qh5 g6 (...h6)` and stuck
* `Qf5 g6 Qxf6` winning a bishop!

# Review

Recognize #MateThreat, do a few depth 1, 1.5 calculations.