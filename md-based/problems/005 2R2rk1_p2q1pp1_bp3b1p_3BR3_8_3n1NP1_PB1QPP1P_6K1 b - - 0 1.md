---
DATE_CREATED: 2024-07-09
---
What's black's best move/line?

```chess
fen: 2R2rk1/p2q1pp1/bp3b1p/3BR3/8/3n1NP1/PB1QPP1P/6K1 b - - 0 1
orientation: black
```

<!-- divider -->

`Rxc8 exd3 Bxe5 Bxe5 Qxd5`

## Review

I am not good at these types of positions. There are six captures I can make: Bxe5, Nxe5, Qxd5, Nxb2, Qxc8, Bxc8.

Try calculation...

* `Qxd5 Rxd5` and no killer move to follow
* `Qxc8 exd3 Bxe5 Bxe5` and gained two exchanges (+4)
* `Bxc8 Qxd3 Bxe5 Bxe5` and gained two exchanges (+4)
* `Rxc8 exd3 Bxe5 Bxe5` and gained two exchanges (+4)
* `Bxe5 Rxf8+ Kxf8 dxe3` and I gained one exchange (+2)
* `Nxe5 Rxf8+ Kxf8 Nxe5 Bxe5 Bxe5` and I gained one exchange (+2)

It feels like the +4 variations are interchangeable. What did I miss?

A helpful user writes to focus on the bishop in the center of the board. If it can be captured, the line beats the others. So it was an calculation error, of the insufficient depth variety, because at the end of the `Rxc8` line, there's simply Qxd5. I calculated 2 instead of 2.5.

It's one of these complicated "guns pointing everywhere" situations where you must #Calculate for #MaximumDamage.

