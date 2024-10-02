import hashlib
import asyncio
import hashlib
import random
import operator
def digest(value):
    """
    Return the SHA1 digest of the given value.
    """
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha1(value).digest()



def generate_node_id():
    
    random_number = random.randint(0, 1000000)
    random_string = str(random_number)
    node_id = hashlib.sha256(random_string.encode()).digest()
    
    return node_id

async def gather_dict(dic):

    cors = list(dic.values())
    results = await asyncio.gather(*cors)

    return dict(zip(dic.keys(), results))

def digest(string):

    if not isinstance(string, bytes):
        string = str(string).encode('utf8')

    return hashlib.sha1(string).digest()[:8]  # Solo los primeros 8 bytes


def shared_prefix(args):

    i = 0
    while i < min(map(len, args)):
        if len(set(map(operator.itemgetter(i), args))) != 1:
            break
        i += 1

    return args[0][:i]

def bytes_to_bit_string(bites):

    bits = [bin(bite)[2:].rjust(8, '0') for bite in bites]
    
    return "".join(bits)

import random
import socket

def get_random_port(start=1024, end=65535):

    while True:
        try:
           
            port = random.randint(start, end)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
      
            return port
        except OSError:
         
            continue
