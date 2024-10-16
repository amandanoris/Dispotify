import random
import pickle
import asyncio
import logging
import socket
from RPC import KademliaProtocol
from utils import digest,get_local_ip
from storage import ForgetfulStorage
from kademlia_node import Node
from look import ValueSpiderCrawl, NodeSpiderCrawl, KeySpiderCrawl, SearchByMetadataSpiderCrawl
from utils import check_dht_value_type


log = logging.getLogger(__name__)  


class Server:

    protocol_class = KademliaProtocol

    def __init__(self, ksize=20, alpha=3, node_id=None, storage=None):

        self.ksize = ksize
        self.alpha = alpha
        self.storage = storage or ForgetfulStorage()
        self.node = Node(node_id or digest(random.getrandbits(255)))
        self.transport = None
        self.protocol: None | KademliaProtocol = None

    def stop(self):
        if self.transport is not None:
            self.transport.close()

        if self.refresh_loop:
            self.refresh_loop.cancel()

        if self.save_state_loop:
            self.save_state_loop.cancel()

    def _create_protocol(self):
        return self.protocol_class(self.node, self.storage, self.ksize)

    async def listen(self, port, interface='0.0.0.0'):
 
        loop = asyncio.get_event_loop()
        listen = loop.create_datagram_endpoint(self._create_protocol,
                                               local_addr=(interface, port))
        log.info("Nodo %i escuchando en %s:%i",
                 self.node.long_id, interface, port)
        self.transport, self.protocol = await listen
        self.refresh_table()
    
    async def broadcast_discovery(self, broadcast_port=2222):
        log.info("Enviando mensaje de descubrimiento a la red")

        local_ip = get_local_ip()

        broadcast_address = ('<broadcast>', broadcast_port)  
        discovery_message = f"DISCOVERY:{self.node.port}:{local_ip}".encode('utf-8')

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(discovery_message, broadcast_address)

    async def listen_for_discovery(self, listen_port=2222,interface='0.0.0.0'):
 
        log.info(f"Escuchando mensajes de descubrimiento en el puerto {listen_port}")
    
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            log.warning("SO_REUSEPORT no está disponible en este sistema operativo")

        sock.setblocking(False) 
        sock.bind(("", listen_port))  

        loop = asyncio.get_event_loop()

        async def handle_discovery():

            while True:
                print("Esperando mensajes de descubrimiento...")
                print("vecinos" + str(self.bootstrappable_neighbors()))
                try:

                    data = await loop.sock_recv(sock, 1024)

                    try:

                        message = data.decode('utf-8')
                        print(message)
                    except UnicodeDecodeError as e:
                        log.error(f"Error al decodificar el mensaje: {e}. Datos crudos: {data}")
                        continue  

                    if message.startswith("DISCOVERY:"):
                        parts = message.split(":")
                        if len(parts) == 3:
                            _, node_port, node_ip = parts
                            
                            print(f"Descubrimiento de nodo {node_port} desde {node_ip} interface {interface} esta haciendo bootstrap {self.node.id.hex()}")
                           
                            await self.bootstrap([(node_ip, int(node_port))])
                        else:
                            print(f"Mensaje de descubrimiento mal formado: {message}")
                except Exception as e:
                    print(f"Error inesperado: {e}")

        
        loop.add_reader(sock.fileno(), lambda: asyncio.create_task(handle_discovery()))

        try:
           
            await asyncio.Future()
        except asyncio.CancelledError:
            print("Escucha cancelada, cerrando socket...")
        finally:
            loop.remove_reader(sock.fileno())
            sock.close()

            await self.listen_for_discovery (listen_port = listen_port, interface = interface)

    async def auto_discovery(self, broadcast_port=2222,interface='0.0.0.0'):
       
        await asyncio.gather(
            self.broadcast_discovery(broadcast_port),
            self.listen_for_discovery(broadcast_port,interface)
        )

    async def start_with_auto_discovery(self, port, broadcast_port=2222, interface='0.0.0.0'):
      
        local_ip = get_local_ip()
   
        self.node.port=port
        await self.listen(port, interface=local_ip)
    
        await self.auto_discovery(broadcast_port,interface)
    
    def refresh_table(self):
        #print("Refreshing routing table")
        asyncio.ensure_future(self._refresh_table())
        loop = asyncio.get_event_loop()
        self.refresh_loop = loop.call_later(30, self.refresh_table)

    async def _refresh_table(self):
        assert (self.protocol)
        results = []
        for node_id in self.protocol.get_refresh_ids():
            node = Node(node_id)
            nearest = self.protocol.router.find_neighbors(node, self.alpha)
            spider = NodeSpiderCrawl(self.protocol, node, nearest,
                                     self.ksize, self.alpha)
            results.append(spider.find())

        await asyncio.gather(*results)

        #print('reinsertando valores')
        #print("esto no deberia estar vacio"+str(self.storage.iter_older_than(0)))
        for dkey, value in self.storage.iter_older_than(30):
            #print("lo que voy a reinsertar es " + str(value))
            await self.set_digest(dkey, value)
        #print('saliendo de la reinsercion de valores')

    def bootstrappable_neighbors(self):
        neighbors = self.protocol.router.find_neighbors(self.node)
        return [tuple(n)[-2:] for n in neighbors]

    async def bootstrap(self, addrs):
        log.debug("Attempting to bootstrap node with %i initial contacts",
                  len(addrs))
        cos = list(map(self.bootstrap_node, addrs))
        gathered = await asyncio.gather(*cos)
        nodes = [node for node in gathered if node is not None]
        spider = NodeSpiderCrawl(self.protocol, self.node, nodes,
                                 self.ksize, self.alpha)
        return await spider.find()

    async def bootstrap_node(self, addr):
        
        result = await self.protocol.ping(addr, self.node.id)
        print(f"Resultado del ping: {result}")
        return Node(result[1], addr[0], addr[1]) if result[0] else None

    async def get(self, key, is_digested = False):

        #print("Looking up key %s", key)
        if(is_digested == False):
          dkey = digest(key)
        else:
            dkey = key
        if self.storage.get(dkey) is not None:
            return self.storage.get(dkey)
        node = Node(dkey)
        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            print("There are no known neighbors to get key %s", key)
            return None
        spider = ValueSpiderCrawl(self.protocol, node, nearest,
                                  self.ksize, self.alpha)
        return await spider.find()

    async def get_keys(self):

        node = self.node
        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            keys = []
            for k, _ in self.storage:
                keys.append (k)
            return keys
        spider = KeySpiderCrawl(self.protocol, node, nearest,
                                  self.ksize, self.alpha)
        return await spider.find()
    
    async def set(self, key, value):
        if not check_dht_value_type(value):
            raise TypeError(
                "Value must be of type int, float, bool, str, or bytes"
            )
        log.info("setting '%s' = '%s' on network", key, value)
        dkey = digest(key)
        return await self.set_digest(dkey, value)

    async def set_digest(self, dkey, value):

        node = Node(dkey)

        nearest = self.protocol.router.find_neighbors(node)
        #print('el vecino mas cercano es' + str(nearest))
        if not nearest:
            print("There are no known neighbors to set key %s",
                        dkey.hex())
            return False

        spider = NodeSpiderCrawl(self.protocol, node, nearest,
                                 self.ksize, self.alpha)
        nodes = await spider.find()
        #print("setting '%s' on %s", dkey.hex(), list(map(str, nodes)))

        if len (nodes) == 0:
            return False
        biggest = max([n.distance_to(node) for n in nodes])
        if self.node.distance_to(node) < biggest:
            self.storage[dkey] = value
        results = [self.protocol.call_store(n, dkey, value) for n in nodes]
        return any(await asyncio.gather(*results))
    
    async def search_by_metadata (self, search_criteria):
        node =self.node
        nearest=self.protocol.router.find_neighbors(node)
        if not nearest:
            raise Exception ('problema del que te hable')
        spider=SearchByMetadataSpiderCrawl (self.protocol,node,nearest,self.ksize,self.alpha)
        return await spider.find(search_criteria)
        
