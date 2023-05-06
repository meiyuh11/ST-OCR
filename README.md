# ST-OCR
This repository consists of three py files.
## eq.py
Given K human block annotations, find all acceptable K' block annotations. Each block is represented as a tuple of integers. Each integer is from the location ID. All location IDs are positive.

The block definition of an image is represented by a dictionary, from location ID to block tuple. For example, an image of five words with block (1 2 3) and (4 5) is represented by {1: (1,2,3), 2: (1,2,3), 3: (1,2,3), 4:(4,5), 5:(4,5)}.

Please follow __main__ to understand the code.

## bestGT-eq.py
Given the best block definition (bestGT), and the OCR predicted block definition for an image, find their
superblock alignment.

BestGT is defined as a dictionary  of location ID to block tuple. Location IDs are negative for deleted words. Similarly for the predicted
block definition, a negative location means an insertion error.

bestGT-eq.py is a super set of eq.py, in the sense that it can handle both cases. Once you have bestGT-eq.py, you may get rid of eq.py.
eq.py is there to provide a quick understanding of equivalence classes and superblocks.


## bleu.py
Based on the superblock alignment found by bestGT-eq.py, compute the BLEU score. Ngrams across block boundaries are excluded.
