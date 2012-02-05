def tuples(seq, n, with_permutations):
    if(n > len(seq)):
        return
    if n == 1:
        for e in seq:
            yield [e]
    else:
        for i in range(len(seq)):
            if with_permutations:
                for tail in tuples(seq[:i]+seq[i+1:], n-1, True):
                    yield [seq[i]]+tail
            else:
                for tail in tuples(seq[i+1:], n-1, False):
                    yield [seq[i]]+tail
                
def all_different(seq):
    for i in xrange(len(seq)):
        if seq[i] in seq[i+1:]:
            return False
    return True

def retval(provides):
    r = {}
    for k in provides():
        r[k] = False
    return r