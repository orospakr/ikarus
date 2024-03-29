class Channel(object):
    def __init__(self, ircfactory, name):
        self.ircfactory = ircfactory
        self.users = []
        self.name = name
        self.ircfactory.registerChannel(self)

    def joinUser(self, user):
        self.users.append(user)
        user.joined_channels.append(self)
        nick_list = ""
        for u in self.users:
            u.sendLine(":%s!~%s@localhost. JOIN :#%s" % (user.nick, user.name, self.name))
            nick_list += u.nick + ' '
        nick_list = nick_list.strip()
        user.sendLine(":localhost. 353 %s = #%s :%s" %(user.nick, self.name, nick_list))

    def findUser(self, nick):
        for user in self.users:
            if user.nick == nick:
                return user
            else:
                return None

    def privMsg(self, speaker, msg):
        for user in self.users:
            if user is speaker:
                continue
            if speaker in self.users:
                user.sendLine(':%s!~%s@localhost. PRIVMSG #%s :%s' % (speaker.nick, speaker.name, self.name, msg))

    def partUser(self, leaver, msg):
        if leaver not in self.users:
            leaver.sendLine(":localhost. 422 %s #%s :You're not on that channel." % (
                    leaver.nick, self.name))
            return
        for user in self.users:
            user.sendLine(':%s!~%s@localhost. PART #%s :%s' % (leaver.nick, leaver.name, self.name, msg))
        self.users.remove(leaver)

    def whoQuery(self, user):
        for u in self.users:
            user.sendLine(":localhost. 352 %s #%s %s localhost. irc.localnet %s H :0 Andrew Clunis" % (user.nick, self.name, u.name,u.nick))
        user.sendLine(":localhost. 315 %s #%s :End of /WHO list." % (user.nick, self.name))

