import twisted.protocols.basic
import twisted.internet.protocol

class IRC(twisted.protocols.basic.LineReceiver):

    def __init__(self):
        #twisted.protocols.basic.LineOnlyReceiver.__init__(self)
        #self.nick = "orospakr"
        pass

    def lineReceived(self, line):
        #self.nick = line.split()[1]
        #self.se(line)
        self.sendLine(line)
        for user in self.factory.users:
            user.sendLine(line)

    def connectionMade(self):
        self.factory.register_user(self)

class IRCFactory(twisted.internet.protocol.Factory):
    protocol = IRC
    users = []

    def register_user(self, user):
        self.users.append(user)
