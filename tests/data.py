import base
import model, yaml

problems = {
    'orthodox': model.makeSafe(yaml.load("""---
        algebraic:
          white: [Kc7, Qb2, Rg8, Sf2]
          black: [Kg2, Pg3, Pf4]
        stipulation: "#3"
        solution: |
          "1.Sf2-g4 + !
                1...Kg2-f1 {(g1)}
                    2.Rg8-a8 threat:
                            3.Ra8-a1 #
                1...Kg2-h3
                    2.Sg4-h2 !
                        2...g3*h2
                            3.Qb2-h8 #
                1...Kg2-h1
                    2.Qb2-h2 + !
                        2...g3*h2
                            3.Sg4-f2 #
                1...Kg2-f3
                    2.Qb2-c2 zugzwang.
                        2...g3-g2
                            3.Qc2-d3 #"
    """)),

    'switchbacks':  model.makeSafe(yaml.load("""
        {algebraic: {white: ["Ba1", "Bh1"]}, stipulation: "ser-~3",
        solution: "1.Ba1-h8 2.Bh8-a1 3.Ba1-h8 4.Bh8-a1" }
    """)),

    'c2c':  model.makeSafe(yaml.load("""
        {algebraic: {white: ["Ba1", "Bh1"]}, stipulation: "ser-~3",
        solution: "1.Ba1-h8" }
    """)),


}
