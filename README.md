# Distpotify - Spotify Distribuido

| **Nombre**                   | **Grupo** | **Github**                                           |
|------------------------------|-----------|------------------------------------------------------|
| Juan Miguel Pérez Martínez    | C-412     | [@juan-miguel](https://github.com/JuanMiguel01)       |
| Amanda Noris Hernández        | C-412     | [@amanda-noris](https://github.com/amandanoris)     |

## Descripción

**Distpotify** es un sistema distribuido inspirado en Spotify que permite a cualquier host conectarse y reproducir música. Este sistema cuenta con una interfaz que permite subir, listar, buscar y reproducir música utilizando metadatos como género, autor, álbum y nombre de la canción. El sistema está diseñado para ser tolerante a fallos y mantener la reproducción continua de música incluso ante fallas en los nodos.

### Características principales:

- **Subida, búsqueda y reproducción de música**: Los usuarios pueden interactuar con el sistema mediante una interfaz simple para manejar canciones y sus metadatos.
- **Sistema distribuido**: Implementa una red de nodos distribuidos con roles específicos, como almacenamiento de música, gestión de metadatos y enrutamiento de pedidos.
- **Autodescubrimiento y tolerancia a fallos**: Utiliza Kademlia para garantizar la replicación de datos, seguridad ante fallas y autodescubrimiento de nuevos nodos en la red.
- **Reproducción continua**: La música no se interrumpe en caso de fallos de nodos, garantizando una experiencia de usuario fluida.

## Tecnologías Utilizadas

- **Backend**: Python.
- **Frontend**: JavaScript (NPM).


## Estructura del Proyecto

### Archivos Importantes

- **`protocol.py`**: Contiene la implementación de todos los procedimientos RPC y las llamadas entre nodos en la red.
  
- **`node.py`**: Implementa la lógica de un nodo individual dentro de la red, incluyendo la gestión de los vecinos, enrutamiento y almacenamiento de datos.
  
- **`server.py`**: Esta clase maneja la vista de alto nivel de un nodo y permite que un nodo actúe como servidor dentro de la red. Es el punto de inicio para que un nodo comience a escuchar y participar activamente en la red.

- **`search_engine.py`**: Implementa las funcionalidades de búsqueda y manipulación de datos en la red distribuida. Los métodos incluyen:
  - `async def search_by_metadata(metadata_node, search_criteria)`
  - `async def get_all_values_from_network(server)`
  - `async def download_song(chunks_server, retrieved_metadata)`
  - `async def upload_metadata_song(server, song_metadata)`
  - `async def upload_song(chunks_server, song_metadata, file_path)`

- **`clientNode.py`**: Implementa un nodo cliente que interactúa con la red para almacenar y recuperar datos. También puede obtener todos los valores de la red. Ejemplo de métodos:
  - `async def store_on_network(self, key, value)`
  - `async def search_on_network(self, key)`
  - `async def get_all_values_from_network()`

### Instalación y Ejecución

#### 1. Clonar el repositorio

```bash
git clone https://github.com/usuario/distpotify.git
cd distpotify
````

#### 2. Frontend
Para ejecutar el frontend:

````bash
npm start
````

#### 3. Backend
Para iniciar el backend, simplemente ejecuta:
    
    ````bash
    python3 app.py
    ````

#### 4. Levantar Nodos en la Red
Cada nodo necesita un puerto específico para funcionar. Para iniciar nodos de almacenamiento de música y metadatos, sigue estos pasos:

````bash
python3 new_server.py --port <PUERTO> --broadcast <PUERTO_BROADCAST>
````
#### 5. Autodescubrimiento de Nodos
El autodescubrimiento utiliza un mecanismo de broadcast para encontrar nodos vecinos en la red. El proceso de autodescubrimiento se realiza en paralelo mientras los nodos inician.

Código clave de autodescubrimiento:

````python
async def auto_discovery(self, broadcast_port=2222,interface='0.0.0.0'):
    await asyncio.gather(
        self.broadcast_discovery(broadcast_port),
        self.listen_for_discovery(broadcast_port,interface)
    )
````
El nodo también escucha los mensajes de broadcast para conectarse automáticamente con otros nodos:

````python	
async def listen_for_discovery(self, listen_port=2222,interface='0.0.0.0'):
    log.info(f"Escuchando mensajes de descubrimiento en el puerto {listen_port}")
````



# Funcionamiento del Sistema Distribuido
## Autodescubrimiento
Distpotify implementa un sistema de autodescubrimiento basado en broadcast UDP. Los nodos envían y escuchan mensajes de broadcast para descubrir otros nodos y conectarse a ellos mediante Kademlia. Los nodos pueden hacer bootstrap para integrarse a la red automáticamente cuando detectan nuevos vecinos.

Broadcast de descubrimiento: Cada nodo envía un mensaje de broadcast en la red local

Escucha de descubrimiento: Los nodos también escuchan continuamente mensajes de descubrimiento para establecer conexiones

# Funcionalidades del Nodo Cliente
El nodo cliente puede almacenar y recuperar datos de la red distribuida usando los métodos RPC implementados.

#### Almacenamiento en la red:

````python	
    async def store_on_network(self, key, value):
        success = await self.set(key, value)
````

#### Búsqueda en la red:

````python 
async def search_on_network(self, key):
    value = await self.get(key)
````

#### Obtener todos los valores de la red:

````python 
    async def get_all_values_from_network(self):
    neighbor_values = await self.protocol.call_get_all_values(neighbor)
````


# Notas Adicionales
Nuestra implementación de Kademlia ofrece funcionalidades para replicación, seguridad ante fallos y autodescubrimiento. Los nodos se comunican de forma eficiente mediante RPC y utilizan tablas de enrutamiento para almacenar referencias a otros nodos.

Roles de los nodos: Cada nodo tiene un rol específico, como almacenamiento de música o manejo de metadatos, también tenemos los nodos de cliente que se encargan de realizar las peticiones. Esto permite la especialización de nodos, pero varios roles pueden coexistir en un mismo host.

Tolerancia a fallos: En caso de que un nodo falle, los datos almacenados en la red se replican, asegurando que no haya pérdida de información crítica, como la música o los metadatos siempre debe existir al menos un nodo de cada tipo para que la red siga funcionando.
