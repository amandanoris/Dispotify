import struct
import hashlib
from collections import namedtuple
import logging
from random import getrandbits  

log = logging.getLogger(__name__)  
class KademliaNode:
    
    def __init__(self, identifier, address=None, port=None):
       
        if isinstance(identifier, bytes):
            self.id = hashlib.sha1(identifier).hexdigest()
        elif isinstance(identifier, int):
            self.id = hashlib.sha1(str(identifier).encode()).hexdigest()
        elif isinstance(identifier, str):
            self.id = hashlib.sha1(identifier.encode()).hexdigest()
        else:
            raise ValueError("Identifier must be bytes, int, or str")
        
        print(f"ID generated: {self.id}, Length: {len(self.id)}")
        
        if len(self.id) != 40:
            raise ValueError(f"Invalid ID length: {len(self.id)}. Expected 40 characters.")

        if address and port:
            self.address = (address, port)
        else:
            self.address = None

    def distance_to(self, other):
        return int(self.id, 16) ^ int(other.id, 16)

    @staticmethod
    def generate_id():
    
        return hashlib.sha1(struct.pack('!Q', getrandbits(64))).hexdigest()

    def __repr__(self):
        return f'<KademliaNode id={self.id} address={self.address}>'

class NodeHeap:
    def __init__(self):
        self.nodes = []

    def add(self, node):
        self.nodes.append(node)

    def get_closest(self, ksize):
  
        self.nodes.sort(key=lambda node: node.id)
        return self.nodes[:ksize]
