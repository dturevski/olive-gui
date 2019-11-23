import sys, re

stopwords = ["jt", "tt", "tourney", "mt", "mt.", "тк", "wccc", "turnier", "ty", "ty.", "j.t.", "t.t.",
             "corr", "corr.", "мк", "мт", "юк", "конкурс", "выпуск", "посвященный", "турнир", "спецвыпуск"]

def is_numbered_tt(s):
    return re.match("\btt-[0-9]+\b", s)

def has_stopword(s):
    for word in s.split():
        if word in stopwords:
            return True
    return False

def has_unmatched_prenthesis(s):
    return s.count("(") != s.count(")")


def legit(s):
    return \
        not has_stopword(s) and \
        not s.endswith("-") and \
        not is_numbered_tt(s) and \
        not has_unmatched_prenthesis(s)

def main():
    with open(sys.argv[1], 'r') as f:
        for line in [s for s in f.readlines() if legit(s.strip().lower())]:
            print(line, end = '')


if __name__ == '__main__':
    main()