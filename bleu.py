import math
from collections import Counter, namedtuple
import numpy as np

"""
Refer to https://github.com/mozilla/sacreBLEU/blob/master/sacrebleu.py
and
https://aclanthology.org/P02-1040.pdf

log BLEU = min(1-r/c, 0) + \sum_i w_i log p_i
"""
NGRAM_ORDER = 4
BLEU = namedtuple(
    "BLEU", "score, ngram_hits, total_ngrams, precisions, bp, sys_len, ref_len"
)


def my_log(num):
    """
    Floors the log function
    :param num: the number
    :return: log(num) floored to a very low number
    """
    if num == 0.0:
        return -9999999999
    return math.log(num)


def compute_bleu(
    correct,
    total,
    sys_len,
    ref_len,
    smooth="none",
    smooth_floor=0.01,
    use_effective_order=False,
):
    """Computes BLEU score from its sufficient statistics. Adds smoothing.
    :param correct: List of counts of correct ngrams, 1 <= n <= NGRAM_ORDER
    :param total: List of counts of total ngrams, 1 <= n <= NGRAM_ORDER
    :param sys_len: The cumulative system length
    :param ref_len: The cumulative reference length
    :param smooth: The smoothing method to use
    :param smooth_floor: The smoothing value added, if smooth method 'floor' is used
    :param use_effective_order: Use effective order.
    :return: A BLEU object with the score (100-based) and other statistics.
    """

    precisions = [0 for x in range(NGRAM_ORDER)]

    smooth_mteval = 1.0
    effective_order = NGRAM_ORDER
    for n in range(NGRAM_ORDER):
        if total[n] == 0:
            break

        if use_effective_order:
            effective_order = n + 1

        if correct[n] == 0:
            if smooth == "exp":
                smooth_mteval *= 2
                precisions[n] = 100.0 / (smooth_mteval * total[n])
            elif smooth == "floor":
                precisions[n] = 100.0 * smooth_floor / total[n]
        else:
            precisions[n] = 100.0 * correct[n] / total[n]

    # If the system guesses no i-grams, 1 <= i <= NGRAM_ORDER, the BLEU score is 0 (technically undefined).
    # This is a problem for sentence-level BLEU or a corpus of short sentences, where systems will get no credit
    # if sentence lengths fall under the NGRAM_ORDER threshold. This fix scales NGRAM_ORDER to the observed
    # maximum order. It is only available through the API and off by default

    brevity_penalty = 1.0
    if sys_len < ref_len:
        brevity_penalty = math.exp(1 - ref_len / sys_len) if sys_len > 0 else 0.0

    bleu = brevity_penalty * math.exp(
        sum(map(my_log, precisions[:effective_order])) / effective_order
    )

    return BLEU._make(
        [bleu, correct, total, precisions, brevity_penalty, sys_len, ref_len]
    )


def superblock_extract_ngrams(lines, min_order=1, max_order=NGRAM_ORDER):
    """
    :param lines: a list of block translations
    :param max_order: collect n-grams from 1<=n<=max
    :return: a dictionary containing ngrams and counts
    """
    ngrams = Counter()
    for line in lines:
        tokens = line.lower().split()
        for n in range(min_order, max_order + 1):
            for i in range(0, len(tokens) - n + 1):
                ngram = " ".join(tokens[i : i + n])
                ngrams[ngram] += 1

    return ngrams


def all_translations(HT, block_idx, combo):
    if block_idx == len(HT):  # #blocks
        yield combo
    else:
        for translation in HT[block_idx]:
            combo[block_idx] = translation
            yield from all_translations(HT, block_idx + 1, combo)


def superblock_ref_stats(MT, refs):
    """Counting GT ngrams for one superblock
    MT = [ MT(b1) MT(b2) ...] for a superblock
    refs = HT = [ HT(a1) HT(a2) ... HT(ah)]
    where each HT(ai) is a list of translations
    -->
    HT_all = [ OneOf(HT(a1)) OneOf(HT(a2)) ... OneOf(HT(an))]
    """
    outlen = sum([len(block.split()) for block in MT])  # c
    GT_ngrams = Counter()
    closest_diff = None
    closest_len = None  # r
    combo = [None] * len(refs)
    for ref in all_translations(refs, 0, combo):
        reflen = sum([len(block.split()) for block in ref])
        diff = abs(outlen - reflen)
        if closest_diff is None or diff < closest_diff:
            closest_diff = diff
            closest_len = reflen
        elif diff == closest_diff:
            if reflen < closest_len:
                closest_len = reflen

        ngrams_ref = superblock_extract_ngrams(ref)
        for ngram in ngrams_ref.keys():
            GT_ngrams[ngram] = max(GT_ngrams[ngram], ngrams_ref[ngram])

    assert closest_diff is not None
    return GT_ngrams, closest_diff, closest_len, outlen


def Lookup(blockname):
    """Look up translation of a block.
    blockname convention: "ai" for GT blocks, "bi" for OCR blocks
    Each GT block has a list of possible translations.
    """
    translation = {
        "caution1": ["CAUTION"],
        "caution23": ["CHILDREN PLAYING"],
        "caution123": "CAUTION CHILDREN PLAYING",
        "a1": ["i love you dearly", "i am very fond of you"],
        "a2": ["fine", "all right", "yes"],
        "b1": "i love yes",
        "b2": "fine",
        "b3": "the the the",
    }

    return translation[blockname]


if __name__ == "__main__":
    # corpus_bleu() in sacrebleu.py
    sys_len = 0  # c
    ref_len = 0  # r
    correct = np.array([0] * NGRAM_ORDER, dtype=int)  # numerator of precision i+1
    total = np.array([0] * NGRAM_ORDER, dtype=int)  # denominator of precision i+1

    # Each image consists of a list of EQ classes.
    # Each EQ class is a pair of (GT superblock, prediction superblock).
    # Each superblock consists of a list of blocks.
    # Table 3
    image1 = [(["caution1", "caution23"], ["caution123"])]  # Figure 4
    image2 = [(["a1", "a2"], ["b1", "b2"]), ([], ["b3"])]  # Table 2
    corpus = [image1, image2]

    for image in corpus:
        correct1 = np.array([0] * NGRAM_ORDER, dtype=int) 
        total1 = np.array([0] * NGRAM_ORDER, dtype=int) 
        for sent in image:
            gt_blocks, pred_blocks = sent
            HT = [Lookup(blkname) for blkname in gt_blocks]
            MT = [Lookup(blkname) for blkname in pred_blocks]
            ref_ngrams, closest_diff, closest_len, outlen = superblock_ref_stats(MT, HT)
            sys_len += outlen  # c
            ref_len += closest_len  # r

            sys_ngrams = superblock_extract_ngrams(MT)
            for ngram in sys_ngrams.keys():
                n = len(ngram.split())
                correct1[n-1] += min(sys_ngrams[ngram], ref_ngrams.get(ngram, 0))
                total1[n-1] += sys_ngrams[ngram]
        print(correct1)
        print(total1)
        print()
        correct += correct1
        total += total1

    bleu = compute_bleu(
        correct,
        total,
        sys_len,
        ref_len,
        smooth="exp",
        smooth_floor=0.01,
        use_effective_order=True,
    )
    print(bleu)
