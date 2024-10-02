import asyncio
from network import Server

async def start_bootstrap_node():
   
    server = Server()

    await server.listen(5678)
    print("Bootstrap node listening on port 5678")

    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(start_bootstrap_node())
