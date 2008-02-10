from twisted.trial import unittest
from twisted.test import proto_helpers

import pmock

import twisted.internet
import twisted.internet.reactor

import ikarus.irc
import ikarus.channel
import logging

import ikarus.tests.test_irc

class ChannelTestCase(unittest.TestCase):
    def setUp(self):
        #self.factory = ikarus.irc.IRCFactory()
        #self.irc = self.factory.buildProtocol(None)
        #self.irc.nick = "orospakr"
        self.irc_factory = pmock.Mock() # mockery of ikarus.irc.IRCFactory
        self.irc_factory.users = []
#        self.irc_factory.expects(pmock.return_value(None)).register_channel()
        self.c = ikarus.channel.Channel(self.irc_factory, "mychannel")

    def testInstantiation(self):
        self.failIfEqual(self.c, None)

    def testFindUser(self):
        user = pmock.Mock()
        user.nick = "orospakr"
        self.irc_factory.users.append(user)
        self.c.joinUser(user)
        found_user = self.c.findUser("orospakr")
        self.failIfEqual(user, None)
        self.failUnlessEqual(user.nick, "orospakr")

    def testFindUserNoUser(self):
        found_user = self.c.findUser("orospakr")
        self.failUnlessEqual(found_user, None)

    def testInformJoin(self):
        self.listening_user = pmock.Mock()
        self.listening_user.nick = "listening_guy"
        self.listening_user.name = "listening_guy"
        self.listening_user.expects(pmock.once()).sendLine(pmock.eq(
                ":orospakr!~orospakr@localhost. JOIN :#mychannel"))
        self.irc_factory.users.append(self.listening_user)

        self.user = pmock.Mock()
        self.user.nick = "orospakr"
        self.user.name = "orospakr"
        self.irc_factory.users.append(self.user)
        self.user.expects(pmock.never()).sendLine(pmock.eq(""))

        self.c.joinUser(self.listening_user)
        self.c.joinUser(self.user)

        self.listening_user.verify()
        self.user.verify()

    def testJoinAndMessage(self):
        self.testInformJoin()
        self.listening_user.expects(pmock.once()).sendLine(pmock.eq(
                ":orospakr!~orospakr@localhost. PRIVMSG #mychannel :Hello."))
        self.user.expects(pmock.never()).sendLine(pmock.eq(""))
        self.c.privMsg(self.user, "Hello.")
        self.listening_user.verify()
        self.user.verify()

        # make sure the same goes both ways...
        self.user.expects(pmock.once()).sendLine(pmock.eq(
                ":listening_guy!~listening_guy@localhost. PRIVMSG #mychannel :Happy times."))
        self.listening_user.expects(pmock.never()).sendLine(pmock.eq(""))
        self.c.privMsg(self.listening_user, "Happy times.")
        self.listening_user.verify()
        self.user.verify()



