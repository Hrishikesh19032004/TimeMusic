import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import os

CLIENT_ID = "b466dac2e7ea450e8505d0caef51e38f"
CLIENT_SECRET = "7bb56e9bedb7411d8da87ae8a1c26d46"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

query = "Kabir Singh"
folder_name = f"{query.replace(' ', '_')}_Data"
os.makedirs(folder_name, exist_ok=True)

limit = 50

results_tracks = sp.search(q=query, type='track', limit=limit)
results_albums = sp.search(q=query, type='album', limit=limit)
results_artists = sp.search(q=query, type='artist', limit=limit)
results_playlists = sp.search(q=query, type='playlist', limit=limit)

track_data = []
for item in results_tracks.get('tracks', {}).get('items', []):
    track_data.append({
        'Track Name': item.get('name', ''),
        'Artist(s)': ", ".join([artist.get('name', '') for artist in item.get('artists', [])]),
        'Album': item.get('album', {}).get('name', ''),
        'Release Year': item.get('album', {}).get('release_date', '')[:4],
        'Duration (sec)': round(item.get('duration_ms', 0) / 1000)
    })
df_tracks = pd.DataFrame(track_data)
df_tracks.to_csv(os.path.join(folder_name, f"{query}_tracks.csv"), index=False)

album_data = []
for item in results_albums.get('albums', {}).get('items', []):
    album_data.append({
        'Album Name': item.get('name', ''),
        'Artist(s)': ", ".join([artist.get('name', '') for artist in item.get('artists', [])]),
        'Release Year': item.get('release_date', '')[:4],
        'Total Tracks': item.get('total_tracks', 0)
    })
df_albums = pd.DataFrame(album_data)
df_albums.to_csv(os.path.join(folder_name, f"{query}_albums.csv"), index=False)

artist_data = []
for item in results_artists.get('artists', {}).get('items', []):
    artist_data.append({
        'Artist Name': item.get('name', ''),
        'Genres': ", ".join(item.get('genres', [])),
        'Followers': item.get('followers', {}).get('total', 0),
        'Popularity': item.get('popularity', 0)
    })
df_artists = pd.DataFrame(artist_data)
df_artists.to_csv(os.path.join(folder_name, f"{query}_artists.csv"), index=False)

playlist_data = []
for item in results_playlists.get('playlists', {}).get('items', []):
    if item:
        playlist_data.append({
            'Playlist Name': item.get('name', ''),
            'Owner': item.get('owner', {}).get('display_name', ''),
            'Total Tracks': item.get('tracks', {}).get('total', 0),
            'Description': item.get('description', '')
        })
df_playlists = pd.DataFrame(playlist_data)
df_playlists.to_csv(os.path.join(folder_name, f"{query}_playlists.csv"), index=False)

print(f"All CSVs saved in folder: {folder_name}")
