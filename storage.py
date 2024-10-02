import os
import hashlib
from datetime import datetime, timedelta
import json
import asyncio

STORAGE_DIR = os.path.join(os.getcwd(), 'music_storage')  # local

class MusicStorage:
    """
    Implementación de almacenamiento que maneja archivos de audio y metadatos asociados utilizando Kademlia.
    """
    def __init__(self, storage_dir=STORAGE_DIR, kademlia_server=None):
        self.storage_dir = storage_dir
        self.store = {}
        self.kademlia_server = kademlia_server 
        if self.kademlia_server is None:
            print("Error: Kademlia server is None a la hora de inicializar el music storage!")
        else:
            print("Kademlia server initialized correctly.")
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def iter_older_than(self, days):
        """
        Itera sobre las canciones almacenadas y devuelve aquellas cuya 
        fecha de almacenamiento es anterior al número de días especificado.
        """
        limit = datetime.now() - timedelta(days=days)
        for file_hash, song in self.store.items():
            if song['timestamp'] < limit:
                yield file_hash, song

    async def get(self, file_hash):
        """
        Recupera la canción almacenada localmente o sus metadatos desde Kademlia.

        Args:
            file_hash (str): El hash del archivo de la canción que se busca.

        Returns:
            dict or None: Devuelve un diccionario con la información de la canción si se encuentra, de lo contrario, None.
        """
        # local
        if file_hash in self.store:
           return self.store[file_hash]
        
        #  desde Kademlia
        print("servidor de kademlia pa buscar la cancion" + str(self.kademlia_server))
        metadata = await self.get_song_metadata(file_hash)
        
        if metadata:
        
            self.store[file_hash] = {
                'metadata': metadata,
                'timestamp': datetime.now()
            }
            return self.store[file_hash]
        else:

            return None

    def _generate_file_hash(self, file_path):
        """Genera un hash SHA-1 a partir del archivo."""
        sha1 = hashlib.sha1()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(65536)  # Leer en bloques de 64KB
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest()
       
    

    async def add_song(self, file_path, metadata):
 
        #local
        file_hash = self._generate_file_hash(file_path)
        file_extension = os.path.splitext(file_path)[1]
        file_name = f"{file_hash}{file_extension}"
        destination = os.path.join(self.storage_dir, file_name)
        

        os.rename(file_path, destination)

        self.store[file_hash] = {
            'file_path': destination,
            'metadata': metadata,
            'timestamp': datetime.now()
        }
        print(f"Song '{metadata['title']}' added locally with hash {file_hash}.")
        
        metadata_json = json.dumps(metadata)
        
        # Almacenar los metadatos en Kademlia como una cadena JSON
        await self.kademlia_server.set(file_hash, metadata_json)
        print(f"Metadata for '{metadata['title']}' stored in Kademlia.")
        
        return file_hash

        
    async def get_song_metadata(self, file_hash):
        """Recupera los metadatos de la canción desde Kademlia."""
        if self.kademlia_server is None:
            print("Error: Kademlia server is None!")
        else:
   
            metadata_json = await self.kademlia_server.get(file_hash)

            if metadata_json:
                try:
                    return json.loads(metadata_json)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON for hash: {file_hash}")
                    return None
            return None

    
    async def search_songs(self, search_query, search_type='title'):
        """
        Busca canciones basadas en los metadatos (título, autor, género, etc.) utilizando Kademlia.
        
        Args:
            search_query (str): El término de búsqueda.
            search_type (str): El tipo de búsqueda (puede ser 'title', 'author', 'genre', etc.).
        """
        all_songs = self.store  
         
        #esto esta local

        results = []
        for file_hash, song in all_songs.items():
            if search_query.lower() in song['metadata'].get(search_type, "").lower():
                results.append({
                    'hash': file_hash,
                    'metadata': song['metadata']
                })
        return results
