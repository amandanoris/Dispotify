
import random
import asyncio
import logging

from rpcudp.protocol import RPCProtocol

from kademlia_node import KademliaNode
from kbuckets import RoutingTable
from utils import digest

log = logging.getLogger(__name__)  

class KademliaProtocol(RPCProtocol):
    def __init__(self, source_node, storage, ksize):
        RPCProtocol.__init__(self)
        self.router = RoutingTable(self, ksize, source_node)
        self.storage = storage
        self.source_node = source_node

    def get_refresh_ids(self):
        ids = []
        for bucket in self.router.lonely_buckets():
            rid = random.randint(*bucket.range).to_bytes(20, byteorder='big')
            ids.append(rid)
        return ids

    def rpc_stun(self, sender):  
        return sender

    def rpc_store(self, sender, nodeid, key, value):
        source = KademliaNode(nodeid, sender[0], sender[1])
        self.welcome_if_new(source)
        log.debug("got a store request from %s, storing '%s'='%s'",
                  sender, key.hex(), value)
        self.storage[key] = value
        return True

    def rpc_ping(self, sender, nodeid, *args):
        source = KademliaNode(nodeid, sender[0], sender[1])
        self.welcome_if_new(source)
        return ([nodeid, [sender[0], sender[1]]])



    def rpc_find_node(self, sender, nodeid, key):
        """
        Responde a una solicitud de búsqueda de nodo, devolviendo vecinos cercanos al nodo objetivo.
        """
        source = KademliaNode(nodeid, sender[0], sender[1])
        self.welcome_if_new(source)
        
        node = KademliaNode(key)
        neighbors = self.router.find_neighbors(node, exclude=source)
        
        print(f"Encontrando nodos cercanos a {key} desde {sender}")
        return list(map(tuple, neighbors))



    def rpc_find_value(self, sender, nodeid, key):
        source = KademliaNode(nodeid, sender[0], sender[1])
        self.welcome_if_new(source)
        value = self.storage.get(key, None)
        if value is None:
            return self.rpc_find_node(sender, nodeid, key)
        return True, value, sender  
    
    async def call_find_node(self, node_to_ask, node_to_find):
        address = node_to_ask.address
        result = await self.find_node(address, self.source_node.id, node_to_find.id)
        log.debug(f"call_find_node result: {result}")

        return self.handle_call_response(result, node_to_ask)

    async def call_find_value(self, node_to_ask, node_to_find):
        address = node_to_ask.address
        result = await self.find_value(address, self.source_node.id, node_to_find.id)
        log.debug(f"call_find_value result: {result}")

        return self.handle_call_response(result, node_to_ask)

    async def call_ping(self, node_to_ask):
        try:
            address = node_to_ask.address
            result = await self.ping(address, self.source_node.id, address)

            print(f"Ping result from {address}: {result}")

            if result and isinstance(result, tuple) and len(result) == 2:
                print(f"Result from ping: {result}")
               
                success, (node_id, (ip, port)) = result

                print(f"Descomponiendo resultado: Node ID: {node_id}, IP: {ip}, Port: {port}")
                
                aux = KademliaNode(node_id, ip, port)
                aux.id =node_id
                
                self.welcome_if_new(aux)  
                
                return True  

        except Exception as e:
            log.error(f"Error during ping to {address}: {e}")
            return None 


    async def call_store(self, node_to_ask, key, value):
        address = node_to_ask.address
        result = await self.store(address, self.source_node.id, key, value)
        log.debug(f"call_store result: {result}")

        return self.handle_call_response(result, node_to_ask)


    def welcome_if_new(self, node):
       
        if not self.router.is_new_node(node):
            print("este nodo no es nuevo" + str(node))
            return

        print(f"Adding new node to routing table: {node}")
        for key, value in self.storage.store.items():
            keynode = KademliaNode(digest(key))
            neighbors = self.router.find_neighbors(keynode)
            if neighbors:
                last = neighbors[-1].distance_to(keynode)
                new_node_close = node.distance_to(keynode) < last
                first = neighbors[0].distance_to(keynode)
                this_closest = self.source_node.distance_to(keynode) < first
            if not neighbors or (new_node_close and this_closest):
             asyncio.ensure_future(self.call_store(node, key, value))
   
        self.router.add_contact(node)
        print(f"Node {node} added to routing table")
        
        print("Current state of routing table:")
        for bucket in self.router.buckets:
            print(f"Bucket range: {bucket.range}")
            for contact in bucket.get_nodes():
                if isinstance(contact.id, bytes):
                    print(f"Node ID: {contact.id.hex()}, Address: {contact.address}")
                else:
                    print(f"Node ID (str): {contact.id}, Address: {contact.address}")

    def handle_call_response(self, result, node):
        if result and isinstance(result, tuple):
            success, response_data = result
            if success:
                if isinstance(response_data, tuple) and len(response_data) == 2:
                    node_id = response_data[0]  
                    address = response_data[1]  
                    
            
                    if isinstance(address, tuple) and len(address) == 2:
                        ip, port = address
                        
                        self.welcome_if_new(KademliaNode(node_id, ip, port))
                    else:
                        log.error("Address format is invalid: %s", address)
                else:
                    log.error("Response data format is incorrect: %s", response_data)
            else:
                log.error("Ping failed")
        else:
            log.error("Invalid ping result: %s", result)
