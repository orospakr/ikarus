from twisted.trial import unittest
from twisted.test import proto_helpers

import twisted.internet
import twisted.internet.reactor

import ikarus.irc
import logging

class IRCTestCase(unittest.TestCase):
    '''
    Tests the IRC class.  The IRC class represents the user<->server
    protocol.

    This also contains more general integration tests, based on the general
    path of delegation from this object to the others.'''

    def getOutputtedLines(self):
        return self.tr.value().split("\r\n")

    def getLastOutputtedLine(self):
        # not sure why, but I always get a blank line at the end of the value
        # from the string transport.
        return self.getOutputtedLines()[-2]

    def setUp(self):

        self.factory = ikarus.irc.IRCFactory()
        self.i = self.factory.buildProtocol(('127.0.0.1', 6667))
        self.i2 = self.factory.buildProtocol(('127.0.0.1', 6667))
        #twisted.internet.reactor.listenTCP(6667, self.factory, interface="127.0.0.1")

        #twisted.internet.reactor.iterate()
        self.tr = proto_helpers.StringTransport()
        self.tr2 = proto_helpers.StringTransport()
        self.i.makeConnection(self.tr)
        self.i2.makeConnection(self.tr2)
        #self.i.service = ikarus.irc.IRCFactory()
        #self.i.makeConnection(self.i)
        #self.f.protocl = ikarus.irc.IRC

    def testInstantiate(self):
        self.failIfEqual(self.i, None)

    def testSetNick(self):
        self.i.lineReceived("NICK orospakr")
        self.failUnlessEqual(self.i.nick, "orospakr")
        self.i.lineReceived("NICK smartyman")
        self.failUnlessEqual(self.i.nick, "smartyman")

    def testMalformedSetNick(self):
        self.i.lineReceived("NICK")
        input = self.getLastOutputtedLine()
        self.failUnlessEqual(input, ":localhost. 431  :No nickname given")

    def testSetUser(self):
        self.i.lineReceived("USER orospakr orospakrshostname localhost :Andrew Clunis")
        self.failUnlessEqual(self.i.name, "orospakr")

    def testConnectionOpened(self):
        self.i.lineReceived("NOTICE AUTH :*** Looking up your hostname...")
        self.i.lineReceived("NOTICE AUTH :*** Found your hostname")

    def testLogIn(self):
        self.i.lineReceived("NICK orospakr")
        self.i.lineReceived("USER orospakr blahblah-pppoe.myisp.ca ircserver.awesome.org :Andrew Clunis")
        input = self.getOutputtedLines()
        self.failUnlessEqual(input[2], ":localhost. 001 orospakr :Welcome to $hostname.")
        self.failUnlessEqual(input[3], ":localhost. 002 orospakr :Your host is $hostname running version Ikarus")
        self.failUnlessEqual(input[4], "NOTICE orospakr :*** Your host is $hostname running version Ikarus")
        self.failUnlessEqual(self.i.logged_in, True)

    def testConnectionNotOpenedWithOnlyNick(self):
        self.i.lineReceived("NICK orospakr")
        self.failIfEqual(self.i.logged_in, True)

    def testConnectionNotOpenedWithOnlyUser(self):
        self.i.lineReceived("USER orospakr orospakr localhost :Andrew Clunis")
        self.failIfEqual(self.i.logged_in, True)

    def testMalformedSetUser(self):
        self.i.lineReceived("USER")
        self.failUnlessEqual(self.getLastOutputtedLine(), ":localhost. 461 * USER :Not enough parameters")

    def testMalformedSetUserAlmostLongEnough(self):
        self.i.lineReceived("USER whee whee whee")
        self.failUnlessEqual(self.getLastOutputtedLine(), ":localhost. 461 * USER :Not enough parameters")

    def testJoinANewChannel(self):
        self.testLogIn()
        self.i.lineReceived("JOIN #my_channel")
        # I should test the presence of channel logged in info here, once it exists
        # expect callback here.
        self.failUnlessEqual(self.getLastOutputtedLine(), ":orospakr!~orospakr@localhost. JOIN :#my_channel")

    def testMalformedChannelJoin(self):
        self.testLogIn()
        self.i.lineReceived("JOIN")
        self.failUnlessEqual(self.getLastOutputtedLine(), ":localhost. 461 * JOIN :Not enough parameters")

    def testMalformedChannelPrivmsg(self):
        self.testJoinANewChannel()
        self.i.lineReceived("PRIVMSG #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(), ":localhost. 461 * PRIVMSG :Not enough parameters")

    def testJoinBeforeLoginShouldFail(self):
        self.i.lineReceived("JOIN #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(), ":localhost. 451 JOIN :You have not registered")

    def testNickInUse(self):
        # this too...
        pass

    def testPart(self):
        # make sure that the user is removed from the channel and does not receive
        # new messages.
        pass

    def testQuit(self):
        # make sure user is parted from all channels, as above.
        pass

    def testJoinAnExistingChannel(self):
        pass

    def testTwoJoinAChannel(self):
        self.testLogIn()
        self.i2.lineReceived("NICK my_second_guy")
        self.i2.lineReceived("USER msg localhost :Another Dude")
        self.i.lineReceived("JOIN #mychannel")
        self.i2.lineReceived("JOIN #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(), ":my_second_guy!~msg@localhost. JOIN :#mychannel")

    def testGetChannelByName(self):
        self.testJoinANewChannel()
        channel = self.factory.getChannelByName("my_channel")
        self.failUnlessEqual(channel.name, "my_channel")

    def testGetChannelByNameDoesNotExist(self):
        channel = self.factory.getChannelByName("wheetotallynothere")
        self.failUnlessEqual(channel, None)

    def testOneSpeaksToAnotherOnOneChannel(self):
        self.testTwoJoinAChannel()
        self.i.lineReceived("PRIVMSG #mychannel :Lorem Ipsum sit Dolor.")
        input2 = self.tr2.value().split("\r\n")
        self.failUnlessEqual(input2[-2], ":orospakr!~orospakr@localhost. PRIVMSG #mychannel :Lorem Ipsum sit Dolor.")
