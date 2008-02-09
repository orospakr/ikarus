import twisted.protocols.basic
import twisted.internet.protocol

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
            self.nick = items[1]
            if self.user_name is not None:
                self.logged_in = True
        elif items[0] == "USER":
            self.user_name = items[1]
            if self.nick is not None:
                self.logged_in = True

    def connectionMade(self):
        self.sendLine("wefasdfsaf")
        self.factory.register_user(self)

class IRCFactory(twisted.internet.protocol.Factory):
    protocol = IRC
    users = []

    def register_user(self, user):
        self.users.append(user)
