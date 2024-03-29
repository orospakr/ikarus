import twisted.protocols.basic
import twisted.internet.protocol
from twisted.internet import error
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
        self.has_quit = False

    def lineReceived(self, line):
#        logging.debug("line recv'd '%s'" % line)
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
                    self.sendLine(":localhost. 403 %s #doesnotexist :That channel doesn't exist." % self.nick)
                else:
                    channel.partUser(self, message)

        elif items[0] == "QUIT":
            message_start = len("QUIT ") + 1 # +1 to skip the colon
            message = line[message_start:]
            self.doQuit(message, False)

        elif items[0] == "WHO":
            channel_name_start = len("WHO ") # no +1 because there's no colon
            channel_name = line[channel_name_start:]
            chan = self.factory.getChannelByName(channel_name[1:])
            chan.whoQuery(self)

        else:
            bogus_command = items[0]
            self.sendLine(":localhost. 421 %s %s :Unknown command" % (self.nick, bogus_command))

    def doQuit(self, message, no_connection):
        if not no_connection:
            self.sendLine("ERROR :Closing Link: %s (Client Quit)" % self.nick)
        logging.debug("User %s is quitting, reason: %s" % (self.nick, message))
        all_users_who_care = set([])
        for chan in self.joined_channels:
            all_users_who_care = all_users_who_care.union(
               chan.users)
        if not len(self.joined_channels) < 1:
            all_users_who_care.remove(self)
        for u in all_users_who_care:
            u.sendLine(':%s!~%s@localhost. QUIT :%s' % (self.nick, self.name, message))
        for chan in self.joined_channels:
            chan.users.remove(self)
        self.factory.unregisterUser(self)
        self.has_quit = True

    def connectionMade(self):
        self.factory.registerUser(self)
        self.sendLine("NOTICE AUTH :*** Looking up your hostname...")
        # discover hostname?
        self.sendLine("NOTICE AUTH :*** Found your hostname")

    def doLogin(self):
        '''COME BACK HERE'''
        self.logged_in = True
        self.sendLine(":localhost. 001 %s :Welcome to localhost." % self.nick)
        self.sendLine(":localhost. 002 %s :Your host is localhost. running Ikarus 0.1." % self.nick)
        self.sendLine(":localhost. 003 %s :This server was created Mon Sep 25 2006 at 21:10:26 EDT" % self.nick)
        self.sendLine(":localhost. 004 %s localhost. Ikarus r s" % self.nick)
        self.sendLine(":localhost. 005 %s MODES=4 CHANLIMIT=#:20 NICKLEN=16 USERLEN=10 HOSTLEN=63 TOPICLEN=450 KICKLEN=450 CHANNELLEN=30 KEYLEN=23 CHANTYPES=# PREFIX=(ov)@+ CASEMAPPING=ascii CAPAB IRCD=ikarus :are available on this server" % self.nick)
        self.sendLine(":localhost. 422 %s :MOTD file is missing." % self.nick)
        self.sendLine("NOTICE %s :*** Your host is $hostname running version Ikarus" % self.nick)

    def connectionLost(self, reason):
        if not self.has_quit:
            # TODO I should interpret the error states in
            # reason as twisted.python.error, and give
            # more traditional IRC connection error
            # messages.
            logging.debug("connection was lost, without already quitting..")
            self.doQuit(reason.getErrorMessage(), True)
        else:
            logging.debug("connection was lost, with already having quit.")

    def __repr__(self):
        return "IRC object with nickname '%s'" % self.nick

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
        return None

    def getChannelByName(self, name):
        for c in self.channels:
            if c.name == name:
                return c
        return None

    def unregisterUser(self, user):
        logging.debug("Unregistering user with nick '%s'." % user.nick)
        self.users.remove(user)
