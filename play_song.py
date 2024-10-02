import requests
import os
import pygame

SERVER_URL = "http://127.0.0.1:5000"

def download_song(file_hash):
    """Descarga la canción desde el servidor."""
    response = requests.get(f"{SERVER_URL}/download/{file_hash}")
    if response.status_code != 200:
        print("Error al descargar la canción:", response.json().get("error"))
        return None, None
    
    data = response.json()
    metadata = data['metadata']
    file_path = data['file_path']

    if not os.path.exists(file_path):
   
        print(f"Descargando '{metadata['title']}'...")
        download_response = requests.get(f"{SERVER_URL}/music_storage/{os.path.basename(file_path)}", stream=True)
        if download_response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in download_response.iter_content(1024):
                    f.write(chunk)
            print("Descarga completada.")
        else:
            print("Error al descargar el archivo de música.")
            return None, None
    else:
        print("El archivo ya existe localmente.")
    
    return file_path, metadata

def play_music(file_path):
    """Reproduce la canción usando pygame."""
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    print("Reproduciendo música... Presiona Ctrl+C para detener.")
    
    try:
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except KeyboardInterrupt:
        pygame.mixer.music.stop()
        print("\nReproducción detenida.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Uso: python play_song.py <hash_de_la_canción>")
        sys.exit(1)
    
    song_hash = sys.argv[1]
    file_path, metadata = download_song(song_hash)
    
    if file_path:
        print(f"Título: {metadata['title']}")
        print(f"Autor: {metadata['author']}")
        print(f"Género: {metadata['genre']}")
        print(f"Álbum: {metadata['album']}")
        play_music(file_path)
