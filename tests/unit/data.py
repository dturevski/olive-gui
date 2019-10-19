import base
import model, yaml

problems = {
    'orthodox': model.makeSafe(yaml.safe_load("""---
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

    'switchbacks':  model.makeSafe(yaml.safe_load("""
        {algebraic: {white: ["Ba1", "Bh1"]}, stipulation: "ser-~3",
        solution: "1.Ba1-h8 2.Bh8-a1 3.Ba1-h8 4.Bh8-a1" }
    """)),

    'c2c':  model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Ka1, Pg2, Pe2]
          black: [Kc1, Rc4, Bf4, Ba6, Sd5, Sb6, Pg3, Pf5, Pe5, Pe3, Pb3, Pa3]
        stipulation: "h#8"
        solution: |
          "1.Kc1-d2 Ka1-b1 2.Kd2-c3 Kb1-c1 3.Kc3-d4+ Kc1-d1 4.Kd4-e4 Kd1-e1 {
          } 5.Rc4-d4 Ke1-f1 6.Sb6-c4 Kf1-g1 7.Sc4-d2 Kg1-h1 8.Sd2-f3 g2*f3#"
    """)),

    'doublealbino':  model.makeSafe(yaml.safe_load("""
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

    'longtraceback':  model.makeSafe(yaml.safe_load("""
        algebraic:
            white: [Ka6, Bb2]
            black: [Ka8, Qb3, Sc3, Pe5]
        stipulation: "h#9"
        solution: |
            "1.Qb3-b8 Ka6-a5   2.Ka8-b7 Bb2-a3   3.Kb7-c6 Ba3-d6   4.Kc6-d5 Bd6*b8  {
            } 5.Kd5-c4 Bb8-d6   6.Kc4-b3 Bd6-a3   7.Kb3-a2 Ka5-b4   8.Ka2-a1 Kb4-b3  {
            } 9.Sc3-b1 Ba3-b2 #"
    """)),

    'caillaudtempobishop':  model.makeSafe(yaml.safe_load("""
        algebraic:
            white: [Kh1, Bh5, Be1, Pg6, Pg5, Pg4, Pf2, Pe3, Pc3]
            black: [Kh3, Ph4, Pg7, Pf3, Pe4, Pc6, Pc4, Pa7]
        stipulation: "h#9"
        solution:
            1.a7-a5 Be1-d2   2.a5-a4 Bd2-c1   3.a4-a3 Bc1-b2   4.a3-a2 Bb2-a3
            5.a2-a1=R + Ba3-c1   6.Ra1-a2 Kh1-g1   7.Ra2*f2 Bc1-d2   8.Kh3-g3 Bd2-e1
            9.h4-h3 Be1*f2 #"
    """)),

    'pw':  model.makeSafe(yaml.safe_load("""
        {algebraic: {neutral: ["Qa8", "Qa7", "Qb7"]}, stipulation: "ser-h~4",
        solution: "1.nQa7-b8 nQa8-a7 2.nQb7-a8 nQb8-b7" }
    """)),

    'pw2':  model.makeSafe(yaml.safe_load("""
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

    'twinssetplay':  model.makeSafe(yaml.safe_load("""
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

    'z2x1':  model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Ka6, Rh1, Re6, Bh7, Sh5, Pd3]
          black: [Kg2, Qg1, Rh6, Ph2]
        stipulation: "h#2"
        solution: |
          "1.Rh6*h5 Re6-e1   2.Kg2*h1 Bh7-e4 #
          1.Rh6*h7 Re6-e2 +   2.Kg2-f1 Sh5-g3 #"
    """)),

    'z5x1':  model.makeSafe(yaml.safe_load("""
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

    'z3x2':  model.makeSafe(yaml.safe_load("""
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

    'z3x2-ortho':  model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Ka3, Rb7, Ra5, Bd2, Ba2, Sd4, Pg5, Pf4, Pd5, Pb5, Pa6]
          black: [Kd6, Qc3, Rc2, Ra1, Sc1, Sb3, Pg6, Pf6, Pc5, Pa4]
        stipulation: "h#2"
        solution: |
          "1.Qc3*d2 b5-b6 {(a7?)} 2.Sb3*a5 Sd4-b5 #
          1.Qc3*d4 a6-a7 {(f5?)} 2.Sb3*d2 Ra5-a6 #
          1.Qc3*a5 f4-f5 {(b6?)} 2.Sb3*d4 Bd2-f4 #"
    """)),

    '1234':  model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Ke2, Qh1, Sd5, Pe6]
          black: [Ke8, Rh8, Sh7]
        stipulation: "#2"
        solution: |
          "1...Sh7-g5
                  2.Qh1*h8 #
          
           1.Qh1-a1 ! threat:
                  2.Qa1-a8 #
              1...Ke8-d8
                  2.Qa1-a8 #
              1...0-0
                  2.Sd5-e7 #
              1...Ke8-f8
                  2.Qa1*h8 #"
    """)),



    'complextwin':  model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Kg1, Qc7, Rf5, Rf3, Bc8, Bc1, Sg5, Sd6, Pc5, Pb3, Pb2]
          black: [Kd4, Rb8, Bh1, Bf4, Sg7, Sg6, Pg3, Pe7, Pd5, Pd3, Pa3]
        stipulation: "#2"
        twins: 
          b: Move g1 a1 move e7 b4
        solution: |
          "a)
              1.Bc8-e6 ! threat:
                    2.Rf5*d5 # 
                1...Sg6-e5  {(A)} 2.Rf5*f4 # 
                1...Bh1*f3  {(B)} 2.Sg5*f3 # 
                1...Sg7*f5  {(C)} 2.Sd6*f5 # 
                1...a3*b2   {(D)} 2.Bc1*b2 # 
                1...Bf4-e3 +{(E)} 2.Bc1*e3 # 
          
          b) wKg1-->a1  bPe7-->b4
          
            1.Bc8-a6 ! threat:
                    2.Rf3*d3 # 
                1...Sg6-e5  {(B)} 2.Rf5*f4 # 
                1...Bh1*f3  {(C)} 2.Sg5*f3 # 
                1...Sg7*f5  {(D)} 2.Sd6*f5 # 
                1...a3*b2 + {(E)} 2.Bc1*b2 # 
                1...Bf4-e3  {(A)} 2.Bc1*e3 #"
    """)),

    'valladao':  model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Ke1, Qc1, Rh8, Rh1, Bh3, Ba1, Sd1, Sb5, Pg7, Pg6, Pg5, Pd2, Pc7, Pc2]
          black: [Ke7, Rh7, Be8, Ph4, Pf7, Pd5, Pb2, Pa3, Pa2]
        stipulation: "#2"
        options: 
          - SetPlay
        solution: |
          "1...b2-b1=Q
                 2.Ba1-f6 #
             1...b2-b1=S
                 2.Ba1-f6 #
             1...b2-b1=R
                 2.Ba1-f6 #
             1...b2-b1=B
                 2.Qc1*a3 #
                 2.Ba1-f6 #
             1...b2*c1=Q
                 2.Ba1-f6 #
             1...b2*c1=S
                 2.Ba1-f6 #
             1...b2*c1=R
                 2.Ba1-f6 #
             1...b2*c1=B
                 2.Ba1-f6 #
             1...b2*a1=Q
                 2.Qc1*a3 #
             1...b2*a1=S
                 2.Qc1*a3 #
             1...b2*a1=R
                 2.Qc1*a3 #
             1...b2*a1=B
                 2.Qc1*a3 #
             1...Be8*b5
                 2.c7-c8=S #
             1...Be8-c6
                 2.c7-c8=S #
          1.0-0 ! threat:
                 2.Rf1-e1 #
             1...b2*c1=S
                 2.Ba1-f6 #
             1...b2*a1=Q
                 2.Qc1*a3 #
             1...b2*a1=B
                 2.Qc1*a3 #
             1...f7-f5
                 2.g5*f6 ep. #
             1...f7*g6
                 2.g7-g8=S #
             1...Be8*b5
                 2.c7-c8=S #
             1...Be8-d7
                 2.Rf1*f7 #"
    """)),

    'fox':  model.makeSafe(yaml.safe_load("""
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

    '623':  model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Ke5, Ph7, Pb7]
          black: [Ke8]
        stipulation: "#2"
        solution: |
          "1.Ke5-e6 ! threat:
                 2.h7-h8=Q #
                 2.h7-h8=R #
                 2.b7-b8=Q #
                 2.b7-b8=R #
             1...Ke8-d8
                 2.b7-b8=Q #
             1...Ke8-f8
                 2.h7-h8=Q #"
    """)),

    'z22':  model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Ka2, Rh1, Bg8, Sf6, Sd4, Pe6]
          black: [Ke5, Qc8, Re8, Bd6, Bb5, Sg7, Ph5, Pf5, Pf4, Pe4, Pd7, Pc3]
        stipulation: "h#2"
        intended-solutions: 2
        twins: 
          b: Move h1 a5
        solution: |
          "a) 
          1.Sg7*e6 Rh1*h5   2.Se6*d4 Sf6-g4 # 
          1.Re8*e6 Rh1-e1   2.Re6*f6 Sd4-f3 # 
          
          b) wRh1-->a5
          1.Qc8-c5 e6-e7   2.Qc5*d4 Sf6*d7 # 
          1.Qc8-d8 e6*d7   2.Qd8*f6 Sd4-c6 #"
    """)),

    'zpawns':  model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Kd8, Ph2, Pf2]
          black: [Kd5, Rd2]
        stipulation: "h#5.5"
        intended-solutions: 2
        solution: |
          "1...f2-f4   2.Rd2*h2 f4-f5  3.Kd5-e4 f5-f6 4.Ke4-f3 f6-f7 5.Kf3-g2 f7-f8=Q   6.Kg2-h1 Qf8-f1 #
          1...h2-h3   2.Rd2*f2 h3-h4   3.Kd5-e6 h4-h5   4.Ke6-f7 h5-h6   5.Kf7-f8 h6-h7   6.Rf2-f7 h7-h8=Q #"
    """)),

    'rotateandcastle': model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Kh5, Rh8]
        stipulation: "#1"
        solution: |
          "a)
          1.Kh5-g5 #
          b) rotate 270
          1.0-0 #"
    """)),

    'rebirthatarrival': model.makeSafe(yaml.safe_load("""
        algebraic: 
          white: [Bf2]
          black: [Bd4,Pe3]
        stipulation: "h#3"
        solution: "1.e3*f2[+wPf2][+wBd2] f2-f4 2.Bd4-g7"
            """)),

    'simple_anticirce': model.makeSafe(yaml.load("""
        algebraic: 
          white: [Pc4]
          black: [Kc3]
        stipulation: "h#1"
        solution: "1.Kc3*c4[bKc4->e8] "
            """)),
}
