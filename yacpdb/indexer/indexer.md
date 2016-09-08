# Common definitions

* To **visit** a square: to occupy the square in question in initial position,
  after a completed move or after a twinning action.

  *Examples:* Circe-rebirth is visiting.
  The "Take" part of the Take&Make move is not visiting.

# Trajectories

* `Star(PIECE visitor)`

  The **visitor** visits each square from the set (related to visitor's prior position). [(1, 1), (1, -1), (-1, 1), (-1, -1)]


* `BigStar(PIECE visitor)`

  [(2, 2), (2, -2), (-2, 2), (-2, -2)]

* `Cross(PIECE visitor)`

  [(0, 1), (0, -1), (-1, 0), (1, 0)]

* `BigCross(PIECE visitor)`

  [(0, 2), (0, -2), (-2, 0), (2, 0)]

* `Wheel(PIECE visitor)`

  [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]

* `Albino(PIECE visitor)`

  [(-1, -1), (1, -1), (0, -1), (0, -2)]

* `Pickaninny(PIECE visitor)`

  [(-1, 1), (1, 1), (0, 1), (0, 2)]

* `RoundTrip(PIECE visitor, INTEGER count)`

    The **visitor** visits **count** (>2) different squares, and returns to the first square.
    The squares geometrically *do not* all belong to the same line.

* `LinearRoundTrip(PIECE visitor, INTEGER count)`

    Same as `RoundTrip`, but the squares *do* all belong to the same line.

* `SwitchBack(PIECE visitor, INTEGER count)`

  The **visitor** visits **count** (>0) more different squares and returns back via the same route.

* `Exchange(INTEGER count)`

  **count** (>1) pieces cyclically exchange their places.

* `ExchangeBy(PIECE participant)`

  The **participant** takes part in the `Exchange`.
