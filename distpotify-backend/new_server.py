import asyncio
from network import Server
from utils import list_broadcast_addresses

async def main(port, broadcast_port):

    print("Inicializando server...")
    interfaces = list_broadcast_addresses()  

    new_server = Server()
    print('Servidor creado')

    tasks = []  
    for element in interfaces:
        print(f"Iniciando descubrimiento en la interfaz {element}")
        tasks.append(asyncio.create_task(
            new_server.start_with_auto_discovery(port=port, broadcast_port=broadcast_port, interface=element)
        ))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Server con auto-descubrimiento")
    parser.add_argument("--port", type=int, help="Puerto del servidor")
    parser.add_argument("--broadcast_port", type=int, help="Puerto del broadcast")
    args = parser.parse_args()

    port = args.port
    broadcast_port = args.broadcast_port

    asyncio.run(main(port, broadcast_port))
