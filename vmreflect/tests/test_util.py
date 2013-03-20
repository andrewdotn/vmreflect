import string
import unittest

class TestUtil(unittest.TestCase):

    def test_random_string(self):
        from vmreflect.utils import get_random_string
        for l in range(20):
            self.assertEquals(l, len(get_random_string(length=l)))
        for alphabet in ['1234', string.letters, '!$(AJ$)AF(A@F']:
            self.assertTrue(
                all(c in alphabet
                    for c in get_random_string(alphabet=alphabet)))

