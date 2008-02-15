from twisted.trial import unittest
import logging

import ikarus.irc

import pmock

class IRCTestCase(unittest.TestCase):
    def testGetChannelByName(self):
        irc_factory = ikarus.irc.IRCFactory()
        channel = pmock.Mock()
        channel.name = "funcity"
        irc_factory.registerChannel(channel)
        found_channel = irc_factory.getChannelByName("funcity")
        self.failUnlessEqual(True, found_channel is channel)
