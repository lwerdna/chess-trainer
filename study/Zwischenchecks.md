---
DATE_CREATED: 2024-07-03
---

Zwischenzug (in-between moves) that are checks can be called Zwischenchecks!

Scenario "A": The opponent's position has a defended piece whose capture is a check (ingredient #1). You #RemoveTheDefender by distracting it with a trade (ingredient #2), but #Zwischenzug with check before completing the trade.

## Example

```chess
fen: 4r1k1/pp2qppp/2nQ4/2n5/2N3P1/4P2P/PP2P1B1/3R2K1 b - - 0 1
orientation: black
```

This is a harder case because ingredient #2 is already set up (the Q@d6 is distracted with a trade). Now the you insert ingredient #1, #Xray attacking R@d1 whose capture is a check. 

1.Rd8 Qxe7 (1...Qxd8 2.Nxd8) 2.Rxd1+ Kf2 3.Nxe7

From: https://chesstempo.com/chess-tactics/70740678

## Example

```chess
fen: 6k1/p2q1p2/1p4p1/2p4p/P7/1PQ3PP/2P1rP2/4R1K1 b - - 0 1
orientation: black
moves: Qd4 Qxd4 Rxe1+ Kg2 cxd4
```

Ingredient #1 is Rxe1+. The defender is the Q@c3 which can be distracted with Qd4.

1...Qd4 2.Qxd4 Rxe1+ 3.Kg2 cxd4

From: (some chesstempo problem)

## Example

```chess
fen: 3r4/1p3pkp/2b3p1/p2N3r/P1P2P2/1P6/6PP/3RR1K1 w - - 0 1
moves: Nf6 Rxd1 Nxh5+ gxh5 Rxd1
```

This is not scenario "A". Nf6 is a #DiscoveredAttack on the R@d8, but the Rxd1 Rxd1 trade is interrupted by Nxh5+.

1.Nf6 Rxf6 (1...Kxf6 2.Rxd8) 2.Nxh5+ gxh5 3.Rxd1

## Example

```chess
fen: 2kr2r1/pp1n4/3p1pqp/2p1p3/3bPP2/PP1PB1PN/4Q2P/2R2RK1 b - - 0 1
orientation: black
moves: Qg4 Qxg4 Bxe3+ Kh1 Rxg4
```

This is a pure example of scenario "A". The queen is defending the B@e3, whose capture would be a check. The queen can be "trade distracted" by Qg4.
