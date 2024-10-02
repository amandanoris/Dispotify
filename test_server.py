
import unittest
from network import Server

class TestServer(unittest.TestCase):

    def setUp(self):
        self.server = Server()

    async def test_server_initialization(self):
        self.assertIsNotNone(self.server)
        self.assertEqual(self.server.ksize, 20)
        self.assertEqual(self.server.alpha, 3)

    async def test_listen(self):
        await self.server.listen(8468)
        self.assertIsNotNone(self.server.transport)
        self.assertIsNotNone(self.server.protocol)

    def tearDown(self):
        self.server.stop()

if __name__ == '__main__':
    unittest.main()
