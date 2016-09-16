# Preface
  * The goals
  * Predicate naming
  * Predicate arity and design. Priorities.
  * What's not covered

# Definitions

* **Board configuration** is an explicit description of the game state, including:
  * Board size and shape
  * Pieces nature and placement
  * Side to play
  * Castling and en passant rights
  * Fairy conditions in effect

* **Board alteration** is any action that alters the board configuration. Alterations include:
  * Chess moves, played by the rules in effect
  * Twinning actions
  * Null moves (which only alter the side to play)

* **Solution tree** is a directed rooted
  [tree](https://en.wikipedia.org/wiki/Tree_(graph_theory)), whose vertices are
  board configurations and edges are board alterations. The diagram position of the
  chess composition is the root of the tree. The final positions are the leaves of the tree.

* The **line of play** is a path from the root to the one of the leaves in the solution
  tree.

* A piece **visits** a square if it occupies the square in question
  1) in the initial position,
  2) after a completed move
  3) after a twinning.

  In other words, the visiting occurs in the position that is a vertex in the
  solution tree.

  *Examples:* Circe-reborn piece visits the rebirth square. Anti-Circe-reborn piece did not
  visit the capture square.

# Predicates

## Trajectories predicates

* `SwitchBack(PIECE visitor, INTEGER count)`

    In the single line of play the **visitor** visits **count** (>0) more squares
    (may be repeated) and returns to the starting square via the exact reverse route.

  *Example:*
  [SwitchBack(wR, 1)](http://yacpdb.org/#83447),
  [SwitchBack(wB, 3)](http://www.yacpdb.org/#412960)

* `RoundTrip(PIECE visitor, INTEGER count)`

    In the single line of play the **visitor** visits **count** (>2) different squares,
    and returns to the first square.
    The unsigned area encompassed by the path is non-zero.

    Equivalent definition: the circuit contains a sub-circuit that satisfies 2 criteria:
    1) All squares are different
    2) Squares geometrically do not all belong to the same
    [straight line](https://en.wikipedia.org/wiki/Line_(geometry)).

  *Example:*
  [RoundTrip(wB, 7)](http://www.yacpdb.org/#412003)

  Note that the *signed* area of the 8-shaped poligon in the example is zero,
  while the unsigned area is 4.


* `LinearClosedPath(PIECE visitor, INTEGER count)`

    The **visitor** performs  a closed path of length **count** in the single line of play
    that is neither `SwitchBack` nor `RoundTrip`.

* `PlaceExchange(INTEGER count)`

  **count** (>1) pieces cyclically exchange their places.

* `PlaceExchangeBy(PIECE participant)`

  The **participant** takes part in the `Exchange`.

* `Star(PIECE visitor)`

  The **visitor** visits each square from the set (related to the visitor's prior
  position) in different lines of play. The set is [(1, 1), (1, -1), (-1, 1), (-1, -1)].
  The visitor starting position does not have be its diagram position.

   *Example:* [Star(bK)](http://yacpdb.org/#49265)


* `BigStar(PIECE visitor)`

  Same as `Star`, the set is [(2, 2), (2, -2), (-2, 2), (-2, -2)]

* `Cross(PIECE visitor)`

  Same as `Star`, the set is [(0, 1), (0, -1), (-1, 0), (1, 0)]

* `BigCross(PIECE visitor)`

  Same as `Star`, the set is [(0, 2), (0, -2), (-2, 0), (2, 0)]

* `Wheel(PIECE visitor)`

  Same as `Star`, the set is [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]

* `PseudoAlbino(PIECE visitor)`

  Same as `Star`, the set is [(-1, -1), (1, -1), (0, -1), (0, -2)]. The visitor does not
  necessarily start from the 2nd rank.

  *Example*: [Albino(wP)](http://yacpdb.org/#44165)

* `PseudoPickaninny(PIECE visitor)`

  Same as `Star`, the set is [(-1, 1), (1, 1), (0, 1), (0, 2)]. The visitor does not
  necessarily start from the 7th rank.

* `CornerToCorner(PIECE visitor)`

   The **visitor** visits two different corner squares in a single line of play.

  *Example*: [CornerToCorner(wK)](http://yacpdb.org/#341021)

* `FourCorners(PIECE visitor)`

  The **visitor** visits (not necessarily in a single line of play) the squares a1, a8, h1 and
  h8

  *Example*: [FourCorners(wQ)](http://yacpdb.org/#297)


