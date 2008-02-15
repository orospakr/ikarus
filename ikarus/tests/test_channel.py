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
        self.irc_factory = pmock.Mock() # mockery of ikarus.irc.IRCFactory
        self.irc_factory.users = []
        self.c = ikarus.channel.Channel(self.irc_factory, "mychannel")

    def testInstantiation(self):
        self.failIfEqual(self.c, None)

    # I might adapt this test case to also test a hostname other
    # than localhost.
    def testJoinAndMessageChannelWithNameOtherThanMyChannel(self):
        chan = ikarus.channel.Channel(self.irc_factory, "coolpeopleonly")
        user = pmock.Mock()
        user.name = "nobody"
        user.nick = "clevernickname"
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":clevernickname!~nobody@localhost. JOIN :#coolpeopleonly"))
        self.irc_factory.users.append(user)
        chan.joinUser(user)

        other_user = pmock.Mock()
        other_user.name = "someone_else"
        other_user.nick = "spam_and_eggs"
        other_user.expects(pmock.once()).sendLine(pmock.eq(
                ":spam_and_eggs!~someone_else@localhost. JOIN :#coolpeopleonly"))
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":spam_and_eggs!~someone_else@localhost. JOIN :#coolpeopleonly"))
        self.irc_factory.users.append(other_user)
        chan.joinUser(other_user)

        user.expects(pmock.once()).sendLine(pmock.eq(
                ":spam_and_eggs!~someone_else@localhost. PRIVMSG #coolpeopleonly :Hi There!"))
        chan.privMsg(other_user, "Hi There!")

    def testFindUser(self):
        user = pmock.Mock()
        user.nick = "orospakr"
        user.name = "orospakr"
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":orospakr!~orospakr@localhost. JOIN :#mychannel"))
        self.irc_factory.users.append(user)
        self.c.joinUser(user)
        found_user = self.c.findUser("orospakr")
        self.failIfEqual(user, None)
        self.failUnlessEqual(user.nick, "orospakr")
        self.failUnlessEqual(user.name, "orospakr")

    def testFindUserNoUser(self):
        found_user = self.c.findUser("orospakr")
        self.failUnlessEqual(found_user, None)

    def testJoinUser(self):
        self.joining_user = pmock.Mock()
        self.joining_user.nick = "somefella"
        self.joining_user.name = "sfella"
        self.joining_user.expects(pmock.once()).sendLine(pmock.eq(
                ":somefella!~sfella@localhost. JOIN :#mychannel"))
        self.irc_factory.users.append(self.joining_user)
        self.c.joinUser(self.joining_user)
        self.joining_user.verify()

    def testInformJoin(self):
        self.listening_user = pmock.Mock()
        self.listening_user.nick = "listening_guy"
        self.listening_user.name = "listening_guy"
        self.listening_user.expects(pmock.once()).sendLine(pmock.eq(
                ":listening_guy!~listening_guy@localhost. JOIN :#mychannel"))
        self.listening_user.expects(pmock.once()).sendLine(pmock.eq(
                ":orospakr!~orospakr@localhost. JOIN :#mychannel"))
        self.irc_factory.users.append(self.listening_user)

        self.user = pmock.Mock()
        self.user.nick = "orospakr"
        self.user.name = "orospakr"
        self.user.expects(pmock.once()).sendLine(pmock.eq(
                ":orospakr!~orospakr@localhost. JOIN :#mychannel"))
        self.irc_factory.users.append(self.user)

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



