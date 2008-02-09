from twisted.trial import unittest
from twisted.test import proto_helpers

import twisted.internet
import twisted.internet.reactor

import ikarus.irc
import logging

class IRCTestCase(unittest.TestCase):
    def setUp(self):

        self.factory = ikarus.irc.IRCFactory()
        self.i = self.factory.buildProtocol(('127.0.0.1', 6667))
        #twisted.internet.reactor.listenTCP(6667, self.factory, interface="127.0.0.1")

        #twisted.internet.reactor.iterate()
        self.tr = proto_helpers.StringTransport()
        self.i.makeConnection(self.tr)
        #self.i.service = ikarus.irc.IRCFactory()
        #self.i.makeConnection(self.i)
        #self.f.protocl = ikarus.irc.IRC

    def testInstantiate(self):
        self.failIfEqual(self.i, None)

    def testEcho(self):
        self.i.lineReceived("whee")
        #twisted.internet.reactor.iterate()
        self.assertEquals(self.tr.value(), "whee\r\n")

    def testAllEcho(self):
        self.i2 = self.factory.buildProtocol(('127.0.0.1', 6667))
        self.tr2 = proto_helpers.StringTransport()
        self.i2.makeConnection(self.tr2)

        self.i.lineReceived("omgwtfbbq")
        self.assertEquals(self.tr2.value(), "omgwtfbbq\r\n")


#     def testNickChange(self):
#         i.lineReceived("NICK orospakr")
#         self.failUnlessEqual(i.nick, "orospakr")
#         i.lineReceived("NICK smartyman")
#         self.failUnlessEqual(i.nick, "smartyman")

#    def testPing(self):
#        i.lineReceived("PING irc.awesome.ca.")

    def openConnection(self):
        pass
        #self.i.makeConnection()
        # RECEIVE NOTICE AUTH :*** Looking up your hostname...


