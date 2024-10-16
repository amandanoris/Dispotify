from quart import Quart
from quart_cors import cors
from controllers.music_controller import upload_music, stream_music, list_music, search_music
from client_node import ClientNode
from client_node_test import discovery_task
import asyncio

if __name__ == '__main__':

    app = cors (Quart (__name__), allow_origin = '*')

    metadata_client_node = ClientNode ()
    song_client_node = ClientNode ()

    @app.before_request
    async def create_clients ():

        app.before_request_funcs [None].remove (create_clients)

        # cliente para metadatos
        task1 = asyncio.create_task (discovery_task (metadata_client_node, 8418, 2222))
        # cliente para canciones
        task2 = asyncio.create_task (discovery_task (song_client_node, 8419, 2223))

        await task1
        await task2

    @app.route('/api/upload', methods=['POST'])
    async def upload ():

        return await upload_music (metadata_client_node, song_client_node)

    @app.route('/stream/<string:kademlia_key>', methods=['GET'])
    async def stream (kademlia_key):
        return await stream_music(metadata_client_node, song_client_node, kademlia_key)

    @app.route('/api/music', methods=['GET'])
    async def api_list_music():
        return await list_music(metadata_client_node)

    @app.route('/api/search', methods=['POST'])
    async def api_search_music():
        return await search_music(metadata_client_node)

    app.run (host='0.0.0.0', port=5000, debug=True)
