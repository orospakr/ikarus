from twisted.trial import unittest

import ikarus.irc

class IRCTestCase(unittest.TestCase):
    def testInstantiate(self):
        i = ikarus.irc.IRC()
        self.failIfEqual(i, None)
