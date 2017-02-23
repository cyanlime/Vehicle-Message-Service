from pypack import PyPack

def callback(scope, payload):
    print payload

def secure_method(first_msg):
    return first_msg.payload

def TCPHandler(socket, address):
    PyPack.hold(secure_method, socket.makefile(), callback)