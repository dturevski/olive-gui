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
        algebraic: 
          white: [Ka1, Pg2, Pe2]
          black: [Kc1, Rc4, Bf4, Ba6, Sd5, Sb6, Pg3, Pf5, Pe5, Pe3, Pb3, Pa3]
        stipulation: "h#8"
        solution: |
          "1.Kc1-d2 Ka1-b1 2.Kd2-c3 Kb1-c1 3.Kc3-d4+ Kc1-d1 4.Kd4-e4 Kd1-e1 {
          } 5.Rc4-d4 Ke1-f1 6.Sb6-c4 Kf1-g1 7.Sc4-d2 Kg1-h1 8.Sd2-f3 g2*f3#"
    """)),

    'doublealbino':  model.makeSafe(yaml.load("""
        algebraic:
            white: [Kc6, Qb5, Rd1, Bb6, Ph2, Pg2, Pd2, Pb2]
            black: [Ke5, Qb4, Rb7, Ra6, Ba4, Sc5, Sc3, Ph3, Pf6, Pf3, Pe6, Pe3, Pb3]
        stipulation: "h#2"
        solution: |
            "1.Qb4-f4 g2-g4   2.Sc3-e4 d2-d4 #
            1.Ke5-d4 g2*f3   2.e6-e5 d2*c3 #
            1.Ke5-f4 g2*h3   2.Sc5-e4 d2*e3 #
            1.Ke5-e4 g2-g3   2.Sc5-d7 d2-d3 #"
    """)),

    'longtraceback':  model.makeSafe(yaml.load("""
        algebraic:
            white: [Ka6, Bb2]
            black: [Ka8, Qb3, Sc3, Pe5]
        stipulation: "h#9"
        solution: |
            "1.Qb3-b8 Ka6-a5   2.Ka8-b7 Bb2-a3   3.Kb7-c6 Ba3-d6   4.Kc6-d5 Bd6*b8  {
            } 5.Kd5-c4 Bb8-d6   6.Kc4-b3 Bd6-a3   7.Kb3-a2 Ka5-b4   8.Ka2-a1 Kb4-b3  {
            } 9.Sc3-b1 Ba3-b2 #"
    """)),

    'caillaudtempobishop':  model.makeSafe(yaml.load("""
        algebraic:
            white: [Kh1, Bh5, Be1, Pg6, Pg5, Pg4, Pf2, Pe3, Pc3]
            black: [Kh3, Ph4, Pg7, Pf3, Pe4, Pc6, Pc4, Pa7]
        stipulation: "h#9"
        solution:
            1.a7-a5 Be1-d2   2.a5-a4 Bd2-c1   3.a4-a3 Bc1-b2   4.a3-a2 Bb2-a3
            5.a2-a1=R + Ba3-c1   6.Ra1-a2 Kh1-g1   7.Ra2*f2 Bc1-d2   8.Kh3-g3 Bd2-e1
            9.h4-h3 Be1*f2 #"
    """)),

}
