class Channel(object):
    def __init__(self, ircfactory, name):
        self.ircfactory = ircfactory
#        self.ircfactory.register_channel(self)
        self.users = []

    def joinUser(self, user):
        for u in self.users:
            u.sendLine(":%s!~%s@localhost. JOIN :#mychannel" % (user.nick, user.name))
        self.users.append(user)

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
            user.sendLine(':%s!~%s@localhost. PRIVMSG #mychannel :%s' % (speaker.nick, speaker.name, msg))
