def initialize_freqs(alphabet):
    frequencies = {letter: 1 for letter in alphabet}
    return frequencies
    
    
def freq_on_the_go(frequencies, new_char):
    frequencies[new_char] += 1
    return frequencies
    
    
def freq_to_prob(frequencies):
    total_chars = sum([freq for freq in frequencies.values()])
    probs = {character: freq*1.0/total_chars for character, freq in frequencies.items()}
    return probs


def prob_to_cumulative_prob(probs):
    cumulative_prob = 0
    f = [cumulative_prob]
    for key in probs:
        cumulative_prob += probs[key]
        f.append(cumulative_prob)
    f.pop()
    f = dict([(a,mf) for a,mf in zip(probs,f)])
    return f


def n_gram_frequency(text, n=1):
    n_freq = dict()
    for index in range(len(text)-n+1):
        gram = ''.join(text[index:index+n])
        n_freq[gram] = n_freq.get(gram, 0) + 1
    return n_freq
