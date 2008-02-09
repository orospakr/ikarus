import twisted.protocols.basic
import twisted.internet.protocol

class IRC(twisted.protocols.basic.LineReceiver):

    def __init__(self):
        #twisted.protocols.basic.LineOnlyReceiver.__init__(self)
        pass


    def lineReceived(self, line):
        self.nick = line.split(" ")[1]

    def connectionMade(self):
        self.sendLine("wefasdfsaf")
        self.factory.register_user(self)

class IRCFactory(twisted.internet.protocol.Factory):
    protocol = IRC
    users = []

    def register_user(self, user):
        self.users.append(user)
