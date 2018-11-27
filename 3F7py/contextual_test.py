from utils import *
from pprint import pprint
import contextual as con

f = open('10.txt.utf-8')
bible = f.read()
f.close()
print(bible[555:925])
bible_test = bible[:1000]
bible = bible[555:]


def full_encode(text_to_encode, n_gram=2):
    padded_text = ''.join([' ' for _ in range(n_gram)]) + text_to_encode
    alphabet = set(letter for letter in padded_text)
    alphabet = sorted(list(alphabet))
    print(alphabet)

    n_gram_freqs = {n: n_gram_frequency(padded_text, n=n) for n in range(1, n_gram+1)}
    encoded, conditional_probs, cumulative_probs, highest_gram = con.encode(text_to_encode, n_gram_freqs)
    decoded = con.decode(encoded, source_length=len(text_to_encode),
                         conditional_probs=conditional_probs, cumulative_probs=cumulative_probs,
                         highest_gram=highest_gram)
    return encoded, decoded


encodings, decoded = full_encode(bible_test)
print(encodings)
print(decoded)
