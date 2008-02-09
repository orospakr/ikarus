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
        pass

    def connectionMade(self):
        pass

class IRCFactory(twisted.internet.protocol.Factory):
    protocol = IRC
