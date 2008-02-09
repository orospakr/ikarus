#!/usr/bin/env python

import logging
from twisted.internet import reactor

import ikarus.irc

def run():
    logging.basicConfig(level=logging.DEBUG)
    reactor.listenTCP(6667, ikarus.irc.IRCFactory())
    logging.info("Ikarus started.  Listening...")
    reactor.run()

if __name__ == '__main__':
    run()
