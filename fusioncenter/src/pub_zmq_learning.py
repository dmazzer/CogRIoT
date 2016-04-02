#!/usr/bin/env python
"""Simple example of publish/subscribe illustrating topics.

Publisher and subscriber can be started in any order, though if publisher
starts first, any messages sent before subscriber starts are lost.  More than
one subscriber can listen, and they can listen to  different topics.

Topic filtering is done simply on the start of the string, e.g. listening to
's' will catch 'sports...' and 'stocks'  while listening to 'w' is enough to
catch 'weather'.
"""

#-----------------------------------------------------------------------------
#  Copyright (c) 2010 Brian Granger, Fernando Perez
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys
import time

import zmq
import numpy
import time
from random import choice
from random import randrange

def main():
    stock_symbols = ['RAX', 'EMC', 'GOOG', 'AAPL', 'RHAT', 'AMZN']

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://0.0.0.0:5555")
    
    while True:
            time.sleep(3)
            # pick a random stock symbol
            stock_symbol = choice(stock_symbols)
            # set a random stock price
            stock_price = randrange(1, 100)
     
            # compose the message
            msg = "{0} ${1}".format(stock_symbol, stock_price)
     
            print("Sending Message: {0}".format(msg))
     
            # send the message
            socket.send(msg)
            # Python3 Note: Use the below line and comment
            # the above line out
            # socket.send_string(msg)

if __name__ == "__main__":
    main()
