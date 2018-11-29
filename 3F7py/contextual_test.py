from utils import *
import contextual as con

f = open('10.txt.utf-8', encoding='utf-8-sig')
bible = f.read()
f.close()
print(bible[555:925])
bible_test = bible[:1000]
bible = bible[555:]

encodings, decoded, con_p = con.full_encode(bible_test)
print(decoded)