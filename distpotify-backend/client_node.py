
from network import Server
from RPC import KademliaProtocol
from storage import IStorage

class ClientNode(Server):

    def __init__(self, ksize=20, alpha=3, node_id=None):
        super().__init__(ksize, alpha, node_id, storage=EmptyStorage())
        self.protocol: KademliaProtocol = self._create_protocol()
        print(f"Nodo cliente {self.node.long_id} inicializado")
    
    async def get_all_values_from_network(self):
        all_values = []
       
        for neighbor in self.bootstrappable_neighbors():
            try:
                
                neighbor_values = await self.protocol.call_get_all_values(neighbor)
                if neighbor_values:
                    
                    all_values.extend(neighbor_values)
            except Exception as e:
                print(f"Error al obtener valores del vecino {neighbor}: {e}")
        
        if all_values:
            print("Valores encontrados en la red:")
            print(all_values)
            for key, value in all_values:
                print(f"{key}: {value}")
        else:
            print("No se encontraron valores en la red.")
        return all_values


class EmptyStorage(IStorage):
    def __setitem__(self, key, value):
        pass

    def __getitem__(self, key):
        return None

    def get(self, key, default=None):
        return None

    def iter_older_than(self, seconds_old):
        return iter([])

    def __contains__(self, key):
        return False

    def __iter__(self):
        return iter([])