from collections import Counter
import logging

from kademlia_node import KademliaNode, NodeHeap
from utils import digest
import asyncio
log = logging.getLogger(__name__)  

class SpiderCrawl:
    """
    Base class for spider crawlers in the Kademlia network.
    """
    def __init__(self, protocol, target, nodes, ksize, alpha):
        self.protocol = protocol
        self.target = target
        self.nodes = nodes
        self.ksize = ksize
        self.alpha = alpha

    async def find(self):
        """
        Crawl the network for a target key or node.
        """
        pass


class NodeSpiderCrawl(SpiderCrawl):
    async def find(self):
        heap = NodeHeap()
        results = []                               

        for node in self.nodes:
            print(f"Enviando ping al nodo: {node.address}")
            result = await self.protocol.call_ping(node) 
            print("result dentro del for es "+ str(result))
            results.append(result)  

        print("results en el NodeSpiderCrawl es " + str(results))

        responses = await asyncio.gather(*[res for res in results if res is not None], return_exceptions=True)
        print("responses en el NodeSpiderCrawl es " + str(responses))

        for response in responses:
            if isinstance(response, Exception):
                log.error(f"Excepción durante el ping: {response}")
                continue
            if response is None:
                log.warning("Respuesta None durante el ping")
                continue

            try:
                success = response[0]
                if success:
                    node_id = response[1][0]
                    sender = response[1][1]
                    print(f"Añadiendo nodo al heap: ID {node_id}, Sender {sender}")
                    heap.add(KademliaNode(node_id, sender[0], sender[1]))

                    print("Nodos actuales en el heap:")
                    for node in heap.get_closest(self.ksize):
                        print(f"Node ID: {node.id.hex()}, Address: {node.address}")
                else:
                    log.warning("El ping no fue exitoso")
            except Exception as e:
                log.error(f"Error procesando la respuesta del ping: {e}")

        return heap.get_closest(self.ksize)


class ValueSpiderCrawl(SpiderCrawl):
    async def find(self):
        """
        Crawl nodes to find the value closest to target.
        """
        heap = NodeHeap()
        results = []

        for node in self.nodes:
            result = self.protocol.call_get(node, self.target.id)  # No hagas await aquí.
            results.append(result)

        responses = await asyncio.gather(*results)

        for response in responses:
            if response[0]:
                heap.add(response[1])

        return heap.get_closest(self.ksize)
