import arithmetic as arith
from vl_codes import bytes2bits, bits2bytes
from os import stat
from itertools import groupby

filename = 'hamlet.txt'
Nin = stat(filename).st_size
f = open(filename, 'r')
hamlet = f.read()
frequencies = dict([(key, len(list(group))) for key, group in groupby(sorted(hamlet))])
p = dict([(a,frequencies[a]/Nin) for a in frequencies])
f.close()

hamlet = hamlet * 10
Nin = Nin * 10

arith_encoded = arith.encode(hamlet, p, probability_on_the_go=False)
arith_decoded = arith.decode(arith_encoded, p, Nin, probability_on_the_go=False)
hamlet_zipped = bits2bytes(arith_encoded)
Nout = len(hamlet_zipped)
print(Nout/Nin)
print(8 * Nout/Nin)

arith_encoded = arith.encode(hamlet, p, probability_on_the_go=True)
arith_decoded = arith.decode(arith_encoded, p, Nin, probability_on_the_go=True)
hamlet_zipped = bits2bytes(arith_encoded)
Nout = len(hamlet_zipped)
print(Nout/Nin)
print(8 * Nout/Nin)
