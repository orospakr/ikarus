from twisted.trial import unittest
from twisted.test import proto_helpers

import twisted.internet
import twisted.internet.reactor
import twisted.python.failure
from twisted.internet import error

import ikarus.irc
import logging

# in the form: nick, username, real name.
user_fixtures = [
    ["orospakr", "aclunis", "Andrew Clunis"],
    ["karfai", "dkelly", "Don Kelly"],
    ["norbert", "nwinklareth", "Norbert Winklareth"]
    ]

class IRCTestCase(unittest.TestCase):
    '''
    Tests the IRC class.  The IRC class represents the user<->server
    protocol.

    This also contains more general integration tests, based on the general
    path of delegation from this object to the others.

    The Integration tests need to be factored out into an Integration
    test suite, and this test case would have mocked collaborator tests only.
    '''

    def usersNeeded(self, num, log_them_in=True):
        '''Call this at the beginning of your test method to specify however many
        logged in and ready users you want to use in your test.'''
        self.users = []
        self.trs = []
        for n in range(0, num):
            new_user = self.connectUser()
            if log_them_in:
                self.logInUser(new_user, n)

    def connectUser(self):
        new_user = self.factory.buildProtocol(('127.0.0.1', 6667))
        new_tr = proto_helpers.StringTransport()
        self.trs.append(new_tr)
        self.users.append(new_user)
        new_user.makeConnection(new_tr)
        return new_user

    def logInUser(self, u, n):
        self.setNick(u, user_fixtures[n][0])
        self.setUser(u, user_fixtures[n][1], "%sscomputer.pppoe.lolisp.eu" % user_fixtures[n][1], "localhost.", user_fixtures[n][2])

    def getOutputtedLines(self, num):
        return self.trs[num].value().split("\r\n")

    def getLastOutputtedLine(self, num):
        # not sure why, but I always get a blank line at the end of the value
        # from the string transport.
        return self.getOutputtedLines(num)[-2]

