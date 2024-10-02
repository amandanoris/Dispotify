import unittest
from unittest.mock import MagicMock
from RPC import KademliaProtocol
from kademlia_node import KademliaNode

class Storage:
    def __init__(self):
        self.store = {}

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def items(self):
        return self.store.items()

    def get(self, key, default=None):
        return self.store.get(key, default)


class TestKademliaRPC(unittest.TestCase):

    def setUp(self):
        self.source_node = KademliaNode("8c9c6b150947ca38d092f344ff32786f7e79474e")
        self.storage = Storage()  
        self.ksize = 20
        self.protocol = KademliaProtocol(self.source_node, self.storage, self.ksize)

    def test_rpc_ping(self):
        sender = ("192.168.1.1", 5000)
        nodeid = "8c9c6b150947ca38d092f344ff32786f7e79474e"
        response = self.protocol.rpc_ping(sender, nodeid)
        self.assertEqual(response, (True, nodeid, sender))

    def test_rpc_store(self):
        sender = ("192.168.1.1", 5000)
        nodeid = "8c9c6b150947ca38d092f344ff32786f7e79474e"
        key = b"test_key"
        value = "test_value"

        response = self.protocol.rpc_store(sender, nodeid, key, value)
        self.assertTrue(response)
        self.assertIn(key, self.storage.store)  
        self.assertEqual(self.storage.store[key], value)  

    def test_rpc_find_node_existing(self):
        sender = ("192.168.1.1", 5000)
        nodeid = "8c9c6b150947ca38d092f344ff32786f7e79474e"
        key = b"test_key"

        self.protocol.router.find_neighbors = MagicMock(return_value=[KademliaNode("neighbor1"), KademliaNode("neighbor2")])

        response = self.protocol.rpc_find_node(sender, nodeid, key)
        self.assertEqual(response, [("neighbor1",), ("neighbor2",)])

    def test_rpc_find_node_non_existing(self):
        sender = ("192.168.1.1", 5000)
        nodeid = "8c9c6b150947ca38d092f344ff32786f7e79474e"
        key = b"non_existing_key"


        self.protocol.router.find_neighbors = MagicMock(return_value=[])

        response = self.protocol.rpc_find_node(sender, nodeid, key)
        self.assertEqual(response, [])

    def test_rpc_find_value_existing(self):
        sender = ("192.168.1.1", 5000)
        nodeid = "8c9c6b150947ca38d092f344ff32786f7e79474e"
        key = b"test_key"
        value = "test_value"
        self.storage[key] = value

        response = self.protocol.rpc_find_value(sender, nodeid, key)
        self.assertEqual(response, (True, value, sender))

    def test_rpc_find_value_non_existing(self):
        sender = ("192.168.1.1", 5000)
        nodeid = "8c9c6b150947ca38d092f344ff32786f7e79474e"
        key = b"non_existing_key"

        response = self.protocol.rpc_find_value(sender, nodeid, key)
        self.assertIsInstance(response, list)  

if __name__ == "__main__":
    unittest.main()
