# ST-OCR
This repository consists of three py files.
## eq.py
Given K human block annotations, find all acceptable block annotations. Each block is represented as a tuple of integers. Each integer is from the location ID. 

The block definition of an image is represented by a dictionary from location ID to block tuple. For example, an image of five words with block (1 2 3) and (4 5) is represented by {1: (1,2,3), 2: (1,2,3), 3: (1,2,3), 4:(4,5), 5:(4,5)}.

## bestGT-eq.py
Given the best block definition (in a form of dictionary of location ID to block tuple), and the OCR predicted block definition for an image, find their
superblock alignment.

## bleu.py
Based on the superblock alignment found by bestGT-eq.py, compute the BLEU score. Ngrams across block boundaries are excluded.
