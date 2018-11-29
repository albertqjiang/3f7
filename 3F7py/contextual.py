from math import floor, ceil
from sys import stdout as so
from bisect import bisect
from utils import *


def encode(raw_text, n_gram_freqs):
    precision = 32
    one = int(2 ** precision - 1)
    quarter = int(ceil(one / 4))
    half = 2 * quarter
    threequarters = 3 * quarter

    highest_gram = max(list(n_gram_freqs.keys()))

    conditional_probs = joint_to_cond_prob(n_gram_freqs)
    cumulative_probs = dict()
    for key, value in conditional_probs.items():
        condition = key.split('|')[1]
        cumulative_probs[condition] = cumulative_probs.get(condition, dict())
        cumulative_probs[condition][key] = value

    for condition, probs in cumulative_probs.items():
        cumulative_probs[condition] = prob_to_cumulative_prob(probs)

    y = []  # initialise output list
    lo, hi = 0, one  # initialise lo and hi to be [0,1.0)
    straddle = 0  # initialise the straddle counter to 0

    for k in range(len(raw_text)):  # for every symbol
        # arithmetic coding is slower than vl_encode, so we display a "progress bar"
        # to let the user know that we are processing the file and haven't crashed...
        if k % 100 == 0:
            so.write('Arithmetic encoded %d%%    \r' % int(floor(k / len(raw_text) * 100)))
            so.flush()

        # 1) calculate the interval range to be the difference between hi and lo and
        # add 1 to the difference. The added 1 is necessary to avoid rounding issues
        lohi_range = hi - lo + 1

        # 2) narrow the interval end-points [lo,hi) to the new range [f,f+p]
        # within the old interval [lo,hi], being careful to round 'innwards' so
        # the code remains prefix-free (you want to use the functions ceil and
        # floor). This will require two instructions. Note that we start computing
        # the new 'lo', then compute the new 'hi' using the scaled probability as
        # the offset from the new 'lo' to the new 'hi'
        if k >= highest_gram - 1:
            condition = ''.join(raw_text[k-highest_gram+1:k])
            reference = raw_text[k] + '|' + condition
        else:
            condition = raw_text[:k].rjust(highest_gram-1)
            reference = raw_text[k] + '|' + condition

        lo = lo + int(ceil(lohi_range * cumulative_probs[condition][reference]))
        hi = lo + int(floor(lohi_range * conditional_probs[reference]))

        if lo == hi:
            raise NameError('Zero interval!')

        # Now we need to re-scale the interval if its end-points have bits in common,
        # and output the corresponding bits where appropriate. We will do this with an
        # infinite loop, that will break when none of the conditions for output / straddle
        # are fulfilled
        while True:
            if hi < half:  # if lo < hi < 1/2
                # stretch the interval by 2 and output a 0 followed by 'straddle' ones (if any)
                # and zero the straddle after that. In fact, HOLD OFF on doing the stretching:
                # we will do the stretching at the end of the if statement
                y.append(0)  # append a zero to the output list y
                y.extend([1] * straddle)  # extend by a sequence of 'straddle' ones
                straddle = 0  # zero the straddle counter
            elif lo >= half:  # if hi > lo >= 1/2
                # stretch the interval by 2 and substract 1, and output a 1 followed by 'straddle'
                # zeros (if any) and zero straddle after that. Again, HOLD OFF on doing the stretching
                # as this will be done after the if statement, but note that 2*interval - 1 is equivalent
                # to 2*(interval - 1/2), so for now just substract 1/2 from the interval upper and lower
                # bound (and don't forget that when we say "1/2" we mean the integer "half" we defined
                # above: this is an integer arithmetic implementation!
                y.append(1)  # append a 1 to the output list y
                y.extend([0] * straddle)  # extend 'straddle' zeros
                straddle = 0  # reset the straddle counter
                lo -= half
                hi -= half  # substract half from lo and hi
            elif lo >= quarter and hi < threequarters:  # if 1/4 < lo < hi < 3/4
                # we can increment the straddle counter and stretch the interval around
                # the half way point. This can be impemented again as 2*(interval - 1/4),
                # and as we will stretch by 2 after the if statement all that needs doing
                # for now is to subtract 1/4 from the upper and lower bound
                straddle += 1  # increment straddle
                lo -= quarter
                hi -= quarter  # subtract 'quarter' from lo and hi
            else:
                break  # we break the infinite loop if the interval has reached an un-stretchable state
            # now we can stretch the interval (for all 3 conditions above) by multiplying by 2
            lo *= 2  # multiply lo by 2
            hi = hi * 2 + 1  # multiply hi by 2 and add 1 (I DON'T KNOW WHY +1 IS NECESSARY BUT IT IS. THIS IS MAGIC.
            # A BOX OF CHOCOLATES FOR ANYONE WHO GIVES ME A WELL ARGUED REASON FOR THIS... It seems
            # to solve a minor precision problem.)

    # termination bits
    # after processing all input symbols, flush any bits still in the 'straddle' pipeline
    straddle += 1  # adding 1 to straddle for "good measure" (ensures prefix-freeness)
    if lo < quarter:  # the position of lo determines the dyadic interval that fits
        y.append(0)  # output a zero followed by "straddle" ones
        y.extend([1] * straddle)
    else:
        y.append(1)  # output a 1 followed by "straddle" zeros
        y.extend([0] * straddle)
    return y, conditional_probs, cumulative_probs, highest_gram


