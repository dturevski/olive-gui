def tuples(seq, n, with_permutations):
    if(n > len(seq)):
        return
    if n == 1:
        for e in seq:
            yield [e]
    else:
        for i in range(len(seq)):
            if with_permutations:
                for tail in tuples(seq[:i] + seq[i + 1:], n - 1, True):
                    yield [seq[i]] + tail
            else:
                for tail in tuples(seq[i + 1:], n - 1, False):
                    yield [seq[i]] + tail


def all_different(seq):
    return len(set(seq)) == len(seq)


def retval(provides):
    r = {}
    for k in provides():
        r[k] = False
    return r


def find(seq, elem):
    try: return seq.index(elem)
    except: return -1
