import asyncio
import logging
from utils import list_broadcast_addresses
from search_engine import upload_metadata_song, upload_song, get_all_values_from_network, download_song, search_by_metadata
from client_node import ClientNode

log = logging.getLogger(__name__)

async def discovery_task(client_node, port, broadcast_port):
    interfaces = list_broadcast_addresses()

    discovery_tasks = []
    for element in interfaces:
        print(f"Iniciando descubrimiento en la interfaz {element}")
        discovery_tasks.append(client_node.start_with_auto_discovery(
            port=port,
            broadcast_port=broadcast_port,
            interface=element
        ))

    await asyncio.gather(*discovery_tasks)

async def interactive_mode(client_node):
    """
    Este modo interactivo permitirá ejecutar store y search desde la terminal.
    """
    print("Modo interactivo iniciado. Ingrese comandos:")
    print("Comandos disponibles:")
    print("store <clave> <valor>  - Almacenar un valor en la red.")
    print("search <clave>         - Buscar un valor en la red.")
    print("exit                   - Terminar el programa.")

    while True:
        user_input = input("> ").strip ()
        command = user_input.split ()

        if len(command) == 0:
            continue

        elif command[0] == "upload_metadata" and len(command) == 4:
            metadata = {
                "title": command[1],
                "author": command[2],
                "genre": command[3],
                "total_chunks": 0
            }
            print(f"Subiendo metadatos: {metadata}")
            await upload_metadata_song(client_node, metadata)
        
        elif command[0] == "upload_song" and len(command) == 5:
            metadata = {
                "title": command[1],
                "author": command[2],
                "genre": command[3],
                "total_chunks": 0
            }
            path = command[4]
            print(f"Subiendo cancion: {metadata}")
            await upload_song(client_node, metadata, path)

        elif command[0] == "download_song" and len(command) == 5:
            metadata = {
                "title": command[1],
                "author": command[2],
                "genre": command[3],
                "total_chunks": int(command[4])
            }
            print(f"Bajando cancion")
            await download_song(client_node, metadata)

        elif command[0] == "list" and len(command) == 1:
            print(f"Listando todas las canciones")
            #await get_all_values_from_network(client_node)
            await get_all_values_from_network(client_node)
        
        elif command[0] == "search_by_metadata" and len(command) > 1:
            metadata = {}

            for i in range (1, len (command)):

                tuples: list[str] = command [i].split (':')
                tuples: list[str] = [ e.strip () for e in tuples ]
                key = tuples [0]
                tuples = filter (lambda t: t[0] > 0, enumerate (tuples))
                tuples = [ t[1] for t in tuples ]

                metadata [key] = ':'.join (tuples)

            found = await search_by_metadata (client_node, metadata)

            print (f"Buscando por metadatos: {metadata}")
            print (f'encontrado: {found}')
        
        else:
            print("Comando no válido. Intente de nuevo.")
           
        
        
        
        
        
        '''
        elif command[0] == "store" and len(command) == 3:
            key = command[1]
            value = command[2]
            print(f"Almacenando {key}: {value}")
            await client_node.store_on_network(key, value)

        elif command[0] == "search" and len(command) == 2:
            key = command[1]
            print(f"Buscando {key}")
            await client_node.search_on_network(key)

        elif command[0] == "exit":
            print("Saliendo del programa...")
            break
        '''
             



async def main(port, broadcast_port):
    client_node = ClientNode()

    # Iniciamos el descubrimiento de nodos en segundo plano
    discovery = asyncio.create_task(discovery_task(client_node, port, broadcast_port))

    # Modo interactivo para recibir comandos
    await interactive_mode(client_node)

    # Cancelamos el descubrimiento cuando salimos del modo interactivo
    discovery.cancel()

    try:
        await discovery
    except asyncio.CancelledError:
        print("Tarea de descubrimiento cancelada.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nodo cliente de la red")
    parser.add_argument("--port", type=int, help="Puerto para escuchar", default=8418)
    parser.add_argument("--broadcast_port", type=int, help="Puerto de descubrimiento", default=2222)

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(args.port, args.broadcast_port))
    finally:
        loop.close()
