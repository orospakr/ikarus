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
    path of delegation from this object to the others.

    The Integration tests need to be factored out into an Integration
    test suite, and this test case would have mocked collaborator tests only.
    '''

    def getOutputtedLines(self):
        return self.tr.value().split("\r\n")

    def getLastOutputtedLine(self):
        # not sure why, but I always get a blank line at the end of the value
        # from the string transport.
        return self.getOutputtedLines()[-2]

    def getOutputtedLines2(self):
        return self.tr2.value().split("\r\n")

    def getLastOutputtedLine2(self):
        # not sure why, but I always get a blank line at the end of the value
        # from the string transport.
        return self.getOutputtedLines2()[-2]

    def getOutputtedLines3(self):
        return self.tr3.value().split("\r\n")

    def getLastOutputtedLine3(self):
        # not sure why, but I always get a blank line at the end of the value
        # from the string transport.
        return self.getOutputtedLines3()[-2]

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

        self.i3 = self.factory.buildProtocol(('127.0.0.1', 6667))
        self.tr3 = proto_helpers.StringTransport()
        self.i3.makeConnection(self.tr3)
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
        self.failUnlessEqual(self.getLastOutputtedLine(), ":localhost. 461 * USER :Not enough parameters.")

    def testMalformedSetUserAlmostLongEnough(self):
        self.i.lineReceived("USER whee whee whee")
        self.failUnlessEqual(self.getLastOutputtedLine(), ":localhost. 461 * USER :Not enough parameters.")

    def testJoinANewChannel(self):
        self.testLogIn()
        self.i.lineReceived("JOIN #my_channel")
        # I should test the presence of channel logged in info here, once it exists
        # expect callback here.
        self.failUnlessEqual(self.getLastOutputtedLine(), ":orospakr!~orospakr@localhost. JOIN :#my_channel")

    def testMalformedChannelJoin(self):
        self.testLogIn()
        self.i.lineReceived("JOIN")
        self.failUnlessEqual(self.getLastOutputtedLine(),
                             ":localhost. 461 * JOIN :Not enough parameters.")

    def testMalformedChannelPrivmsg(self):
        self.testJoinANewChannel()
        self.i.lineReceived("PRIVMSG #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(),
                             ":localhost. 461 * PRIVMSG :Not enough parameters.")

    def testJoinBeforeLoginShouldFail(self):
        self.i.lineReceived("JOIN #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(),
                             ":localhost. 451 JOIN :You have not registered.")

    def testNickInUseAlreadyLoggedIn(self):
        self.testLogIn()
        self.i2.lineReceived("NICK orospakr")
        self.failUnlessEqual(self.getLastOutputtedLine2(),
                             ":localhost. 433 * orospakr :Nickname is already in use.")

    def testPart(self):
        # make sure that the user is removed from the channel and does not receive
        # new messages.
        self.testTwoJoinAChannel()
        self.i.lineReceived("PART #mychannel :Bye bye.")
        self.failUnlessEqual(self.getLastOutputtedLine(),
                             ":orospakr!~orospakr@localhost. PART #mychannel :Bye bye.")
        self.failUnlessEqual(self.getLastOutputtedLine2(),
                             ":orospakr!~orospakr@localhost. PART #mychannel :Bye bye.")
        self.i.lineReceived("PRIVMSG #mychannel :Lorem Ipsum...")
        self.failIfEqual(self.getLastOutputtedLine2(),
                         ":orospakr!~orospakr@localhost. PRIVMSG #mychannel :Lorem Ipsum...")

    def testMalformedPart(self):
        self.testTwoJoinAChannel()
        self.i.lineReceived("PART")
        self.failUnlessEqual(self.getLastOutputtedLine(),
                             ":localhost. 461 orospakr PART :Not enough parameters.")

    def testPartFromThreeChannels(self):
        # this only tests the reception of the part message.  We assume that
        # if we got that, the test above tested the rest of the removal logic
        # sufficiently.
        self.testLogIn()
        self.i.lineReceived("JOIN #firstchannel")
        self.i.lineReceived("JOIN #mychannel")
        self.i.lineReceived("JOIN #another_channel")
        self.i.lineReceived("PART #firstchannel,#mychannel,#another_channel :I'm outta here!")
        lines = self.getOutputtedLines()
        self.failUnlessEqual(lines[-3],
                             ":orospakr!~orospakr@localhost. PART #mychannel :I'm outta here!")
        self.failUnlessEqual(lines[-2],
                             ":orospakr!~orospakr@localhost. PART #another_channel :I'm outta here!")

#     actually, I'm not going to bother with this.  The RFC says the colon
#     must always be there, so why bother making it flexible just because dancer is?
#     def testPartMalformedMessageMissingColon(self):
#         self.testLogIn()
#         self.i.lineReceived("JOIN #mychannel")
#         self.i.lineReceived("PART #mychannel no colon, but it should still work!")
#         self.failUnlessEqual(self.getLastOutputtedLine(),
#                              ":orospakr!~orospakr@localhost. PART #mychannel :no colon, but it should still work!")

    def testPartFromNonExistentChannel(self):
        # this should be tested in this testcase.
        self.testLogIn()
        self.i.lineReceived("PART #doesnotexist")
        self.failUnlessEqual(self.getLastOutputtedLine(),
                             ":localhost. 403 orospakr #doesnotexist :That channel doesn't exist.")

    def testQuit(self):
        # make sure user is parted from all channels, as above, and can reconnect
        # without getting incorrect "nickname in use messages"
        self.testTwoJoinAChannel()
        self.failIfEqual(None,
                         self.factory.getUserByNick("my_second_guy"))
        self.i2.lineReceived("QUIT :bye bye!")
        self.failUnlessEqual(self.getLastOutputtedLine(),
                             ":my_second_guy!~msg@localhost. QUIT :bye bye!")
        self.failUnlessEqual(self.getLastOutputtedLine2(),
                             "ERROR :Closing Link: my_second_guy (Client Quit)")

        # also verify that the quitted user does not receive
        # messages for a channel they joined before they quit.
        # the idea here is to test that the channel's list of users
        # was updated on user quit.
        self.i2.lineReceived("PRIVMSG #mychannel :msg shouldn't be able to see this.")
        self.failIfEqual(self.getLastOutputtedLine(),
                         ":my_second_guy!~msg@localhost. PRIVMSG #mychannel :msg shouldn't be able to see this.")

    def testShouldBeAbleToUseNickOfQuittedUser(self):
        # the idea here is to test that the IRC factory of users
        # was updated on user quit.
        # TODO obviously, there should be a different story here
        # when the quitted user is registered...
        self.testQuit()
        self.i3.lineReceived("NICK my_second_guy")
#        self.i3.lineReceived("USER msg msg lolpppoe-lolsite.dk ircserver.awesome.org :My Second guy.")
        self.failIfEqual(self.getLastOutputtedLine3(),
                         ":localhost. 433 * my_second_guy :Nickname is already in use.")

    def testQuitDoesNotSendMultipleQuitMessagesToEachUser(self):
        # right now there is a silly bug, where, because transmitting the QUIT message
        # is delegated to all the channels that the user is joined to,
        # any user that is in more than one channel with the quitting user
        # will get multiple quits. oops!
        self.testLogIn()
        self.i2.lineReceived("NICK secondguy")
        self.i2.lineReceived("USER sguy secondguy.myisp.ca localhost. :Someone.")
        self.i.lineReceived("JOIN #somewhere")
        self.i2.lineReceived("JOIN #somewhere")
        self.i.lineReceived("JOIN #somewhere_else")
        self.i2.lineReceived("JOIN #somewhere_else")
        self.i2.lineReceived("QUIT :hasta la vista!")

        lines = self.getOutputtedLines()

        # check to see if the first user got an extra QUIT line back.
        first_returned_statement = lines[-3].split(" ")[1]
        second_returned_statement = lines[-2].split(" ")[1]
        logging.debug(first_returned_statement)
        self.failIfEqual(first_returned_statement, "QUIT")
        # make sure the single message does arrive.
        self.failUnlessEqual(second_returned_statement, "QUIT")

    def testConnectionLost(self):
        pass

    def testChanneListIsUpdatedOnJoin(self):
        def channelToName(c):
            return c.name
        self.testLogIn()
        chans = ["mychannel", "somechannel", "anotherplace"]
        for c in chans:
            self.i.lineReceived("JOIN #%s" % c)
        joined_channel_names = map(channelToName, self.i.joined_channels)
        for c in chans:
            self.failUnlessEqual(True, c in joined_channel_names)

    def testTwoJoinAChannel(self):
        self.testLogIn()
        self.i2.lineReceived("NICK my_second_guy")
        self.i2.lineReceived("USER msg localhost :Another Dude")
        self.failIfEqual(None,
                         self.factory.getUserByNick('my_second_guy'))
        self.i.lineReceived("JOIN #mychannel")
        self.i2.lineReceived("JOIN #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(), ":my_second_guy!~msg@localhost. JOIN :#mychannel")

    def testUserThatHasOnlyDoneNickAndNotUserCanBePunted(self):
        # test that a second session that calls NICK for the
        # same name can punt off another session that has already
        # called nick, but has not yet called USER.
        pass

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

    def testChannelPartUnjoinedUser(self):
        self.testLogIn()
        self.i2.lineReceived("NICK my_second_guy")
        self.i2.lineReceived("USER msg localhost :Someone else.")
        self.i2.lineReceived("JOIN #channel")
        self.i.lineReceived("PART #channel")
        self.failUnlessEqual(self.getLastOutputtedLine(),
                             ":localhost. 422 orospakr #channel :You're not on that channel.")

