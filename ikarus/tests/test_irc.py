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

    def getOutputtedLines(self, num):
        return self.trs[num].value().split("\r\n")

    def getLastOutputtedLine(self, num):
        # not sure why, but I always get a blank line at the end of the value
        # from the string transport.
        return self.getOutputtedLines(num)[-2]

    def connectAnIRCClient(self):
        new_user = self.factory.buildProtocol(('127.0.0.1', 6667))
        self.users.append(new_user)
        new_tr = proto_helpers.StringTransport()
        self.trs.append(new_tr)
        new_user.makeConnection(new_tr)

    def setUp(self):
        self.users = []
        self.trs = []
        self.factory = ikarus.irc.IRCFactory()
        for num in range(0, 3):
            self.connectAnIRCClient()

    def testInstantiate(self):
        self.failIfEqual(self.users[0], None)

    def setNick(self, u, nickname):
        u.lineReceived("NICK %s" % nickname)

    def testSetNick(self):
        self.setNick(self.users[0], "orospakr")
        self.failUnlessEqual(self.users[0].nick, "orospakr")
        self.setNick(self.users[0], "smartyman")
        self.failUnlessEqual(self.users[0].nick, "smartyman")

    def testMalformedSetNick(self):
        self.users[0].lineReceived("NICK")
        input = self.getLastOutputtedLine(0)
        self.failUnlessEqual(input, ":localhost. 431  :No nickname given")

    def testSetUser(self):
        self.users[0].lineReceived("USER orospakr orospakrshostname localhost :Andrew Clunis")
        self.failUnlessEqual(self.users[0].name, "orospakr")

    def testConnectionOpened(self):
        self.users[0].lineReceived("NOTICE AUTH :*** Looking up your hostname...")
        self.users[0].lineReceived("NOTICE AUTH :*** Found your hostname")

    def testLogIn(self):
        self.setNick(self.users[0], "orospakr")
        self.users[0].lineReceived("USER orospakr blahblah-pppoe.myisp.ca ircserver.awesome.org :Andrew Clunis")
        input = self.getOutputtedLines(0)
        self.failUnlessEqual(input[2], ":localhost. 001 orospakr :Welcome to $hostname.")
        self.failUnlessEqual(input[3], ":localhost. 002 orospakr :Your host is $hostname running version Ikarus")
        self.failUnlessEqual(input[4], "NOTICE orospakr :*** Your host is $hostname running version Ikarus")
        self.failUnlessEqual(self.users[0].logged_in, True)

    def testConnectionNotOpenedWithOnlyNick(self):
        self.setNick(self.users[0], "orospakr")
        self.failIfEqual(self.users[0].logged_in, True)

    def testConnectionNotOpenedWithOnlyUser(self):
        self.users[0].lineReceived("USER orospakr orospakr localhost :Andrew Clunis")
        self.failIfEqual(self.users[0].logged_in, True)

    def testMalformedSetUser(self):
        self.users[0].lineReceived("USER")
        self.failUnlessEqual(self.getLastOutputtedLine(0), ":localhost. 461 * USER :Not enough parameters.")

    def testMalformedSetUserAlmostLongEnough(self):
        self.users[0].lineReceived("USER whee whee whee")
        self.failUnlessEqual(self.getLastOutputtedLine(0), ":localhost. 461 * USER :Not enough parameters.")

    def testJoinANewChannel(self):
        self.testLogIn()
        self.users[0].lineReceived("JOIN #my_channel")
        # I should test the presence of channel logged in info here, once it exists
        # expect callback here.
        self.failUnlessEqual(self.getLastOutputtedLine(0), ":orospakr!~orospakr@localhost. JOIN :#my_channel")

    def testMalformedChannelJoin(self):
        self.testLogIn()
        self.users[0].lineReceived("JOIN")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 461 * JOIN :Not enough parameters.")

    def testMalformedChannelPrivmsg(self):
        self.testJoinANewChannel()
        self.users[0].lineReceived("PRIVMSG #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 461 * PRIVMSG :Not enough parameters.")

    def testJoinBeforeLoginShouldFail(self):
        self.users[0].lineReceived("JOIN #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 451 JOIN :You have not registered.")

    def testNickInUseAlreadyLoggedIn(self):
        self.testLogIn()
        self.setNick(self.users[1], "orospakr")
        self.failUnlessEqual(self.getLastOutputtedLine(1),
                             ":localhost. 433 * orospakr :Nickname is already in use.")

    def testPart(self):
        # make sure that the user is removed from the channel and does not receive
        # new messages.
        self.testTwoJoinAChannel()
        self.users[0].lineReceived("PART #mychannel :Bye bye.")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":orospakr!~orospakr@localhost. PART #mychannel :Bye bye.")
        self.failUnlessEqual(self.getLastOutputtedLine(1),
                             ":orospakr!~orospakr@localhost. PART #mychannel :Bye bye.")
        self.users[0].lineReceived("PRIVMSG #mychannel :Lorem Ipsum...")
        self.failIfEqual(self.getLastOutputtedLine(1),
                         ":orospakr!~orospakr@localhost. PRIVMSG #mychannel :Lorem Ipsum...")

    def testMalformedPart(self):
        self.testTwoJoinAChannel()
        self.users[0].lineReceived("PART")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 461 orospakr PART :Not enough parameters.")

    def testPartFromThreeChannels(self):
        # this only tests the reception of the part message.  We assume that
        # if we got that, the test above tested the rest of the removal logic
        # sufficiently.
        self.testLogIn()
        self.users[0].lineReceived("JOIN #firstchannel")
        self.users[0].lineReceived("JOIN #mychannel")
        self.users[0].lineReceived("JOIN #another_channel")
        self.users[0].lineReceived("PART #firstchannel,#mychannel,#another_channel :I'm outta here!")
        lines = self.getOutputtedLines(0)
        self.failUnlessEqual(lines[-3],
                             ":orospakr!~orospakr@localhost. PART #mychannel :I'm outta here!")
        self.failUnlessEqual(lines[-2],
                             ":orospakr!~orospakr@localhost. PART #another_channel :I'm outta here!")

