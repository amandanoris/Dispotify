import asyncio
from network import Server

async def run_servers():
    server1 = Server(node_id='node1_id')
    await server1.listen(port=5678)

    server2 = Server(node_id='node2_id')
    await server2.listen(port=5679)

    await server1.bootstrap([('127.0.0.1', 5679)])  

    await server1.set("mi_clave", "mi_valor")

    value = await server2.get("mi_clave")
    print(f"Valor recuperado desde server2: {value}")  

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_servers())
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        loop.close()
