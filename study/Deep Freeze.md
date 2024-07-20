---
DATE_CREATED: 2024-07-03
---

### deep freeze

Capablanca called this "one pawn holds two", in Silman's Complete Endgame Course it's called the "deep freeze":

```chess
fen: 8/8/6p1/7p/7P/8/8/K1k5 b - - 0 1
moves: g5 hxg5 h4 g6 h3 g7 h2 g8=Q h1=Q
```

Note it doesn't work if the freezing pawn isn't at least on the 4th rank. For example, on the 3rd disaster happens:

```chess
fen: 8/8/8/6p1/7p/7P/8/K1k5 b - - 0 1
moves: g4 hxg4 h3 g5 h2 g6 h1=Q g7
```

It's interesting that black wins the race by two more than the previous example, due to him being closer by 1 and white being further away by 1.

If the freeze is available and is not taken, you could lose. If white plays a5 (freezing) he wins, else he draws:

```chess
fen: 8/1p6/p6k/7P/P6K/8/8/8 w - - 0 1
moves: Kg4 b5
```

There're also attributes of the deep freeze for larger groups of pawns. Here, two pawns might freeze three:

```chess
fen: 8/5pp1/p6p/P1k5/2P3PP/2K5/8/8 w - - 0 1
moves: h5 g6 g5
```

And if hxg5 then g6 and if gxh5 gxh6