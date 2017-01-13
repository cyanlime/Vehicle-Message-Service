from pypack import PyPack

def callback(scope, payload):
    print payload

def TCPHandler(socket, address):
    PyPack.hold('vehicle', socket.makefile(), callback)