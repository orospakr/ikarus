import twisted.protocols.basic
import twisted.internet.protocol
import logging

import ikarus.channel

class IRC(twisted.protocols.basic.LineReceiver):

    def __init__(self):
        #twisted.protocols.basic.LineOnlyReceiver.__init__(self)
        #self.logged_in = True
        self.logged_in = False
        self.nick = None
        self.name = None

    def lineReceived(self, line):
        items = line.split(" ")
        if items[0] == "NICK":
            if len(items) == 1:
                self.sendLine(":localhost. 431  :No nickname given")
                return
            self.nick = items[1]
            if self.name is not None:
                self.doLogin()
        elif items[0] == "USER":
            if len(items) < 5:
                logging.warning("Malformed USER from %s" % self.nick)
                self.sendLine(":localhost. 461 * USER :Not enough parameters")
                return
            self.name = items[1]
            if self.nick is not None:
                self.doLogin()
        elif items[0] == "PRIVMSG":
            if len(items) < 3:
                # wrong number of args, should be error?
                logging.warning("Malformed PRIVMSG from %s" % self.nick)
                self.sendLine(":localhost. 461 * PRIVMSG :Not enough parameters")
                return
            channel_name = items[1][1:]
            message_start = len("PRIVMSG ") + len(channel_name) + 3
            message = line[message_start:]
            channel = self.factory.getChannelByName(channel_name)
            channel.privMsg(self, message)

        elif items[0] == "JOIN":
            if not self.logged_in:
                self.sendLine(":localhost. 451 JOIN :You have not registered")
                return
            if len(items) < 2:
                self.sendLine(":localhost. 461 * JOIN :Not enough parameters")
                return
            channel_name = items[1][1:]
            channel = self.factory.getChannelByName(channel_name)
            if channel is None:
#                logging.debug("Channel %s does not exist, so creating a new one, for %s!" % (channel_name, self.nick))
                channel = ikarus.channel.Channel(self.factory, channel_name)
                self.factory.channels.append(channel)
            channel.joinUser(self)

    def connectionMade(self):
        self.factory.register_user(self)
        self.sendLine("NOTICE AUTH :*** Looking up your hostname...")
        # discover hostname?
        self.sendLine("NOTICE AUTH :*** Found your hostname")

    def doLogin(self):
        '''COME BACK HERE'''
        self.logged_in = True
        self.sendLine(":localhost. 001 %s :Welcome to $hostname." % self.nick)
        self.sendLine(":localhost. 002 %s :Your host is $hostname running version Ikarus" % self.nick)
        self.sendLine("NOTICE orospakr :*** Your host is $hostname running version Ikarus")

class IRCFactory(twisted.internet.protocol.Factory):
    protocol = IRC

    def __init__(self):
        self.users = []
        self.channels = []

    def register_user(self, user):
        self.users.append(user)

    def registerChannel(self, channel):
        self.channels.append(channel)

    def getChannelByName(self, name):
        for c in self.channels:
            if c.name == name:
                return c
            else:
                return None
