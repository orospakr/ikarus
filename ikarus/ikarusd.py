#!/usr/bin/env python

import logging
from twisted.internet import reactor
from optparse import OptionParser
import sys

import ikarus.irc

def run():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option("-p", "--port", type="int", dest="port",
                      help="TCP port to listen on.  May only be specified once. (default: %default)",
                      default=6667)
    (options, args) = parser.parse_args()
    reactor.listenTCP(options.port, ikarus.irc.IRCFactory())
    logging.info("Ikarus started.  Listening on port %i..." % options.port)
    reactor.run()

if __name__ == '__main__':
    run()
