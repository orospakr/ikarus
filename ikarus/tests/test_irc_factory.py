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

    def testGetChannelNameShouldBeAbleToFindNthChannelInList(self):
        # duurrrrr, this bug took me ages to track down because it was
        # causing a seemingly unrelated test to fail! GRRRR
        irc_factory = ikarus.irc.IRCFactory()
        channel = pmock.Mock()
        channel.name = 'firstchan'
        irc_factory.registerChannel(channel)

        second_channel = pmock.Mock()
        second_channel.name = 'lolchan'
        irc_factory.registerChannel(second_channel)

        found_channel = irc_factory.getChannelByName('lolchan')
        self.failUnlessEqual(True, found_channel is second_channel)

