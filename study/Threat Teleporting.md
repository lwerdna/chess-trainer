---
DATE_CREATED: 2024-07-03
---

Often it would be useful to have a piece able to make more than one move to get to a needed position. Often it can, if the intermediate moves pose huge threats.

Here, the bishop at d7 is type 2 defended, and if a piece were available to remove the defender (the knight on c5), we'd have a simple #RemoveTheDefender tactic.

<!-- problem0 guid=ecc3303f-ed02-4b15-98af-b74e84826d84 -->
What's white's best move/line?

```chess
fen: r4rk1/pp1b1pbp/1q2p1p1/2n3B1/1nP5/2N2N1P/PP3PP1/R2QRBK1 w - - 2 16
```
<!-- problem1 -->
<details>
<summary>Solution</summary>
Black's pieceblob has a type 2 defended piece, so we can #RemoveTheDefender by playing a #TeleportWithThreat move:
<br>

Could the knight work? 1.Na4 Nxa4 2.Qxd7 is ok but then simply 2...Nc5.

Could the bishop work? Yes 1.Be7 Rc8 2.Bxc5 Qxc5 3.Qxd7

```chess
fen: r4rk1/pp1b1pbp/1q2p1p1/2n3B1/1nP5/2N2N1P/PP3PP1/R2QRBK1 w - - 2 16
arrows: c5->d7
moves: Be7 Rfe8 Bxc5 Qxc5 Qxd7
```
</details>
<br>
<!-- problem2 -->

Here, the bishop on c7 is pinned, but nothing is available to attack the pin. Except the bishop can teleport to e6 with a threat, another instance of the bishop bouncing off a rook on f8.

<!-- problem0 guid=1a8b226c-eb44-4bae-b69e-eece6eb5cd7b -->
What's white's best move/line?
<br>

```chess
fen: r1q2rk1/ppbn1ppp/4p3/3pP1Bb/3P4/5N1P/PP2BPP1/2RQ1RK1 w - - 0 1
```
<!-- problem1 -->
<details>
<summary>Solution</summary>
1.Be7 Re8 2.Bd6
Tags: #ThreatTeleporting #Pin.Attack
</details>
<br>
<!-- problem2 -->