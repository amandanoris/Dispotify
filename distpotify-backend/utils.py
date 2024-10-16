import hashlib
import operator
import asyncio
import socket
from logging import log
import netifaces

def list_broadcast_addresses():

    broadcast_addresses = []

    interfaces = netifaces.interfaces()

    for interface in interfaces:
        
        addresses = netifaces.ifaddresses(interface)
        #print(f"{addresses}{interface}")
        if netifaces.AF_INET in addresses:
            ipv4_info = addresses[netifaces.AF_INET][0]
            
            broadcast = ipv4_info.get('broadcast')
            if broadcast:
                broadcast_addresses.append(broadcast)

    return broadcast_addresses

def check_dht_value_type(value):
    typeset = [
        int,
        float,
        bool,
        str,
        bytes
    ]
    return type(value) in typeset  

def get_local_ip():

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        return ip
    except Exception as e:
        log.error(f"Error al obtener la IP local: {e}")
        return "127.0.0.1"  


async def gather_dict(dic):
    cors = list(dic.values())
    results = await asyncio.gather(*cors)
    return dict(zip(dic.keys(), results))


def digest(string):
    if not isinstance(string, bytes):
        string = str(string).encode('utf8')
    return hashlib.sha1(string).digest()


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
