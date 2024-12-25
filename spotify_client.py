import spotipy
import streamlit as st
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

TIER_THRESHOLDS: dict = {
    1: 100,
    2: 50,
    3: 40,
    4: 30,
    5: 20,
    6: 10,
    7: 5,
    8: 0
}

def fetch_spotify_credentials():
    """Retrieve Spotify API credentials from the environment variables."""
    load_dotenv()
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Missing Spotify API credentials. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.")
    return client_id, client_secret

@st.cache_data(show_spinner=False)
def get_playlist_albums(playlist_url):
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=fetch_spotify_credentials()[0],
            client_secret=fetch_spotify_credentials()[1]
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        playlist_id = playlist_url.split('/')[-1].split('?')[0]
        
        if "?si" in playlist_id:
            playlist_id = playlist_id.split("?")[0]
        
        # Fetch all tracks in the playlist
        tracks_data = []
        results = sp.playlist_tracks(playlist_id, 
                                     fields="items(track(album(name,images),popularity)),next", 
                                     limit=100)
        tracks_data.extend(results["items"])
        while results["next"]:
            results = sp.next(results)
            tracks_data.extend(results["items"])
        
        album_map = {}
        for item in tracks_data:
            if item["track"]:
                album_info = item["track"]["album"]
                album_name = album_info["name"]
                album_popularity = item["track"]["popularity"]
                if album_name not in album_map:
                    album_map[album_name] = {
                        "image_url": album_info["images"][0]["url"] if album_info["images"] else None,
                        "popularity_scores": []
                    }
                album_map[album_name]["popularity_scores"].append(album_popularity)
        
        for album_name, data in album_map.items():
            avg_popularity = sum(data["popularity_scores"]) / len(data["popularity_scores"])
            data["tier"] = next(
                tier for tier, threshold in TIER_THRESHOLDS.items() if avg_popularity >= threshold
            )
            data["avg_popularity"] = avg_popularity  # Add average popularity
        return album_map
    except Exception:
        return None