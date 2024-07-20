---
DATE_CREATED: 2024-07-09
---
What's white's best move/line?

```chess
fen: 3rr3/5kpp/2b2n2/p3p3/P1NqPn2/1PQ5/1B4PP/2R2R1K w - - 0 1
```

<!-- divider -->

This has a tempting line found either by #Overloading (the pawn on d5) or by #Peek1 after `Qxd4 exd4` or #Peek2 `Qxd4 Rxd4 Bxd4 exd4` there is hanging knight capturable with `Rxf4`, gaining +3.

But can we do better?

* Nxe5+ Kg8 Nxc6 for +4
* `Nxe5+ Rxe5 Qxd4 Rxd4 Bxd4` and we're +3 with hanging R@e5, N@f4 and B@c6
* `Nxe5+ Qxe5 Qxe5 Rxe5 Bxe5` and we're +3 with hanging N@f4 and B@c6

## Review

It's another one of these complicated "guns pointing everywhere" situations (see also 005) where you must #Calculate for #MaximumDamage.