#     def connectAnIRCClient(self):
#         new_user = self.factory.buildProtocol(('127.0.0.1', 6667))
#         self.users.append(new_user)
#         new_tr = proto_helpers.StringTransport()
#         self.trs.append(new_tr)
#         new_user.makeConnection(new_tr)

    def setUp(self):
        self.factory = ikarus.irc.IRCFactory()
        #for num in range(0, 3):
        #    self.connectAnIRCClient()

    def testInstantiate(self):
        self.usersNeeded(1, log_them_in=False)
        self.failIfEqual(self.users[0], None)

    def setNick(self, u, nickname):
        u.lineReceived("NICK %s" % nickname)

    def setUser(self, u, username, hostname, servername, realname):
        u.lineReceived("USER %s %s %s :%s" % (username, hostname,
                                              servername, realname))

    def testSetNick(self):
        self.usersNeeded(1, log_them_in=False)
        self.setNick(self.users[0], "" + user_fixtures[0][0] + "")
        self.failUnlessEqual(self.users[0].nick, "" + user_fixtures[0][0] + "")
        self.setNick(self.users[0], "smartyman")
        self.failUnlessEqual(self.users[0].nick, "smartyman")

    def testMalformedSetNick(self):
        self.usersNeeded(1, log_them_in=False)
        self.users[0].lineReceived("NICK")
        input = self.getLastOutputtedLine(0)
        self.failUnlessEqual(input, ":localhost. 431  :No nickname given")

    def testSetUser(self):
        #self.users[0].lineReceived("USER " + user_fixtures[0][0] + " " + user_fixtures[0][0] + "shostname localhost :Andrew Clunis")
        self.usersNeeded(1, log_them_in=False)
        self.setUser(self.users[0], "" + user_fixtures[0][0] + "", "" + user_fixtures[0][0] + "shostname", "localhost", "Andrew Clunis")
        self.failUnlessEqual(self.users[0].name, "" + user_fixtures[0][0] + "")

    def testConnectionOpened(self):
        self.usersNeeded(1, log_them_in=False)
        self.users[0].lineReceived("NOTICE AUTH :*** Looking up your hostname...")
        self.users[0].lineReceived("NOTICE AUTH :*** Found your hostname")

    def testLogIn(self):
        self.usersNeeded(1)
        #self.setNick(self.users[0], "" + user_fixtures[0][0] + "")
        #self.setUser(self.users[0], "" + user_fixtures[0][0] + "", "blahblah-pppoe.myisp.ca", "ircserver.awesome.org", "Andrew Clunis")
        input = self.getOutputtedLines(0)
        self.failUnlessEqual(input[2], ":localhost. 001 " + user_fixtures[0][0] + " :Welcome to $hostname.")
        self.failUnlessEqual(input[3], ":localhost. 002 " + user_fixtures[0][0] + " :Your host is $hostname running version Ikarus")
        self.failUnlessEqual(input[4], "NOTICE " + user_fixtures[0][0] + " :*** Your host is $hostname running version Ikarus")
        self.failUnlessEqual(self.users[0].logged_in, True)

    def testConnectionNotOpenedWithOnlyNick(self):
        self.usersNeeded(1, log_them_in=False)
        self.setNick(self.users[0], "" + user_fixtures[0][0] + "")
        self.failIfEqual(self.users[0].logged_in, True)

    def testConnectionNotOpenedWithOnlyUser(self):
        self.usersNeeded(1, log_them_in=False)
        self.setUser(self.users[0], user_fixtures[0][0], user_fixtures[0][0] + ".myhost.ca",
                     "localhost", "Andrew Clunis")
        self.failIfEqual(self.users[0].logged_in, True)

    def testMalformedSetUser(self):
        self.usersNeeded(1, log_them_in=False)
        self.users[0].lineReceived("USER")
        self.failUnlessEqual(self.getLastOutputtedLine(0), ":localhost. 461 * USER :Not enough parameters.")

    def testMalformedSetUserAlmostLongEnough(self):
        self.usersNeeded(1, log_them_in=False)
        self.users[0].lineReceived("USER whee whee whee")
        self.failUnlessEqual(self.getLastOutputtedLine(0), ":localhost. 461 * USER :Not enough parameters.")

    def testJoinANewChannel(self):
        self.testLogIn()
        self.users[0].lineReceived("JOIN #my_channel")
        # I should test the presence of channel logged in info here, once it exists
        # expect callback here.
        self.failUnlessEqual(self.getOutputtedLines(0)[-3],
                             ":" + user_fixtures[0][0] + "!~" + user_fixtures[0][1] + "@localhost. JOIN :#my_channel")
        self.failUnlessEqual(self.getOutputtedLines(0)[-2],
                             ":localhost. 353 " + user_fixtures[0][0] + " = #my_channel :" + user_fixtures[0][0] + "")

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
        self.usersNeeded(1, log_them_in=False)
        self.users[0].lineReceived("JOIN #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 451 JOIN :You have not registered.")

    def testNickInUseAlreadyLoggedIn(self):
        #self.testLogIn()
        self.usersNeeded(1)
        self.connectUser() # will return a user with index 1
        self.setNick(self.users[1], "" + user_fixtures[0][0] + "")
        self.failUnlessEqual(self.getLastOutputtedLine(1),
                             ":localhost. 433 * " + user_fixtures[0][0] + " :Nickname is already in use.")

    def testPart(self):
        # make sure that the user is removed from the channel and does not receive
        # new messages.
        self.testTwoJoinAChannel()
        self.users[0].lineReceived("PART #mychannel :Bye bye.")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":" + user_fixtures[0][0] + "!~" + user_fixtures[0][1] + "@localhost. PART #mychannel :Bye bye.")
        self.failUnlessEqual(self.getLastOutputtedLine(1),
                             ":" + user_fixtures[0][0] + "!~" + user_fixtures[0][1] + "@localhost. PART #mychannel :Bye bye.")
        self.users[0].lineReceived("PRIVMSG #mychannel :Lorem Ipsum...")
        self.failIfEqual(self.getLastOutputtedLine(1),
                         ":" + user_fixtures[0][0] + "!~" + user_fixtures[0][1] + "@localhost. PRIVMSG #mychannel :Lorem Ipsum...")

    def testMalformedPart(self):
        self.testTwoJoinAChannel()
        self.users[0].lineReceived("PART")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 461 " + user_fixtures[0][0] + " PART :Not enough parameters.")

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
                             ":" + user_fixtures[0][0] + "!~" + user_fixtures[0][1] + "@localhost. PART #mychannel :I'm outta here!")
        self.failUnlessEqual(lines[-2],
                             ":" + user_fixtures[0][0] + "!~" + user_fixtures[0][1] + "@localhost. PART #another_channel :I'm outta here!")

#     actually, I'm not going to bother with this.  The RFC says the colon
#     must always be there, so why bother making it flexible just because dancer is?
#     def testPartMalformedMessageMissingColon(self):
#         self.testLogIn()
#         self.users[0].lineReceived("JOIN #mychannel")
#         self.users[0].lineReceived("PART #mychannel no colon, but it should still work!")
#         self.failUnlessEqual(self.getLastOutputtedLine(0),
#                              ":" + user_fixtures[0][0] + "!~" + user_fixtures[0][0] + "@localhost. PART #mychannel :no colon, but it should still work!")

    def testPartFromNonExistentChannel(self):
        # this should be tested in this testcase.
        self.testLogIn()
        self.users[0].lineReceived("PART #doesnotexist")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 403 " + user_fixtures[0][0] + " #doesnotexist :That channel doesn't exist.")

    def testQuit(self):
        # make sure user is parted from all channels, as above, and can reconnect
        # without getting incorrect "nickname in use messages"
        self.testTwoJoinAChannel()
        self.failIfEqual(None,
                         self.factory.getUserByNick("" + user_fixtures[1][0] + ""))
        self.users[1].lineReceived("QUIT :bye bye!")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":" + user_fixtures[1][0] + "!~" + user_fixtures[1][1] + "@localhost. QUIT :bye bye!")
        self.failUnlessEqual(self.getLastOutputtedLine(1),
                             "ERROR :Closing Link: " + user_fixtures[1][0] + " (Client Quit)")

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
        self.usersNeeded(3)
        logging.debug(self.factory.users)
        self.users[1].lineReceived("QUIT :toodles!")
        logging.debug(self.factory.users)
        self.setNick(self.users[2], "" + user_fixtures[1][0] + "") # user user #1's nick
        self.failIfEqual(self.getLastOutputtedLine(2),
                         ":localhost. 433 * " + user_fixtures[1][0] + " :Nickname is already in use.")

    def testQuitDoesNotSendMultipleQuitMessagesToEachUser(self):
        # right now there is a silly bug, where, because transmitting the QUIT message
        # is delegated to all the channels that the user is joined to,
        # any user that is in more than one channel with the quitting user
        # will get multiple quits. oops!
