import unittest
from collections import Counter

class QuorumTests(unittest.TestCase):
    def test_three_matching_replicas_confirm(self):
        votes = Counter(["ACCEPTED", "ACCEPTED", "ACCEPTED", "UNAVAILABLE"])
        self.assertGreaterEqual(votes["ACCEPTED"], 3)

    def test_two_matching_replicas_do_not_confirm(self):
        votes = Counter(["ACCEPTED", "ACCEPTED", "UNAVAILABLE", "UNAVAILABLE"])
        self.assertLess(votes["ACCEPTED"], 3)

    def test_one_divergent_replica_is_outvoted(self):
        winner, count = Counter(["ACCEPTED", "ACCEPTED", "ACCEPTED", "REJECTED"]).most_common(1)[0]
        self.assertEqual(winner, "ACCEPTED")
        self.assertEqual(count, 3)

if __name__ == "__main__":
    unittest.main()
