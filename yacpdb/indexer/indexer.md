# Preface
## The goals
The main goal is to design and document a set of [predicates]()
that partially describe the content of the chess compositions.

Key features to achieve:
* The predicates desing should be as clear and unambigous as possible
* The predicates desing should facilitate the database search

What this project is **not**:
* This project is not a tool for *extensive* description of the content of the chess composition
* This project does not have any relation to artistic or aestetic evaluation of the chess compositions
* This project is not intended to substitute (or have any major impact on) the existing
  chess problem terminology.


## Predicate naming, arity and design. Priorities.

When there is no consensus in the community regarding the exact definition of a certain
term ("switchback" is one good example) it is preferred to choose a new name for predicate
that was not used before in chess composition.


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

# Predicate parameters domains
(ordered alphabetically)
* **CAPTUREFLAG**: "WithCaptures" or "Captureless"
* **COLOR**: a single character 'w', 'b' or 'n' for white, black and neutral, respectively
* **INTEGER**: any integer number
* **PIECE**: concatenation of COLOR and PIECENAME
* **PIECENAME**: one- or two-letter piece code, as defined by the
  [Popeye](https://github.com/thomas-maeder/popeye)
  solving software (english input)

# Predicates

## Trajectories predicates


* `ClosedWalk(PIECE visitor, INTEGER length, CAPTUREFLAG cflag)`

    In the single line of play the **visitor** changes the visited square **length**
    (>1) times (squares may be repeated) and returns to the starting square.

* `TraceBack(PIECE visitor, INTEGER count, CAPTUREFLAG cflag)`

    Is a special case of `ClosedWalk` where visitor returns to the starting square via the
    exact reverse route. The **count** is half the length of the walk.

  *Example:* [TraceBack(wR, 1, WithCaptures)](http://yacpdb.org/#83447)

  *Example:* [TraceBack(wB, 3, WithCaptures)](http://www.yacpdb.org/#412960)

* `ArealCycle(PIECE visitor, INTEGER length, CAPTUREFLAG cflag)`

    Is a special case of `ClosedWalk` where visited squares:
    1) Are all different
    2) Do not all belong to the same
    [straight line](https://en.wikipedia.org/wiki/Line_(geometry)).

    *Example:*
    [ArealCycle(wB, 7, WithCaptures)](http://www.yacpdb.org/#412003)

    Note that the *signed* area of the 8-shaped poligon in the example is zero,
    while the unsigned area is 4.


* `LinearCycle(PIECE visitor, INTEGER length, CAPTUREFLAG cflag)`

    Same as `ArealCycle`, but the squares all lie on the same straight line.

    *Example*: [ClosedWalk(wB, 7, CaptureLess) +
    LinearCycle(wB, 3, CaptureLess)](http://www.yacpdb.org/#86606)

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


