---
DATE_CREATED: 2024-07-03
---

I like searching for and collecting interesting ways to conceptualize chess. Perhaps this is a way to daydream instead of actually study, but...

I'd been using the term "piece blob" to refer to the types and arrangement of a side's pieces (mostly not considering the pawns, except where they protect a piece). Then, I'd try to find certain features of the piece blob that increased the chances a tactic existed. For example:

* hanging pieces - those without any protector
* "danger shapes" - pieces, pieces on a diagonal (vs. B,Q), on a line (vs. R,Q), and the various knight-forkable shapes
* law mobility pieces - susceptible to being trapped

Danial Naroditsky has a nice helper concept, the sorting of the pieces into three protection types:

* type 1 is completely undefended or Q
* type 2 is defended by single non-pawn piece
* type 3 is defended by pawn or multiple pieces

You might replace "type" with "safety", so safety 3 is highest and safety 1 is lowest. Type 1 pieces are the hanging pieces.

Of course the safety of a blob can't be fully determined without looking at the opponent's possibilities. The knight-forkable shapes aren't hazardous without a knight around.

Integrating opponent moves, I thought of:

* "chains" of protection (piece A protects piece B protects ... ), where, perhaps a defender can be removed earlier in the chain
* little counters on each piece, denoting how many more times they are defended than attacked - can the opponent make a move that makes some counter(s) negative without a reply returning them to zero?

And if a position contains none of these defects, look if any moves (perhaps a harmless exchange) might perturb or transform the position into one that does contain them.

By this point, the term "piece blob" growing into simply "position", we just have to consider the pawns as well.

Jan Markos has an interesting way to think of pawn structures, his "magnetic skin". He also says it could be like a space station, and the pieces are astronauts, which can be within the station (behind the pawns), on the surface of the station (protected by pawns), or on a space walk (dangerously away from the station).

