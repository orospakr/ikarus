from twisted.trial import unittest
from twisted.test import proto_helpers

import twisted.internet
import twisted.internet.reactor

import ikarus.irc
import logging

class IRCTestCase(unittest.TestCase):
    '''
    Tests the IRC class.  The IRC class represents the user<->server
    protocol.'''

    connection_registered = [
        ":localhost. 001 orospakr :Welcome to the Ikarus IRC-powered Test Net",
        ":localhost. 002 orospakr :Your host is localhost.",
#        "NOTICE orospakr :*** Your host is localhost.[localhost./6667], running version dancer-ircd-1.0.36",
        ":localhost. 003 orospakr :This server was cobbled together Thu Nov  9 03:18:35 UTC 2006",
        ":localhost. 004 orospakr localhost. dancer-ircd-1.0.36 aAbBcCdDeEfFGhHiIjkKlLmMnNopPQrRsStuUvVwWxXyYzZ0123459*@ bcdefFhiIklmnoPqstv",
        ":localhost. 005 orospakr MODES=4 CHANLIMIT=#:20 NICKLEN=16 USERLEN=10 HOSTLEN=63 TOPICLEN=450 KICKLEN=450 CHANNELLEN=30 KEYLEN=23 CHANTYPES=# PREFIX=(ov)@+ CASEMAPPING=ascii CAPAB IRCD=dancer :are available on this server"
]

    def getLastOutputtedLine(self):
        #logging.debug(self.tr.value().split("\r\n"))
        return self.tr.value().split("\r\n")[-2]

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

    def testSetNick(self):
        self.i.lineReceived("NICK orospakr")
        self.failUnlessEqual(self.i.nick, "orospakr")
        self.i.lineReceived("NICK smartyman")
        self.failUnlessEqual(self.i.nick, "smartyman")

    def testMalformedSetNick(self):
        '''ANDREW START HERE AND LEARN WHAT THE DEAL IS WITH ERRBACKS'''
        pass

    def testSetUser(self):
        self.i.lineReceived("USER orospakr orospakrshostname localhost :Andrew Clunis")
        self.failUnlessEqual(self.i.user_name, "orospakr")

    def testConnectionOpened(self):
        self.i.lineReceived("NICK orospakr")
        self.i.lineReceived("USER orospakr orospakr localhost :Andrew Clunis")
        # check to see that the user is logged in
        self.failUnlessEqual(self.i.logged_in, True)

    def testConnectionNotOpenedWithOnlyNick(self):
        self.i.lineReceived("NICK orospakr")
        self.failIfEqual(self.i.logged_in, True)

    def testConnectionNotOpenedWithOnlyUser(self):
        self.i.lineReceived("USER orospakr orospakr localhost :Andrew Clunis")
        self.failIfEqual(self.i.logged_in, True)


