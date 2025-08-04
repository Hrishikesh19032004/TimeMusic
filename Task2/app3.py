import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

query = "Kabir Singh"
folder = f"{query.replace(' ', '_')}_Data"

df_tracks = pd.read_csv(os.path.join(folder, f"{query}_tracks.csv"))
df_albums = pd.read_csv(os.path.join(folder, f"{query}_albums.csv"))
df_playlists = pd.read_csv(os.path.join(folder, f"{query}_playlists.csv"))

#  Most frequent artist names
all_artists = df_tracks['Artist(s)'].dropna().str.split(', ').explode()
top_artists = all_artists.value_counts().head(5)

plt.figure(figsize=(8, 5))
sns.barplot(x=top_artists.values, y=top_artists.index, palette="viridis")
plt.title("Top 5 Most Frequent Artists")
plt.xlabel("Count")
plt.ylabel("Artist")
plt.tight_layout()
plt.show()

# Year-wise releases
year_counts = df_tracks['Release Year'].value_counts().sort_index()

plt.figure(figsize=(8, 4))
sns.lineplot(x=year_counts.index, y=year_counts.values, marker="o", color="teal")
plt.title("Track Count by Release Year")
plt.xlabel("Year")
plt.ylabel("Number of Tracks")
plt.tight_layout()
plt.show()

# Track duration range
bins = [0, 120, 180, 240, 300, 600]
labels = ['<2min', '2-3min', '3-4min', '4-5min', '5min+']
df_tracks['Duration Range'] = pd.cut(df_tracks['Duration (sec)'], bins=bins, labels=labels, right=False)
duration_counts = df_tracks['Duration Range'].value_counts().sort_index()

plt.figure(figsize=(8, 4))
sns.barplot(x=duration_counts.index, y=duration_counts.values, palette="mako")
plt.title("Track Duration Ranges")
plt.xlabel("Duration Range")
plt.ylabel("Number of Tracks")
plt.tight_layout()
plt.show()

# Popular albums
top_albums = df_albums[['Album Name', 'Total Tracks']].sort_values(by='Total Tracks', ascending=False).head(5)

plt.figure(figsize=(8, 4))
sns.barplot(x='Total Tracks', y='Album Name', data=top_albums, palette="flare")
plt.title("Top 5 Albums by Total Tracks")
plt.xlabel("Track Count")
plt.ylabel("Album")
plt.tight_layout()
plt.show()

#  Popular playlists
top_playlists = df_playlists[['Playlist Name', 'Total Tracks']].sort_values(by='Total Tracks', ascending=False).head(5)

plt.figure(figsize=(8, 4))
sns.barplot(x='Total Tracks', y='Playlist Name', data=top_playlists, palette="crest")
plt.title("Top 5 Playlists by Total Tracks")
plt.xlabel("Track Count")
plt.ylabel("Playlist")
plt.tight_layout()
plt.show()
