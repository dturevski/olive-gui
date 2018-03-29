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

    'pw':  model.makeSafe(yaml.load("""
        {algebraic: {neutral: ["Qa8", "Qa7", "Qb7"]}, stipulation: "ser-h~4",
        solution: "1.nQa7-b8 nQa8-a7 2.nQb7-a8 nQb8-b7" }
    """)),

    'pw2':  model.makeSafe(yaml.load("""
        algebraic: 
          white: [Kh8, Rg8, Bc6, Pe5]
          black: [Ke7, Pe6, Pc7]
        stipulation: "#4"
        solution: |
          "1.Kh8-h7 ! zugzwang.
                1...Ke7-f7 
                    2.Rg8-h8 zugzwang.
                        2...Kf7-e7 
                            3.Kh7-g8 zugzwang.
                                3...Ke7-d8 
                                    4.Kg8-f7 #"
    """)),

    'twinssetplay':  model.makeSafe(yaml.load("""
        algebraic: 
          white: [Kh1, Rh4, Rc1]
          black: [Kd2, Pe3, Pe2]
        stipulation: "h#2"
        options: 
          - SetPlay
        twins: 
          b: Move h4 g1
          c: Move h4 h3
        solution: |
          "a) 1...Rc1-c4   2.Kd2-d3 Rh4-d4 #          
          1.e2-e1=S Rh4-c4   2.Se1-d3 Rc4-c2 #          
          b) wRh4-->g1 1.e2-e1=R Rg1-f1   2.Re1-e2 Rf1-d1 #          
          c) wRh4-->h3 1.e2-e1=B Rc1-c3   2.e3-e2 Rh3-d3 #"
    """)),

    'z2x1':  model.makeSafe(yaml.load("""
        algebraic: 
          white: [Ka6, Rh1, Re6, Bh7, Sh5, Pd3]
          black: [Kg2, Qg1, Rh6, Ph2]
        stipulation: "h#2"
        solution: |
          "1.Rh6*h5 Re6-e1   2.Kg2*h1 Bh7-e4 #
          1.Rh6*h7 Re6-e2 +   2.Kg2-f1 Sh5-g3 #"
    """)),

    'z5x1':  model.makeSafe(yaml.load("""
        algebraic: 
          white: [Kb2, Rb7, Be5, Bb3, Sf3, Sd3]
          black: [Kc6, Re3, Sa5, Pf6, Pe4, Pa6]
        stipulation: "h#2"
        solution: |
          "1.Re3*f3 Bb3-d1   2.e4-e3 Bd1*f3 # 
            1.e4*d3 Rb7-b6 +   2.Kc6-c5 Be5-d4 # 
            1.Sa5*b3 Rb7-c7 +   2.Kc6-d5 Sd3-f4 # 
            1.Sa5*b7 Be5-c7   2.Kc6-b5 Sf3-d4 # 
            1.f6*e5 Sf3*e5 +   2.Kc6-d6 Rb7-d7 #"
    """)),

    'z3x2':  model.makeSafe(yaml.load("""
        algebraic: 
          white: [Ke3, Rb4, Ba6, Sa3, Ph3]
          black: [Kf5, Rc4, Bb7, Bb2, Sa2, Ph4, Ph2, Pg7, Pg2, Pd7, Pc3]
        stipulation: "h#2"
        options: 
          - Take&MakeChess
        solution: |
          "1.Sa2*b4-b5 Sa3*c4-e4   2.Kf5*e4-g3 Ba6*b5-d6 #
          1.Bb2*a3-b1 Ba6*c4-f4   2.Kf5*f4-g3 Rb4*b1-g6 #
          1.Bb7*a6-b5 Rb4*c4-g4   2.Kf5*g4-g3 Sa3*b5-e2 #"
    """)),

    'z3x2-ortho':  model.makeSafe(yaml.load("""
        algebraic: 
          white: [Ka3, Rb7, Ra5, Bd2, Ba2, Sd4, Pg5, Pf4, Pd5, Pb5, Pa6]
          black: [Kd6, Qc3, Rc2, Ra1, Sc1, Sb3, Pg6, Pf6, Pc5, Pa4]
        stipulation: "h#2"
        solution: |
          "1.Qc3*d2 b5-b6 {(a7?)} 2.Sb3*a5 Sd4-b5 #
          1.Qc3*d4 a6-a7 {(f5?)} 2.Sb3*d2 Ra5-a6 #
          1.Qc3*a5 f4-f5 {(b6?)} 2.Sb3*d4 Bd2-f4 #"
    """)),


    'fox':  model.makeSafe(yaml.load("""
        algebraic: 
          white: [Ke1, Ra5, Bg5, Se2, Pf2]
          black: [Ke4, Bd8, Sg4, Pg6, Pe6, Pb4]
        stipulation: "h#2"
        twins: 
          b: Remove b4
        solution: |
          "a) 1.Bd8*a5 f2-f4   2.Ke4-f5 Se2-g3 #          
          b) -bPb4 1.Bd8*g5 f2-f3 +   2.Ke4-e3 Ra5-a3 #"
    """)),
}
