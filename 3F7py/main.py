import arithmetic as arith
from os import stat
from itertools import groupby

filename = 'hamlet.txt'
Nin = stat(filename).st_size
f = open(filename, 'r')
hamlet = f.read()
frequencies = dict([(key, len(list(group))) for key, group in groupby(sorted(hamlet))])
p = dict([(a,frequencies[a]/Nin) for a in frequencies])
f.close()

arith_encoded = arith.encode(hamlet, p, probability_on_the_go=True)
arith_decoded = arith.decode(arith_encoded, p, Nin, probability_on_the_go=True)
print('\n'+''.join(arith_decoded[:294]))
