from quart import request, send_file
from search_engine import upload_metadata_song, upload_song,get_all_values_from_network,download_song, search_by_metadata
import traceback, json
import base64, io
import asyncio
from client_node import ClientNode

async def upload_music(metadata_client_node, song_client_node):

    try:

        files = await request.files
        form = await request.form

        if 'file' not in files:
            return "No file part in the request", 400

        uploaded_file = files ['file']

       
        if uploaded_file.filename == '':
            return "No selected file", 400

        
        file_bytes = uploaded_file.read ()
       
        metadata = {
                "title":  form ['name'],
                "author": form ['author'],
                "album":  form ['album'],
                "genre":  form ['genre'],
                "total_chunks": 0
            }
        
        print(f"Subiendo cancion: {metadata}")
        metadata = await upload_song(song_client_node, metadata, file_bytes)

        print(f"Subiendo metadatos: {metadata}")
        await upload_metadata_song(metadata_client_node, metadata)

        return {'message': 'Música subida correctamente'}, 201

    except Exception as e:

        print(f"Error al subir música: {str(e)}") 
        return {'message': f'Error al subir música: {str(e)}'}, 500
    

async def stream_music(metadata_node, song_node, key):
    
    try:
        key = base64.b64decode (key)
        meta = await metadata_node.get (key, is_digested = True)
        if not meta:
            raise Exception ('la cancion no existe')
        meta = json.loads (meta)
        song_bytes = await download_song (song_node, meta)
        if not song_bytes:
            raise Exception ('la cancion no tiene chunks')
        stream = io.BytesIO (song_bytes)
        return await send_file (stream, mimetype = 'audio/mpeg')
    except Exception as e:
        print (e)
        traceback.print_exc ()
        return {'message': f'Error al transmitir música: {str(e)}'}, 500

async def list_music(metadata_client_node):
    try:
        songs = await get_all_values_from_network(metadata_client_node)
        return {'music': songs }, 200
    except Exception as e:
        print (e)
        traceback.print_exc ()
        return {'message': f'Error al listar música: {str(e)}'}, 500

async def search_music(metadata_node: ClientNode):
    try:
        command = await request.data
        command = command.decode ('utf8')
        command = command.split ()
        metadata = {}
        songs = []

        for i in range (len (command)):

            tuples: list[str] = command [i].split (':')
            tuples: list[str] = [ e.strip () for e in tuples ]
            key = tuples [0]
            tuples = list (map (lambda t: t[1], filter (lambda t: t[0] > 0, enumerate (tuples))))

            metadata [key] = ':'.join (tuples)

        print (f'searching for {metadata}')
        found = await search_by_metadata (metadata_node, metadata)
        return {'results': found }, 200
    except Exception as e:
        print (e)
        traceback.print_exc ()
        return {'message': f'Error al buscar música: {str(e)}'}, 500
