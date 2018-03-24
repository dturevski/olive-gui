# The YACPDB query language guide

[TOC]
## Synopsis
## Preface
### The goals
The main goal is to design and document a set of [predicates](https://en.wikipedia.org/wiki/Predicate_(mathematical_logic)) that partially describe the content of the chess compositions.

Key features to achieve:
* The predicates design should be as clear and unambigous as possible
* The predicates design should facilitate the database search

What this project is **not**:
* This project is not a tool for *extensive* description of the content of the chess composition
* This project does not have any relation to artistic or aestetic evaluation of the chess compositions
* This project is not not a revisiting of the existing chess problem terminology.


### Predicate naming, arity and design. Priorities.

When there is no consensus in the community regarding the exact definition of a certain term ("switchback" is one good example) it is preferred to choose a new name for predicate that was not used before in chess composition.

## Query language

### Informal definition

### Formal definition

#### Tokens
* INT - decimal non-negative integer literal
* TCS - alphanumeric string in TitleCase
* STR - utf8 string literal
* CMP - comparison operator: '>', '<', '='

#### Rules

The query language grammar defined in [Backus–Naur form](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form):

* Param := INT | STR
* ParamList := Param | Param, ParamList
* Predicate := TCS | TCS(ParamList)
* Expression := Predicate | Predicate CMP INT
* Expression := (Expression)
* Expression := NOT Expression
* Expression := Expression AND Expression
* Expression := Expression OR Expression

Logical operators precenence is NOT > AND > OR, i.e.:
* NOT A AND B = (NOT A) AND B
* A OR B AND C = A OR (B AND C)


### YACPDB implementation notes
* Wildcard character is `*` (asteriks)
* `Predicate` is a shorthand for `Predicate > 0`
* String literals may be 'single quoted' or "double quoted", they may not include a single or a double quote character respectively. String literals that include both single and double quote are not supported. In simple cases a string literal may be accepted without quotes.
* For a 0-nary predicate the only supported syntax is `PredicateName`, using `PredicateName()` would yield an error

## Definitions

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

* **Solution tree** is a directed rooted [tree](https://en.wikipedia.org/wiki/Tree_(graph_theory)), whose vertices are board configurations and edges are board alterations. The diagram position of the chess composition (except for retros) is the root of the tree. The final positions are the leaves of the tree.

  *TODO: Retros*

* The **line of play** is a path from the root to the one of the leaves in the solution tree.

* A piece **visits** a square if it occupies the square in question
  1) in the initial position,
  2) after a completed move
  3) after a twinning.

  In other words, the visiting occurs in the position that is a vertex in the solution tree.

  *Examples:* Circe-reborn piece visits the rebirth square. Anti-Circe-reborn piece did not
  visit the capture square.

## Predicate parameter domains
(ordered alphabetically)
* **ACTIVITYFLAG**: "Active" or "Passive"
* **CAPTUREFLAG**: "WithCaptures" or "Captureless"
* **COLOR**: a single character 'w', 'b' or 'n' for white, black and neutral, respectively
* **DATE**: a date in YYYY[-MM[-DD]] format
* **INTEGER**: any integer number
* **PIECE**: concatenation of COLOR and PIECENAME
* **PIECENAME**: one- or two-letter piece code, as defined by the [Popeye](https://github.com/thomas-maeder/popeye) solving software (english input)
* **STRING**: unicode character string

## Predicates

### Metadata predicates

Same meaning as in the YACPDB search form. Metadata predicates do not involve analysis of the solution.

* `Matrix(STRING piecelist)`

	The relative position of the pieces matches that of the **piecelist**
    Fairy pieces are ok, e.g. `Matrix("wKa1 nNHh8")` (nNH = neutral nightrider-hopper)

* `Id`

    YACPDB problem id satisfies (is equal, less or greater than) the constraint.
    Use `Id=X or Id=Y or Id=Z` to hotlink to an arbitrary set of problems.

* `Author(STRING name)`

	Meaning that at least one of the authors matches **name**

* `Source(STRING name)`
* `SourceId(STRING sourceid)`
* `IssueId(STRING issueid)`
* `PublishedAfter(DATE date)`
* `Stip(STRING regex)`
* `Option(STRING option)`

	`Option(*) = 0` for no options / fairy conditions.

* `Keyword(STRING keyword)`
* `PCount(COLOR color)`

    Number of pieces of the specified **color** matches the constraint
    Use `PCount(*)` to constraint the total number of pieces.

* `With(STRING pieces)`
    
    The diagram position contains the listed pieces.
    
    *Example:* [With("wR wR wR")](http://yacpdb.org/#36411) - three or or more white rooks on board.

* `Fairy`

    There are fairy pieces or conditions in the titular (diagram) twin. No constraint on
    stipulation and non-titular twins.

### Trajectories predicates


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
    2) Do not all belong to the same [straight line](https://en.wikipedia.org/wiki/Line_(geometry)).

    *Example:*
    [ArealCycle(wB, 7, WithCaptures)](http://www.yacpdb.org/#412003)

    Note that the *signed* area of the 8-shaped polygon in the example is zero,
    while the unsigned area is 4.


* `LinearCycle(PIECE visitor, INTEGER length, CAPTUREFLAG cflag)`

    Same as `ArealCycle`, but the squares all lie on the same straight line.

    *Example*: [ClosedWalk(wB, 7, Captureless) +
    LinearCycle(wB, 3, Captureless)](http://www.yacpdb.org/#86606)

* `PlaceExchange(INTEGER count)`

  **count** (>1) pieces cyclically exchange their places.

* `PlaceExchangeBy(PIECE participant)`

  The **participant** takes part in the `PlaceExchange`.

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

  *Example*: [PseudoAlbino(wP)](http://yacpdb.org/#44165)

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

* `Excelsior(PIECE promotion, INTEGER length)`
  
    A black or white pawn-like piece (pawn, berolina, superpawn) makes **length** moves and promotes into **promotion**.


### Miscellaneous predicates with fairy support


* `Phases`

   How many there are distinct first moves in the solution (actual or null-moves for setplay, but not twins).
   
* `Twins`

   How many there are twins (a problem without twins has `Twins = 1`).
   
   *Example*: [Twins = 27](http://yacpdb.org/#435307)

* `ZilahiPiece(PIECE actor, ACTIVITYFLAG flag)`

   In one line of play **actor** is making the final move. In another line of play this piece
   is captured. Depending on whether it is captured on its initial square or elsewhere, activity **flag**
   is either Passive or Active.
   
   *Example*: [ZilahiPiece(wR, Passive)](http://yacpdb.org/#88498)

* `Zilahi(INTEGER folds)`

   **folds** (>1) lines of play are connected in a circular way with `ZilahiPiece`s.

   *Example*: [Zilahi(5)](http://yacpdb.org/#45243)

* `Valladao(PIECE promotion, INTEGER length)`

### Twomover change patterns

Applicable to direct/self/reflex/semi-reflex play problems in two moves. In this section the two moves are considered
the same and labeled with one letter if they have identical
* Departure/arrival squares
* Departure/arrival piece types
* Departing piece origin square (including twin id, if the piece originated in twin by replacing another piece)

Other properties of the move are ignored (capture, rebirths, imitator moves etc).

### Orthodox


### Helpmate Analyzer predicates

These are only applicable to orthodox helpmates

* `HundredDollar`

   HMA: _100-Dollar theme_
    
   A solution in 5 moves contains a white Excelsior and a black Excelsior with Knight promotions.