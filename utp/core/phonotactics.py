"""UTP phonotactics: is a root a legal word of its proto-language?

The inventory comes from the sound-laws file ("proto": units, vowels,
onset_clusters, finals). The policy comes from the pack and says what the
inventory alone cannot:

  transparent          segments ignored when counting consonant clusters (a glottal stop)
  no_initial           segments a word may not begin with
  max_medial_cluster   most consonants allowed together between vowels
  final_cluster        whether a word may end in two consonants
"""

DEFAULT_POLICY = {"transparent": [], "no_initial": [], "max_medial_cluster": 2, "final_cluster": False}


class Phonotactics:
    def __init__(self, proto, policy=None):
        self.units = sorted(proto["units"], key=len, reverse=True)
        self.vowels = set(proto["vowels"])
        self.onsets = set(proto.get("onset_clusters", []))
        self.finals = set(proto.get("finals", []))
        p = dict(DEFAULT_POLICY, **(policy or {}))
        self.transparent = set(p["transparent"])
        self.no_initial = set(p["no_initial"])
        self.max_medial = p["max_medial_cluster"]
        self.final_cluster = p["final_cluster"]

    def segment(self, form):
        """Longest-match split into the inventory's units, or None if a sound is not in it."""
        out, i = [], 0
        while i < len(form):
            for u in self.units:
                if form.startswith(u, i):
                    out.append(u)
                    i += len(u)
                    break
            else:
                return None
        return out

    def check(self, form):
        us = self.segment(form)
        if not us:
            return False, "contains a sound outside the proto-language"
        if us[0] in self.no_initial:
            return False, f"cannot start with {us[0]}"
        cons_run, onset, seen_v = [], [], False
        for u in us:
            if u in self.vowels:
                if not seen_v and len(onset) > 1 and "".join(onset) not in self.onsets:
                    return False, f"onset {''.join(onset)}- not allowed"
                if seen_v and len([c for c in cons_run if c not in self.transparent]) > self.max_medial:
                    return False, f"more than {self.max_medial} consonants together"
                seen_v, cons_run = True, []
            else:
                (cons_run if seen_v else onset).append(u)
        if not seen_v:
            return False, "no vowel"
        final = [c for c in cons_run if c not in self.transparent]
        if len(final) > 1 and not self.final_cluster:
            return False, "word ends in a consonant cluster"
        if final and final[0] not in self.finals:
            return False, f"cannot end in {final[0]}"
        return True, ""