#     actually, I'm not going to bother with this.  The RFC says the colon
#     must always be there, so why bother making it flexible just because dancer is?
#     def testPartMalformedMessageMissingColon(self):
#         self.testLogIn()
#         self.users[0].lineReceived("JOIN #mychannel")
#         self.users[0].lineReceived("PART #mychannel no colon, but it should still work!")
#         self.failUnlessEqual(self.getLastOutputtedLine(0),
#                              ":orospakr!~orospakr@localhost. PART #mychannel :no colon, but it should still work!")

    def testPartFromNonExistentChannel(self):
        # this should be tested in this testcase.
        self.testLogIn()
        self.users[0].lineReceived("PART #doesnotexist")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 403 orospakr #doesnotexist :That channel doesn't exist.")

    def testQuit(self):
        # make sure user is parted from all channels, as above, and can reconnect
        # without getting incorrect "nickname in use messages"
        self.testTwoJoinAChannel()
        self.failIfEqual(None,
                         self.factory.getUserByNick("my_second_guy"))
        self.users[1].lineReceived("QUIT :bye bye!")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":my_second_guy!~msg@localhost. QUIT :bye bye!")
        self.failUnlessEqual(self.getLastOutputtedLine(1),
                             "ERROR :Closing Link: my_second_guy (Client Quit)")

        # also verify that the quitted user does not receive
        # messages for a channel they joined before they quit.
        # the idea here is to test that the channel's list of users
        # was updated on user quit.
        self.users[1].lineReceived("PRIVMSG #mychannel :msg shouldn't be able to see this.")
        self.failIfEqual(self.getLastOutputtedLine(0),
                         ":my_second_guy!~msg@localhost. PRIVMSG #mychannel :msg shouldn't be able to see this.")

    def testShouldBeAbleToUseNickOfQuittedUser(self):
        # the idea here is to test that the IRC factory of users
        # was updated on user quit.
        # TODO obviously, there should be a different story here
        # when the quitted user is registered...
        self.testQuit()
        self.setNick(self.users[2], "my_second_guy")
#        self.i3.lineReceived("USER msg msg lolpppoe-lolsite.dk ircserver.awesome.org :My Second guy.")
        self.failIfEqual(self.getLastOutputtedLine(2),
                         ":localhost. 433 * my_second_guy :Nickname is already in use.")

    def testQuitDoesNotSendMultipleQuitMessagesToEachUser(self):
        # right now there is a silly bug, where, because transmitting the QUIT message
        # is delegated to all the channels that the user is joined to,
        # any user that is in more than one channel with the quitting user
        # will get multiple quits. oops!
        self.testLogIn()
        self.setNick(self.users[1], "secondguy")
        self.users[1].lineReceived("USER sguy secondguy.myisp.ca localhost. :Someone.")
        self.users[0].lineReceived("JOIN #somewhere")
        self.users[1].lineReceived("JOIN #somewhere")
        self.users[0].lineReceived("JOIN #somewhere_else")
        self.users[1].lineReceived("JOIN #somewhere_else")
        self.users[1].lineReceived("QUIT :hasta la vista!")

        lines = self.getOutputtedLines(0)

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
            self.users[0].lineReceived("JOIN #%s" % c)
        joined_channel_names = map(channelToName, self.users[0].joined_channels)
        for c in chans:
            self.failUnlessEqual(True, c in joined_channel_names)

    def testTwoJoinAChannel(self):
        self.testLogIn()
        self.setNick(self.users[1], "my_second_guy")
        self.users[1].lineReceived("USER msg localhost :Another Dude")
        self.failIfEqual(None,
                         self.factory.getUserByNick('my_second_guy'))
        self.users[0].lineReceived("JOIN #mychannel")
        self.users[1].lineReceived("JOIN #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(0), ":my_second_guy!~msg@localhost. JOIN :#mychannel")

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
        self.users[0].lineReceived("PRIVMSG #mychannel :Lorem Ipsum sit Dolor.")
        input2 = self.trs[1].value().split("\r\n")
        self.failUnlessEqual(input2[-2], ":orospakr!~orospakr@localhost. PRIVMSG #mychannel :Lorem Ipsum sit Dolor.")

    def testChannelPartUnjoinedUser(self):
        self.testLogIn()
        self.setNick(self.users[1], "my_second_guy")
        self.users[1].lineReceived("USER msg localhost :Someone else.")
        self.users[1].lineReceived("JOIN #channel")
        self.users[0].lineReceived("PART #channel")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 422 orospakr #channel :You're not on that channel.")

