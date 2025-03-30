import random
import requests

# This is a script to create a random queue in lyrion which plays from
# each album in the queue 4 songs before moving to the next album and
# so on, until no songs are left. My use case for this is when
# checking out new music. For this I want a compromise between
# randomization and coherence: I don't want to listen each album fully
# (I am in discovery mode and like to jump between releases), but I
# still want to spend sufficient time with one artist/album to emerge
# into the sound and athmosphere of the release. A chunk size of 4 is
# for me the sweet spot for this. The script additional provides an
# album shuffle, since the lyrion album shuffle doesn't work for me.

# Configuration
LYRION_API_BASE_URL = "http://192.168.178.160:9000/jsonrpc.js"
PLAYER_ID = "b8:27:eb:ec:5d:62"  # Adjust as necessary
CHUNK_SIZE = 4  # Number of songs per album in a row

def send_request(params):
    """Send a JSON-RPC request to the Lyrion server."""
    payload = {"id": 1, "method": "slim.request", "params": params}
    response = requests.post(LYRION_API_BASE_URL, json=payload)
    if response.status_code == 200:
        return response.json().get("result", {})
    else:
        raise Exception("Failed to communicate with Lyrion API.")

def get_playlist_length():
    """Fetch the number of tracks in the current playlist."""
    result = send_request([PLAYER_ID, ["playlist", "tracks", "?"]])
    return int(result.get("_tracks", 0))

def get_album_by_index(index):
    """Fetch the album name of a track at a given index."""
    result = send_request([PLAYER_ID, ["playlist", "album", str(index), "?"]])
    return result.get("_album", "Unknown Album")

def extract_albums():
    """Extract albums from the current playlist and store them in a dictionary."""
    num_tracks = get_playlist_length()
    albums = {}
    for index in range(0, num_tracks):
        album = get_album_by_index(index)
        if album not in albums:
            albums[album] = []
        albums[album].append(index)
    return albums

def shuffle_albums(albums):
    """Shuffle the albums in the current queue by moving songs dynamically."""
    album_list = list(albums.keys())
    current_index = 0
    random.shuffle(album_list)
    for album in album_list:
        if albums[album]:
            chunk = albums[album]
            for i, track_index in enumerate(chunk):
                move_track(track_index, current_index+i)
            current_index += len(chunk)
            albums[album] = albums[album][len(chunk):]
            shift_albums(albums, chunk)    

def reorder_queue(albums, chunk_size):
    """Reorder the songs in the queue by moving them dynamically."""
    album_list = list(albums.keys())
    current_index = 0
    
    while any(albums.values()):
        random.shuffle(album_list)
        for album in album_list:
            if albums[album]:
                chunk = albums[album][:chunk_size]
                for i, track_index in enumerate(chunk):
                    move_track(track_index, current_index+i)
                current_index += len(chunk)
                albums[album] = albums[album][len(chunk):]
                shift_albums(albums, chunk)

def shift_albums(albums, chunk):
    """Shift indeces in the album dictionary."""
    for index in chunk:
        for album in albums:
            albums[album] = [
                track + 1 if track < index else track
                for track in albums[album]]
                
def move_track(from_index, to_index):
    """Move a track in the playlist from one position to another."""
    send_request([PLAYER_ID, ["playlist", "move", str(from_index), str(to_index)]])

def ls_queue(be,en):
    """List songs in the queue."""
    for index in range(be, en):
        a = send_request([PLAYER_ID, ["playlist", "artist", str(index), "?"]]).get("_artist", "unknown")
        b = send_request([PLAYER_ID, ["playlist", "title", str(index), "?"]]).get("_title", "unknown")
        print("index ", index, " artist ", a, " title ", b)

        
def main():
    choice = input("Do you want to reorder the queue (R) or shuffle albums (S)? ").strip().lower()
    
    if choice == "r":
        chunk_size_input = input(f"Enter chunk size (default {CHUNK_SIZE}): ").strip()
        chunk_size = int(chunk_size_input) if chunk_size_input.isdigit() else CHUNK_SIZE
        albums = extract_albums()
        reorder_queue(albums, chunk_size)
        print("Queue reordered successfully!")
    elif choice == "s":
        albums = extract_albums()
        shuffle_albums(albums)
        print("Albums shuffled successfully!")
    else:
        print("Invalid choice. Exiting.")
        
if __name__ == "__main__":
    main()
