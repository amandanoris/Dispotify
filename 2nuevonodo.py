import asyncio
from network import Server

async def start_new_node(bootstrap_address):
   
    new_node = Server()
  
    await new_node.listen(0) 
    print(f"New node listening on a random port")

    _, port = new_node.transport.get_extra_info('sockname')
    print(f"New node listening on port {port}")

    success = await new_node.bootstrap([bootstrap_address])
    if success:
        print(f"Node joined the network successfully with bootstrap node at {bootstrap_address}")
    else:
        print("Failed to join the network. Check the bootstrap address and port.")

    await new_node.print_neighbors()

    while True:
        await new_node.print_neighbors()
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(start_new_node(('127.0.0.1', 5678)))
