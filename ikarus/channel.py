class Channel(object):
    def __init__(self, ircfactory, name):
        self.ircfactory = ircfactory
        self.ircfactory.registerChannel(self)
        self.users = []
        self.name = name

    def joinUser(self, user):
        self.users.append(user)
        for u in self.users:
            u.sendLine(":%s!~%s@localhost. JOIN :#%s" % (user.nick, user.name, self.name))

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
