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
        self.irc_factory.expects(pmock.once()).method("registerChannel")
        self.irc_factory.users = []
        self.c = ikarus.channel.Channel(self.irc_factory, "mychannel")

    def testInstantiation(self):
        self.failIfEqual(self.c, None)

    # I might adapt this test case to also test a hostname other
    # than localhost.
    def testJoinAndMessageChannelWithNameOtherThanMyChannel(self):
        self.irc_factory.expects(pmock.once()).method("registerChannel")
        chan = ikarus.channel.Channel(self.irc_factory, "coolpeopleonly")
        user = pmock.Mock()
        user.name = "nobody"
        user.nick = "clevernickname"
        user.joined_channels = []
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":clevernickname!~nobody@localhost. JOIN :#coolpeopleonly"))
        self.irc_factory.users.append(user)
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 353 clevernickname = #coolpeopleonly :clevernickname"))
        chan.joinUser(user)

        other_user = pmock.Mock()
        other_user.name = "someone_else"
        other_user.nick = "spam_and_eggs"
        other_user.joined_channels = []
        other_user.expects(pmock.once()).sendLine(pmock.eq(
                ":spam_and_eggs!~someone_else@localhost. JOIN :#coolpeopleonly"))
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":spam_and_eggs!~someone_else@localhost. JOIN :#coolpeopleonly"))
        other_user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 353 spam_and_eggs = #coolpeopleonly :clevernickname spam_and_eggs"))
        self.irc_factory.users.append(other_user)
        chan.joinUser(other_user)

        user.expects(pmock.once()).sendLine(pmock.eq(
                ":spam_and_eggs!~someone_else@localhost. PRIVMSG #coolpeopleonly :Hi There!"))
        chan.privMsg(other_user, "Hi There!")

    def testFindUser(self):
        user = pmock.Mock()
        user.nick = "orospakr"
        user.name = "orospakr"
        user.joined_channels = []
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":orospakr!~orospakr@localhost. JOIN :#mychannel"))
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 353 orospakr = #mychannel :orospakr"))
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
        self.joining_user.joined_channels = []
        self.joining_user.expects(pmock.once()).sendLine(pmock.eq(
                ":somefella!~sfella@localhost. JOIN :#mychannel"))
        self.joining_user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 353 somefella = #mychannel :somefella"))
        self.irc_factory.users.append(self.joining_user)
        self.c.joinUser(self.joining_user)
        self.joining_user.verify()

    def testInformJoin(self):
        self.listening_user = pmock.Mock()
        self.listening_user.nick = "listening_guy"
        self.listening_user.name = "listening_guy"
        self.listening_user.joined_channels = []
        self.listening_user.expects(pmock.once()).sendLine(pmock.eq(
                ":listening_guy!~listening_guy@localhost. JOIN :#mychannel"))
        self.listening_user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 353 listening_guy = #mychannel :listening_guy"))
        self.listening_user.expects(pmock.once()).sendLine(pmock.eq(
                ":orospakr!~orospakr@localhost. JOIN :#mychannel"))
        self.irc_factory.users.append(self.listening_user)

        self.user = pmock.Mock()
        self.user.nick = "orospakr"
        self.user.name = "orospakr"
        self.user.joined_channels = []
        self.user.expects(pmock.once()).sendLine(pmock.eq(
                ":orospakr!~orospakr@localhost. JOIN :#mychannel"))
        self.user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 353 orospakr = #mychannel :listening_guy orospakr"))
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

    def testMessageFromNonJoinedUser(self):
        user = pmock.Mock()
        user.nick = "someone"
        user.name = "sone"
        user.joined_channels = []
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":someone!~sone@localhost. JOIN :#mychannel"))
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 353 someone = #mychannel :someone"))
        self.c.joinUser(user)
        naughty_user = pmock.Mock()
        naughty_user.nick = "naughtyguy"
        naughty_user.name = "nguy"
        # the following message should never arrive...
        user.expects(pmock.never()).method("sendLine")
        self.c.privMsg(naughty_user, "You shouldn't be able to see this.")
        user.verify()

    def testPartUser(self):
        user = pmock.Mock()
        user.nick = "someone"
        user.name = "sone"
        user.joined_channels = []
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":someone!~sone@localhost. JOIN :#mychannel"))
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 353 someone = #mychannel :someone"))
        self.c.joinUser(user)

        user.expects(pmock.once()).sendLine(pmock.eq(
                ":someone!~sone@localhost. PART #mychannel :Toodles!"))
        self.c.partUser(user, "Toodles!")
        user.verify()

    def testPartUserThatHasNotJoinedThisChannel(self):
        #        :localhost. 442 orospakr #wheeeee :You're not on that channel
        # this should perhaps be just tested in ChannelTest, not here (because
        # the decision being tested is there, not here)

        user = pmock.Mock()
        user.nick = "unjoined_person"
        user.name = "ujp"
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 422 unjoined_person #mychannel :You're not on that channel."))
        self.c.partUser(user, "Bye.")
        user.verify()

    def testWhoQuery(self):
        user = pmock.Mock()
        user.nick = "first_person"
        user.name = "fp"
        user.joined_channels = []
        user.expects(pmock.once()).sendLine(pmock.eq(':first_person!~fp@localhost. JOIN :#mychannel'))
#        user.expects(pmock.once()).sendLine(pmock.eq(':localhost.
        user.expects(pmock.once()).sendLine(pmock.eq(':localhost. 353 first_person = #mychannel :first_person'))
        self.c.joinUser(user)

        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 352 first_person #mychannel fp localhost. irc.localnet first_person H :0 Andrew Clunis"))
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 315 first_person #mychannel :End of /WHO list."))
        self.c.whoQuery(user)

        user2 = pmock.Mock()
        user2.nick = "orospakr"
        user2.name = "orospakr"
        user2.joined_channels = []
        user.expects(pmock.once()).sendLine(pmock.eq(':orospakr!~orospakr@localhost. JOIN :#mychannel'))
        user2.expects(pmock.once()).sendLine(pmock.eq(':orospakr!~orospakr@localhost. JOIN :#mychannel'))
        user2.expects(pmock.once()).sendLine(pmock.eq(':localhost. 353 orospakr = #mychannel :first_person orospakr'))
        self.c.joinUser(user2)

        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 352 first_person #mychannel fp localhost. irc.localnet first_person H :0 Andrew Clunis"))
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 352 first_person #mychannel orospakr localhost. irc.localnet orospakr H :0 Andrew Clunis"))
        user.expects(pmock.once()).sendLine(pmock.eq(
                ":localhost. 315 first_person #mychannel :End of /WHO list."))
        self.c.whoQuery(user)

        user.verify()
        user2.verify()
