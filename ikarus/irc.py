import twisted.protocols.basic
import twisted.internet.protocol
import logging

class IRC(twisted.protocols.basic.LineReceiver):

    def __init__(self):
        #twisted.protocols.basic.LineOnlyReceiver.__init__(self)
        #self.logged_in = True
        self.logged_in = False
        self.nick = None
        self.user_name = None
        pass

    def lineReceived(self, line):
        items = line.split(" ")
        if items[0] == "NICK":
            if len(items) == 1:
                self.sendLine(":localhost. 431  :No nickname given")
                return
            self.nick = items[1]
            if self.user_name is not None:
                self.doLogin()
        elif items[0] == "USER":
            if len(items) < 5:
                self.sendLine(":localhost. 461 * USER :Not enough parameters")
                return
            self.user_name = items[1]
            if self.nick is not None:
                self.doLogin()
        elif items[0] == "PRIVMSG":
            if len(items) < 4:
                # wrong number of args, should be error?
                return

    def connectionMade(self):
        self.factory.register_user(self)
        self.sendLine("NOTICE AUTH :*** Looking up your hostname...")
        # hostname?
        self.sendLine("NOTICE AUTH :*** Found your hostname")

    def doLogin(self):
        '''COME BACK HERE'''
        self.logged_in = True
        self.sendLine(":localhost. 001 %s :Welcome to $hostname." % self.nick)
        self.sendLine(":localhost. 002 %s :Your host is $hostname running version Ikarus" % self.nick)
        self.sendLine("NOTICE orospakr :*** Your host is $hostname running version Ikarus")

class IRCFactory(twisted.internet.protocol.Factory):
    protocol = IRC
    users = []
    channels = []

    def register_user(self, user):
        self.users.append(user)

    def register_channel(self, channel):
        self.channels.append(channel)

    def getChannelByName(self, name):
        for channel in self.channels:
            if channel.name == name:
                return channel
            else:
                return None
