class EQ:
    def __init__(self, eq_id, members):
        self.eq_id = eq_id
        self.members = set(_ for _ in members)  # assume loc > 0
        self.superblocks = None
        self.unique_sb = None

    def __str__(self):
        m = sorted(list(self.members), key=lambda x: abs(x))
        words = [f"EQ{self.eq_id}: {m}"]

        if self.superblocks is not None:
            for i, sb in enumerate(self.superblocks):
                w = f"sb{i}: {sorted(sb, key=lambda b: min(abs(loc) for loc in b))}"
                words.append(w)

        if self.unique_sb is not None:
            for i, sb in enumerate(self.unique_sb):
                w = f"Uniq{i}: {sorted(sb, key=lambda b: min(abs(loc) for loc in b))}"
                words.append(w)
        return "\n".join(words)

    def find_superblock(self, loc2b):
        """
        Find the set of blocks, in loc2b, contain exactly all the words in self.members
        (except for possibly some negative locations)
        """
        blocks = set()
        for loc in self.members:
            if loc in loc2b:
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
    def _positive(self, members):
        pos = set(loc for loc in members if loc > 0)
        return pos

    def __init__(self, Annotators, all_gt=True):
        """Annotators is a list of annotators. |Annotators| = K
        Each annotator is a dict from location id to its block tuple (loc2b)
        See the example in the main code below.
        """
        if all_gt:
            for loc2b in Annotators:
                for loc in loc2b:
                    assert(loc > 0)
                for b in set(loc2b.values()):
                    p = self._positive(b)
                    assert len(p) == len(b)
        else:
            assert(len(Annotators)==2)
            
        self.all_gt = all_gt
        self.EQClasses = {}  # class id to EQ object
        self.loc2EQ = {}  # loc id (may be -ve) to EQ object
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

            set1 = set(
                self.EQClasses[id1].members
            )  # make a copy of all locations in id1
            merge_candidates = [id1]
            while True:
                set2 = set()
                for loc in self._positive(set1):
                    block2 = annotator2[loc]
                    set2 = set2.union(block2)
                if self._positive(set2) == self._positive(set1):
                    set1 = set1.union(set2)  # adding -ve locations from set2
                    break

                for loc in self._positive(set2):
                    if loc not in set1:
                        eq1 = self.loc2EQ[loc]
                        set1 = set1.union(eq1.members)
                        merge_candidates.append(eq1.eq_id)
                set1 = set1.union(set2)
                if self._positive(set1) == self._positive(set2):
                    break

            if len(merge_candidates) > 1:
                self._create(set1, merge_candidates)
            elif len(set1) > len(self.EQClasses[id1].members):
                # adding more negative numbers
                set._create(set1, merge_candidates)

            done = done.union(merge_candidates)

        for loc, b in annotator2.items():
            if loc not in self.loc2EQ:
                self._create(b)

    def all_combinatory(self):
        if not self.all_gt:
            return set()
        
        EQList = list(self.EQClasses.values())
        blocks = set()
        return self._recursive_combinatory(0, blocks, EQList)

    def _recursive_combinatory(self, eq_idx, blocks, EQList):
        if eq_idx == len(EQList):
            yield blocks
        else:
            for sb in EQList[eq_idx].unique_sb:
                blocks2 = blocks.union(sb)
                yield from self._recursive_combinatory(eq_idx + 1, blocks2, EQList)


if __name__ == "__main__":
    # A=bestGT, B=prediction
    # They both may contain negative locations
    a1 = (1, 2, -3, 4, -5)
    a2 = (6, 7)
    A_loc2b = {}
    for a in [a1, a2]:
        for x in a:
            A_loc2b[x] = a

    B_loc2b = {}
    b1 = (1, 2, 4, 7)
    b2 = (6,)
    b3 = (-8, -9)
    for b in [b1, b2, b3]:
        for y in b:
            B_loc2b[y] = b

    eqb = EQBuilder([A_loc2b, B_loc2b], all_gt=False)
    for eq in eqb.EQClasses.values():
        print(eq)
        print()
    for ans in eqb.all_combinatory():
        tmp = sorted(ans, key=lambda b: min(abs(loc) for loc in b))
        print(tmp)

    print("=====")
    # A, B, C all GT block definitions. All positive locations.
    A = {1: (1,), 2: (2, 3), 3: (2, 3), 4: (4, 5), 5: (4, 5)}
    B = {1: (1, 2, 3), 2: (1, 2, 3), 3: (1, 2, 3), 4: (5, 4), 5: (5, 4)}
    C = {1: (1, 2, 3), 2: (1, 2, 3), 3: (1, 2, 3), 4: (4, 5), 5: (4, 5)}
    eqb = EQBuilder([A, B, C])
    for eq in eqb.EQClasses.values():
        print(eq)
        print()
    for ans in eqb.all_combinatory():
        tmp = sorted(ans, key=lambda b: min(abs(loc) for loc in b))
        print(tmp)