def decode(y, source_length, conditional_probs, cumulative_probs, highest_gram):
    precision = 32
    one = int(2 ** precision - 1)
    quarter = int(ceil(one / 4))
    half = 2 * quarter
    threequarters = 3 * quarter

    y.extend(precision * [0])  # dummy zeros to prevent index out of bound errors
    x = source_length * [0]  # initialise all zeros

    # initialise by taking first 'precision' bits from y and converting to a number
    value = int(''.join(str(a) for a in y[0:precision]), 2)
    position = precision  # position where currently reading y
    lo, hi = 0, one

    for k in range(source_length):
        if k % 100 == 0:
            so.write('Arithmetic decoded %d%%    \r' % int(floor(k / source_length * 100)))
            so.flush()

        lohi_range = hi - lo + 1
        # This is an essential subtelty: the slowest part of the decoder is figuring out
        # which symbol lands us in an interval that contains the encoded binary string.
        # This can be extremely wasteful (o(n) where n is the alphabet size) if you proceed
        # by simple looping and comparing. Here we use Python's "bisect" function that
        # implements a binary search and is 100 times more efficient. Try
        # for a = [a for a in f if f[a]<(value-lo)/lohi_range)][-1] for a MUCH slower solution.
        if k >= highest_gram - 1:
            condition = ''.join(x[k-highest_gram+1:k])
        else:
            condition = ''.join(x[:k]).rjust(highest_gram-1)

        a = bisect(list(cumulative_probs[condition].values()), (value - lo) / lohi_range) - 1
        x[k] = list(cumulative_probs[condition].keys())[a].split('|')[0]  # output alphabet[a]

        lo = lo + int(ceil(cumulative_probs[condition][''.join((x[k], '|', condition))] * lohi_range))
        hi = lo + int(floor(conditional_probs[''.join((x[k], '|', condition))] * lohi_range))

        if lo == hi:
            raise NameError('Zero interval!')

        while True:
            if hi < half:
                # do nothing
                pass
            elif lo >= half:
                lo = lo - half
                hi = hi - half
                value = value - half
            elif lo >= quarter and hi < threequarters:
                lo = lo - quarter
                hi = hi - quarter
                value = value - quarter
            else:
                break
            lo = 2 * lo
            hi = 2 * hi + 1
            value = 2 * value + y[position]
            position += 1
            if position == len(y):
                raise NameError('Unable to decompress')

    return x


def joint_to_cond_prob(n_gram_probs):
    cond_probs = dict()
    highest_degree = max(list(n_gram_probs.keys()))
    joint_probs = n_gram_probs[highest_degree]
    gram_probs = n_gram_probs[highest_degree-1]
    for key, value in joint_probs.items():
        cond_probs[key[-1] + "|" + key[:-1]] = value / gram_probs[key[:-1]]
    return cond_probs
