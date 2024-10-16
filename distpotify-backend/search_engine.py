import asyncio
import base64
import json  

MAX_CHUNK_SIZE = 4000  

async def upload_metadata_song(server, song_metadata):

    metadata_json = json.dumps(song_metadata)
    await server.set(f"metadata_{song_metadata['title']}", metadata_json)
    print('Subidos los metadatos a la red de metadatos')

async def upload_song(chunks_server, song_metadata, song_bytes):

    chunks = [song_bytes[i:i + MAX_CHUNK_SIZE] for i in range(0, len(song_bytes), MAX_CHUNK_SIZE)]
    song_metadata['total_chunks'] = len(chunks)  # Actualizamos el número total de fragmentos
    #print(f"Archivo dividido en {len(chunks)} fragmentos de {MAX_CHUNK_SIZE} bytes.")

    for i, chunk in enumerate(chunks):
        chunk_key = f"{song_metadata['title']}_chunk_{i}"
        #print(f'Subiendo el fragmento {i + 1}/{len(chunks)} a la red de chunks con clave {chunk_key}')
        await chunks_server.set(chunk_key, base64.b64encode(chunk).decode('utf-8'))  # Subir cada fragmento a la red de chunks

    print("Todos los fragmentos han sido subidos correctamente.", len(chunks))
    return song_metadata


async def download_song(chunks_server, retrieved_metadata):
    
    retrieved_song = b""
    
    for i in range(retrieved_metadata['total_chunks']):
        chunk_key = f"{retrieved_metadata['title']}_chunk_{i}"
        #print(f"Recuperando el fragmento {i + 1}/{retrieved_metadata['total_chunks']} de la red de chunks con clave {chunk_key}")
        encoded_chunk = await chunks_server.get(chunk_key)

        if encoded_chunk is None:
            print(f"Error: No se pudo recuperar el fragmento {i}.")
            return

        chunk = base64.b64decode(encoded_chunk)
        retrieved_song += chunk

    #output_path = f"{retrieved_metadata['title']}.mp3"
    #with open(output_path, 'wb') as output_file:
    #    output_file.write(retrieved_song)
    #print(f"Archivo reconstruido guardado en {output_path}")

    return retrieved_song

async def wrap_values(server, keys):

    all_values =[]

    for key in keys:
        
        try:
            value = await server.get(key, is_digested=True) 
            print("value: " + str(value))

            if value:
               
                try:
                    metadata = json.loads(value)
                    if all(k in metadata for k in ['title', 'author', 'genre', 'total_chunks']):
                        all_values.append({**metadata, 'id': base64.b64encode (key).decode ('utf8')}) 
                                    
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            print(f"Error al obtener valor para la clave {key}: {e}")

    print("los valores que estan en ka red son"+str(all_values))
    return all_values

async def get_all_values_from_network(server):
   
    network_keys = await server.get_keys()
    return await wrap_values (server, network_keys)

async def search_by_metadata(metadata_node, search_criteria):

    print(f"Buscando canciones con los criterios: {search_criteria}...")

    network_keys = await metadata_node.search_by_metadata (search_criteria)
    return await wrap_values (metadata_node, network_keys)