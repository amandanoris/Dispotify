import unittest
import asyncio
from unittest.mock import AsyncMock
from kademlia_node import KademliaNode
from kbuckets import RoutingTable, KBucket
from RPC import KademliaProtocol
from storage import MusicStorage


class TestKademliaNode(unittest.TestCase):
    def test_node_creation(self):
        
        node1 = KademliaNode(b"testnode1")
        self.assertEqual(len(node1.id), 40)

      
        node2 = KademliaNode(12345)
        self.assertEqual(len(node2.id), 40)

        node3 = KademliaNode("testnode3")
        self.assertEqual(len(node3.id), 40)

    def test_distance_between_nodes(self):
       
        node1 = KademliaNode("node1")
        node2 = KademliaNode("node2")
        distance = node1.distance_to(node2)
        self.assertIsInstance(distance, int)
        self.assertGreater(distance, 0)


class TestRoutingTable(unittest.TestCase):
    def setUp(self):
        self.node = KademliaNode("testnode")
        self.storage = MusicStorage()
        self.protocol = KademliaProtocol(self.node, self.storage, ksize=20)
        self.routing_table = self.protocol.router

    def test_add_contact(self):
     
        new_node = KademliaNode("newnode")
        self.routing_table.add_contact(new_node)

        self.assertFalse(self.routing_table.is_new_node(new_node))

    def test_find_neighbors(self):
    
        for i in range(5):
            node = KademliaNode(f"node{i}")
            self.routing_table.add_contact(node)

        target_node = KademliaNode("target")
        neighbors = self.routing_table.find_neighbors(target_node)
        self.assertEqual(len(neighbors), 5)


class TestKademliaProtocol(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.node = KademliaNode("testnode")
        self.storage = MusicStorage()
        self.protocol = KademliaProtocol(self.node, self.storage, ksize=20)

    async def test_rpc_ping(self):
   
        sender = ("127.0.0.1", 9999)
        nodeid = "testnodeid"
       
        self.protocol.rpc_ping = AsyncMock(return_value=(nodeid, sender))
        
        response = await self.protocol.rpc_ping(sender, nodeid)
        self.assertEqual(response[0], nodeid)
        self.assertEqual(response[1], sender)

    async def test_call_ping(self):
        
        some_node = KademliaNode("some_node")
        self.protocol.call_ping = AsyncMock(return_value="response")
        
        result = await self.protocol.call_ping(some_node)
        self.assertIsNotNone(result)

    async def test_handle_call_response(self):
    
        some_response = "response"
        some_node = KademliaNode("some_node")
        self.protocol.handle_call_response = AsyncMock(return_value=True)
        
        result = await self.protocol.handle_call_response(some_response, some_node)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
