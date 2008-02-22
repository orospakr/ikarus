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
        self.joined_channels = []

    def lineReceived(self, line):
        items = line.split(" ")
        if items[0] == "NICK":
            if len(items) == 1:
                self.sendLine(":localhost. 431  :No nickname given")
                return
            new_nick = items[1]
            existing_user = self.factory.getUserByNick(new_nick)
            if existing_user is not None:
                self.sendLine(':localhost. 433 * %s :Nickname is already in use.' % new_nick)
                return
            self.nick = new_nick
            if self.name is not None:
                self.doLogin()
        elif items[0] == "USER":
            if len(items) < 5:
                logging.warning("Malformed USER from %s" % self.nick)
                self.sendLine(":localhost. 461 * USER :Not enough parameters.")
                return
            self.name = items[1]
            if self.nick is not None:
                self.doLogin()
        elif items[0] == "PRIVMSG":
            if len(items) < 3:
                # wrong number of args, should be error?
                logging.warning("Malformed PRIVMSG from %s" % self.nick)
                self.sendLine(":localhost. 461 * PRIVMSG :Not enough parameters.")
                return
            channel_name = items[1][1:]
            message_start = len("PRIVMSG ") + len(channel_name) + 3
            message = line[message_start:]
            channel = self.factory.getChannelByName(channel_name)
            channel.privMsg(self, message)

        elif items[0] == "JOIN":
            if not self.logged_in:
                self.sendLine(":localhost. 451 JOIN :You have not registered.")
                return
            if len(items) < 2:
                self.sendLine(":localhost. 461 * JOIN :Not enough parameters.")
                return
            channel_name = items[1][1:]
            channel = self.factory.getChannelByName(channel_name)
            if channel is None:
#                logging.debug("Channel %s does not exist, so creating a new one, for %s!" % (channel_name, self.nick))
                channel = ikarus.channel.Channel(self.factory, channel_name)
            channel.joinUser(self)

        elif items[0] == "PART":
            if len(items) < 2:
                self.sendLine(":localhost. 461 %s PART :Not enough parameters." % self.nick)
                return
            channel_args = items[1]
            channel_names = channel_args.split(",")
            message_start = len("PART ") + len(channel_args) + 2 # HACK why is this 2, rather than the 3 used in the PRIVMSG block?!??!
            message = line[message_start:]
            for channel_name in channel_names:
                channel = self.factory.getChannelByName(channel_name[1:])
                if channel is None:
                    self.sendLine(":localhost. 403 orospakr #doesnotexist :That channel doesn't exist.")
                else:
                    channel.partUser(self, message)

        elif items[0] == "QUIT":
            message_start = len("QUIT ") + 1 # +1 to skip the colon
            message = line[message_start:]
            self.sendLine("ERROR :Closing Link: my_second_guy (Client Quit)")
            all_users_who_care = set([])
            for chan in self.joined_channels:
                all_users_who_care = all_users_who_care.union(
                    chan.users)
            all_users_who_care.remove(self)
            for u in all_users_who_care:
                u.sendLine(':%s!~%s@localhost. QUIT :%s' % (self.nick, self.name, message))

    def connectionMade(self):
        self.factory.registerUser(self)
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

    def registerUser(self, user):
        self.users.append(user)

    def registerChannel(self, channel):
        self.channels.append(channel)

    def getUserByNick(self, nick):
        for u in self.users:
            if u.nick == nick:
                return u
            else:
                return None

    def getChannelByName(self, name):
        for c in self.channels:
            if c.name == name:
                return c
        return None
