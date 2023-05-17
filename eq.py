class EQ:
    def __init__(self, eq_id, members):
        self.eq_id = eq_id
        self.members = set([_ for _ in members])  # assume loc > 0
        self.superblocks = None
        self.unique_sb = None

    def find_superblock(self, loc2b):
        """
        Find the set of blocks, in loc2b, contain exactly all the words in self.members
        """
        blocks = set()
        for loc in self.members:
            b = loc2b[loc]
            blocks.add(b)
        return blocks

    def unique_me(self, superblocks):
        unique_sb = []
        for sb in superblocks:
            if sb not in unique_sb:
                unique_sb.append(sb)
        return unique_sb


class EQBuilder:
    def __init__(self, Annotators):
        """Annotators is a list of annotators. |Annotators| = K
        Each annotator is a dict from location id to its block tuple (loc2b)
        See the example in the main code below.
        """
        self.EQClasses = {}  # class id to EQ object
        self.loc2EQ = {}  # loc id to EQ object
        self.eq_id = 0  # eq class id

        for i, loc2b in enumerate(Annotators):
            if i == 0:
                for block in set(loc2b.values()):
                    self._create(block)
            else:
                self._expand(loc2b)

        for eq1 in self.EQClasses.values():
            eq1.superblocks = [eq1.find_superblock(loc2b) for loc2b in Annotators]
            eq1.unique_sb = eq1.unique_me(eq1.superblocks)

    def _create(self, block, deletions=None):
        eq1 = EQ(self.eq_id, block)
        self.EQClasses[self.eq_id] = eq1

        for loc in block:
            self.loc2EQ[loc] = eq1
        self.eq_id += 1

        if deletions is not None:
            for id in deletions:
                del self.EQClasses[id]

    def _expand(self, annotator2):
        eq_ids = list(self.EQClasses.keys())
        done = set()
        for id1 in eq_ids:
            if id1 in done:
                continue
            set1 = self.EQClasses[id1].members  # all locations in id1
            merge_candidates = [id1]
            while True:
                set2 = set(loc2 for loc1 in set1 for loc2 in annotator2[loc1])
                if set2 == set1:
                    break

                for loc in set2:
                    if loc not in set1:
                        eq1 = self.loc2EQ[loc]
                        set1 = set1.union(eq1.members)
                        merge_candidates.append(eq1.eq_id)
                if set1 == set2:
                    break
            if len(merge_candidates) > 1:
                self._create(set1, merge_candidates)
            done = done.union(merge_candidates)

    def all_combinatory(self):
        EQList = list(self.EQClasses.values())
        blocks = set()
        return self.recursive_combinatory(0, blocks, EQList)

    def recursive_combinatory(self, eq_idx, blocks, EQList):
        if eq_idx == len(EQList):
            yield blocks
        else:
            for sb in EQList[eq_idx].unique_sb:
                blocks2 = blocks.union(sb)
                yield from self.recursive_combinatory(eq_idx + 1, blocks2, EQList)


if __name__ == "__main__":
    # Table 1
    A = {1: (1,), 2: (2, 3), 3: (2, 3), 4: (4, 5), 5: (4, 5)}
    B = {1: (1, 2, 3), 2: (1, 2, 3), 3: (1, 2, 3), 4: (5, 4), 5: (5, 4)}
    eqb = EQBuilder([A, B])
    for ans in eqb.all_combinatory():
        tmp = sorted(ans, key=lambda b: min(abs(loc) for loc in b))
        print(tmp)