#        self.testLogIn()
#        self.setNick(self.users[1], "secondguy")
#        self.setUser(self.users[1], "sguy", "secondguy.myisp.ca", "localhost", "Someone.")

        self.usersNeeded(2)
        self.users[0].lineReceived("JOIN #somewhere")
        self.users[1].lineReceived("JOIN #somewhere")
        self.users[0].lineReceived("JOIN #somewhere_else")
        self.users[1].lineReceived("JOIN #somewhere_else")
        self.users[1].lineReceived("QUIT :hasta la vista!")
        self.users[1].connectionLost("socket lolbai!")

        lines = self.getOutputtedLines(0)

        # check to see if the first user got an extra QUIT line back.
        first_returned_statement = lines[-3].split(" ")[1]
        second_returned_statement = lines[-2].split(" ")[1]
        logging.debug(first_returned_statement)
        self.failIfEqual(first_returned_statement, "QUIT")
        # make sure the single message does arrive.
        self.failUnlessEqual(second_returned_statement, "QUIT")


    def testUserClosesConnectionBeforeLogIn(self):
        # I think this screws up right now.
        pass

    def testConnectionLost(self):
        self.testTwoJoinAChannel()

        from twisted.internet.main import CONNECTION_LOST
        self.users[1].connectionLost(twisted.python.failure.Failure(CONNECTION_LOST))

        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":" + user_fixtures[1][0] + "!~" + user_fixtures[1][1] + "@localhost. QUIT :Connection to the other side was lost in a non-clean fashion: Connection lost.")

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
        self.usersNeeded(2)
#        self.testLogIn()
        #self.setNick(self.users[1], "my_second_guy")
        #self.setUser(self.users[1], "msg", "msghost.cx", "localhost", "Another Dude")
        self.failIfEqual(None,
                         self.factory.getUserByNick(user_fixtures[1][0]))
        self.users[0].lineReceived("JOIN #mychannel")
        self.users[1].lineReceived("JOIN #mychannel")
        self.failUnlessEqual(self.getLastOutputtedLine(0), ":" + user_fixtures[1][0] + "!~" + user_fixtures[1][1] + "@localhost. JOIN :#mychannel")

    def testUserThatHasOnlyDoneNickAndNotUserCanBePunted(self):
        # test that a second session that calls NICK for the
        # same name can punt off another session that has already
        # called nick, but has not yet called USER.
        pass

    def testSendLineShouldFailSilentlyAfterConnectionLost(self):
        # actually, this doesn't actually test what we think.
        # because the underlying transport during testing
        # is the StringTransport, the error throwing is never done.
        self.usersNeeded(1)
        self.users[0].connectionLost(twisted.python.failure.Failure(error.ConnectionDone("obooo")))
        self.users[0].sendLine("lol, internet")

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
        self.failUnlessEqual(input2[-2], ":" + user_fixtures[0][0] + "!~" + user_fixtures[0][1] + "@localhost. PRIVMSG #mychannel :Lorem Ipsum sit Dolor.")

    def testChannelPartUnjoinedUser(self):
        self.usersNeeded(2)
        self.users[1].lineReceived("JOIN #channel")
        self.users[0].lineReceived("PART #channel")
        self.failUnlessEqual(self.getLastOutputtedLine(0),
                             ":localhost. 422 " + user_fixtures[0][0] + " #channel :You're not on that channel.")

    def testWhoReturnsUserList(self):
        self.testTwoJoinAChannel()
        self.users[0].lineReceived("WHO #mychannel")
        logging.debug(self.getOutputtedLines(0))
        self.failUnlessEqual(self.getOutputtedLines(0)[-4],
                             ":localhost. 352 " + user_fixtures[0][0] + " #mychannel " + user_fixtures[0][1] + " localhost. irc.localnet " + user_fixtures[0][0] + " H :0 Andrew Clunis")
        self.failUnlessEqual(self.getOutputtedLines(0)[-3],
                             ":localhost. 352 " + user_fixtures[0][0] + " #mychannel " + user_fixtures[1][1] + " localhost. irc.localnet " + user_fixtures[1][0] + " H :0 Andrew Clunis")
        self.failUnlessEqual(self.getOutputtedLines(0)[-2],
                             ":localhost. 315 " + user_fixtures[0][0] + " #mychannel :End of /WHO list.")

