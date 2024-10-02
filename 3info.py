from storage import MusicStorage
from network import Server
import asyncio

async def main():
  
    print("Inicializando nodo Kademlia para subir información...")

    kademlia_server = Server() 
    await kademlia_server.listen(0) 

    _, port = kademlia_server.transport.get_extra_info('sockname')
    print(f"New node listening on port {port}")

    music_storage = MusicStorage(kademlia_server=kademlia_server)

    bootstrap_node = ('127.0.0.1', 5678)
    print(f"Intentando hacer bootstrap con el nodo {bootstrap_node}")
    if await kademlia_server.bootstrap([bootstrap_node]):
        print(f"Nodo unido exitosamente a la red con el nodo bootstrap en {bootstrap_node}")
    else:
        print("Error: No se pudo unir a la red")

    song_metadata = {
        'title': 'Song Title',
        'author': 'Song Author',
        'genre': 'Song Genre'
    }
    print(f"Subiendo la canción con metadatos: {song_metadata}")
    
    song_hash = await music_storage.add_song('2.mp3', song_metadata)
    print(f"La canción fue subida con éxito. Hash generado: {song_hash}")

    print("Esperando unos segundos para asegurar que la canción se propague por la red...")
    await asyncio.sleep(5)  

    print("Inicializando otro nodo Kademlia para obtener la información desde la red...")

    kademlia_server_2 = Server()
    await kademlia_server_2.listen(0)  

    music_storage_2 = MusicStorage(kademlia_server=kademlia_server_2)  
    print("el segundo servidor de guardar musica "+  str(music_storage_2.kademlia_server))

    _, port = kademlia_server_2.transport.get_extra_info('sockname')
    print(f"New node listening on port {port}")

   
    print(f"Intentando hacer bootstrap del segundo nodo con {bootstrap_node}")
    if await kademlia_server_2.bootstrap([bootstrap_node]):
        print("El segundo nodo se unió exitosamente a la red")
    else:
        print("Error: El segundo nodo no pudo unirse a la red")

    print(f"Intentando obtener la canción desde la red con el hash: {song_hash}")
    print("el segundo servidor de guardar musica "+  str(music_storage_2.kademlia_server))
   
    #aki se esta cogiendo del mismo nodo que se subio, no del otros
    retrieved_metadata = await music_storage.get(song_hash)

    if retrieved_metadata:
        print(f"La canción fue obtenida exitosamente desde la red. Metadatos: {retrieved_metadata}")
        metadata = retrieved_metadata['metadata']
        print(str(metadata))
        if metadata == song_metadata:
            print("Verificación exitosa: Los metadatos obtenidos coinciden con los que se subieron.")
        else:
            print("Error: Los metadatos obtenidos no coinciden con los que se subieron.")
    else:
        print("Error: No se pudo obtener la canción desde la red.")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
