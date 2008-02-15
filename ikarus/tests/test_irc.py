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

    def getLastOutputtedLine(self):
        #logging.debug(self.tr.value().split("\r\n"))
        return self.tr.value().split("\r\n")[-2]

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
        input = self.tr.value().split("\r\n")[-2] # argh, doing [-2] is bad!  why is a blank line arriving?
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
        input = self.tr.value().split("\r\n")
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
        input = self.tr.value().split("\r\n")
        self.failUnlessEqual(input[-2], ":localhost. 461 * USER :Not enough parameters")

    def testMalformedSetUserAlmostLongEnough(self):
        self.i.lineReceived("USER whee whee whee")
        input = self.tr.value().split("\r\n")
        self.failUnlessEqual(input[-2], ":localhost. 461 * USER :Not enough parameters")

    def testJoinANewChannel(self):
        self.testLogIn()
        self.i.lineReceived("JOIN #my_channel")
        # I should test the presence of channel logged in info here, once it exists
        # expect callback here.
        input = self.tr.value().split("\r\n")
        self.failUnlessEqual(input[-2], ":orospakr!~orospakr@localhost. JOIN :#my_channel")

    def testMalformedChannelJoin(self):
        # do this next!
        pass

    def testJoinBeforeLoginShouldFail(self):
        # and this!
        pass

    def testNickInUse(self):
        # this too...
        pass

    def testJoinAnExistingChannel(self):
        pass

    def testTwoJoinAChannel(self):
        self.testLogIn()
        self.i2.lineReceived("NICK my_second_guy")
        self.i2.lineReceived("USER msg localhost :Another Dude")
        self.i.lineReceived("JOIN #mychannel")
        self.i2.lineReceived("JOIN #mychannel")
        input = self.tr.value().split("\r\n")
        # check to see that the first user sees the second one join the channel
        self.failUnlessEqual(input[-2], ":my_second_guy!~msg@localhost. JOIN :#my_channel")
        # I should test the presence (and lack thereof) of channel logged in info here,
        # once it exists.
        # obviously not done yet...

#     def testGetChannelByName(self):
#         channel = self.factory.getChannelByName("mychannel")
#         self.failUnlessEqual(channel.name, "mychannel")

    def testGetChannelByNameDoesNotExist(self):
        channel = self.factory.getChannelByName("wheetotallynothere")
        self.failUnlessEqual(channel, None)

#     def testOneSpeaksToAnotherOnOneChannel(self):
#         self.testTwoJoinAChannel()
#         input = self.tr.value().split("\r\n")
#         input2 = self.tr2.value().split("\r\n")
#         self.i.lineReceived("PRIVMSG #mychannel :Lorem Ipsum sit Dolor.")
#         self.failUnlessEqual(input2[-2], ":orospakr!~orospakr@localhost. PRIVMSG #mychannel :Lorem Ipsum sit Dolor.")
