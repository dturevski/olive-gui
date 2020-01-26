# The YACPDB entry format

[TOC]

## Overview

The YACPDB entry is a YAML document that should satisfy this JSON schema:
[yacpdb-entry.schema.json](./yacpdb-entry.schema.json)

* What is [YAML](http://en.wikipedia.org/wiki/YAML)
* What is [JSON schema](https://json-schema.org/)

A typical YACPDB entry may look like this:
```yaml
    ---
    authors: 
      - Ugren, Ljubomir
      - Abdurahmanović, Fadil
    source: 
      name: feenschach
      issue: 01-02
      problemid: 7100
      date:
        year: 1965 
    award:
      tourney:
        name: feenschach
      distinction: 1st Prize
    algebraic: 
      white: [Kh1, Re4, Pg2, Pf5, Pf4, Pf3, Pe6, Pc4]
      black: [Kd1, Bc3, Ph2, Pg3, Pf6, Pe7, Pd3, Pd2, Pc5]
    stipulation: h#4
    options: 
      - SetPlay
    solution: |
      "1...Re4-d4 2.Kd1-e2 Rd4-d5 3.Ke2-e3 Rd5-e5 + 4.Ke3-d4 Re5-e4 #       
      1.Bc3-d4 Re4-e5 2.Bd4-f2 Re5-d5 3.Kd1-e2 Rd5-d4 4.Ke2-e3 Rd4-e4 #"
    keywords:
      - Rundlauf
    reprints:
      - 
        name: FIDE Album
        date:
          year: 1965-1967
        problemid: 587
    foreignids:
      -
        domain: PDB
        problemid: P0503887
```

## Fields

### authors:
```yaml
    authors: 
      - Ugren, Ljubomir
      - Abdurahmanović, Fadil
```
This is a list of people who authored this composition. Each name should follow this
pattern: "Family name, Given names". If the authorship is unknown
this field may be omitted, usage of the names like "Unknown" and
"Anonymous" should be avoided. 

### source:
This is a collection of fields that reference the exact original publication source
of the composition. May be omitted if the source is unknown.
```yaml
    name: Source name as on the cover
    volume: 2 # in case of multi volume publication
    issue: 01-02
    round: 3C # applicable if the source is actually a solving competition event
    problemid: H1234
    pagenumber: 65
    date:
      year: 1965 # or alternatively a span of years, eg: "1965-1967"
      month: 2 # optional
      day: 21 # also optional, but if present, the month is required
```

### award:
This field indicates that composition took part in a certain composing competition
and earned a certain distinction. If the `award` fiels is present the `source` field is required.
```yaml
    tourney:
        name: feenschach
        date: # optionally the date of the tourney may be specified in the same format
            year: ... # if meaningfully different from the source date
    distinction: 1st Prize
    judges:
      - Páros, György
```

### algebraic:
```yaml
    white: [Ka1, Sa2, Pag7]                   # white pao (chinese rook) g7
    black: [Royal Zf3, Qh8]                   # black royal zebra (2,3-leaper) f3
    neutral: [Pa2, HurdleColourChanging Ga5]  # neutral grasshopper at a5 that changes  
                                              # the color of the piece it hops over	
```
The diagram position of the composition.
Note S for the knights as N is reserverd forthe  Nightriders. Fairy pieces are
supported and use the same syntax as in the Popeye solving program:

[Popeye manual](https://github.com/thomas-maeder/popeye/blob/master/py-engl.txt)

For convenience the lists of the supported fairy pieces, specifications and conditions
are available at the edit form via the `Insert' pulldown menu.

### stipulation:
```yaml
    stipulation: h#4
```
The stipulation of the composition. Most Popeye stipulations can be entered here, also 
`"PGXX(.5)"` for proofgames, `"=", "+", "= black to move", "+ black to move"` for endgame
studies and `"see text"` for non-standard stipulations.

### options:
```yaml
    - SetPlay
    - Defence 1
    - AntiCirce
```
The list of applicable options and conditions in Popeye format. `Defence 1`, for example,
indicates that the tries are the part of the author's concept. `AntiCirce` is a fairy chess
rule.

### twins:
Twins use the Popeye syntax as well, with a little difference: in case of Zero-positions 
first twin must be labeled `a`, the second - `b` etc, and in case of normal twins the first
is `b`, the second - `c` and so on. Please note that Popeye is aware of the fairy pieces,
so it is `Add white Sa1`, not `Add white Na1` to add a white knight. 
```yaml
    twins:
      b: Move a1 a2
      c: Continued Exchange a2 h7 # "Continued" means that the transformation is applied
                                  # to the position of the previous twin, not to the diagram position
```


### intended-solutions:
```yaml
    intended-solutions: 3
    intended-solutions: 2.2.1.1
    intended-solutions: 4.1.1...
```
When author intended more than one solution to his problem, this can be indicated 
using one of these three example formats.


### solution:
The solution to the problem in the Popeye output format with optional comments in curly braces
```yaml
    solution: |
      "1...Re4-d4 2.Kd1-e2 Rd4-d5 3.Ke2-e3 Rd5-e5 + 4.Ke3-d4 Re5-e4 # {e4-d4-d5-e5-e4}      
      1.Bc3-d4 Re4-e5 2.Bd4-f2 Re5-d5 3.Kd1-e2 Rd5-d4 4.Ke2-e3 Rd4-e4 # {e4-e5-d5-d4-e4}"
```
Note the YAML pipe symbol `|` for a block of text.

### keywords:
A list of applicable keywords:
```yaml
  - Zilahi
  - Model mates
```
There are two special or "system" keywords:
* `Attention` - to make other users know that there's something wrong with this problem,
but you don't know how to fix it.
* `To delete` - to make administrator know that this problem needs to be
deleted from the database.
Use comments field to give more details.

### comments:
A list of comments with the information that does not fit into the other fields.
```yaml
  - Published under the pseudonym "T.P.C., of New York"
  - See also >>345346
```

### reprints:
`reprints` is the list of the secondary sources and follow the same semantics as the `source` field.
Additionally, two more nested fields could be specified - `variant` and `comments`.
The `variant` field follows the same Popeye twins syntax and indicates that a modified position
was used. `comments` are comments only applicable to this reprint.
```yaml
reprints: 
  - 
    name: Czech Chess Solving Championship
    issue: 27
    date:
      year: 2019
      month: 7
      day: 13
    round: 1
    problemid: C
    variant: Mirror a1 <--> h1 Move g6 f4 
    comments:
      - |
        The solvers were presented with a mirrored position with the white pawn g6 moved to f4,
        effectively swapping the key and the try
```

### foreignids
This field is used to cross-reference other problem collections.
```yaml
    foreignids:
      - domain: PDB
        problemid: P0503887
      - domain: WinChloe
        problemid: 123456
```