import spotipy
import streamlit as st
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
import re
from urllib.parse import urlparse
import time

def fetch_spotify_credentials():
    """Retrieve Spotify API credentials from the environment variables."""
    load_dotenv()
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Missing Spotify API credentials. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.")
    return {"client_id": client_id, "client_secret": client_secret}

def validate_playlist_url(playlist_url: str) -> bool:
    parsed = urlparse(playlist_url)
    return all([parsed.scheme, parsed.netloc]) and "spotify.com" in parsed.netloc

@st.cache_data(show_spinner=False)
def get_playlist_albums(playlist_url, TIER_THRESHOLDS, max_albums=100):
    """Fetch and process playlist albums with improved error handling."""
    if not validate_playlist_url(playlist_url):
        st.warning("Invalid Spotify playlist URL.")
        return None

    try:
        credentials = fetch_spotify_credentials()
        auth_manager = SpotifyClientCredentials(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"]
        )
        sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=10)
        playlist_id = playlist_url.split('/')[-1].split('?')[0]
        
        if "?si" in playlist_id:
            playlist_id = playlist_id.split("?si")[0]
        
        # Verify playlist exists and is accessible
        try:
            sp.playlist(playlist_id, fields="id")
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 404:
                st.warning("Playlist not found")
            elif e.http_status == 403:
                st.warning("Playlist is private or inaccessible")
            return None

        # Fetch tracks with rate limiting protection
        tracks_data = []
        results = sp.playlist_tracks(playlist_id, 
                                   fields="items(track(album(name,images),popularity)),next", 
                                   limit=100)
        tracks_data.extend(results["items"])
        
        retry_count = 0
        while results["next"] and retry_count < 3:
            try:
                time.sleep(0.1)  # Rate limiting protection
                results = sp.next(results)
                tracks_data.extend(results["items"])
            except Exception as e:
                retry_count += 1
                if retry_count == 3:
                    break
                time.sleep(1)  # Wait longer between retries
        
        album_map = {}
        for item in tracks_data:
            if len(album_map) >= max_albums:
                break
            if item.get("track") and item["track"].get("album"):
                album_info = item["track"]["album"]
                album_name = album_info.get("name", "Unknown Album")
                album_popularity = item["track"].get("popularity", 0)
                
                if album_name not in album_map:
                    images = album_info.get("images", [])
                    image_url = images[0].get("url") if images else None
                    album_map[album_name] = {
                        "image_url": image_url,
                        "popularity_scores": []
                    }
                album_map[album_name]["popularity_scores"].append(album_popularity)
        
        if not album_map:
            st.warning("No valid albums found in playlist")
            return None

        for album_name, data in album_map.items():
            scores = data["popularity_scores"]
            avg_popularity = sum(scores) / len(scores)
            data["tier"] = next(
                (tier for tier, threshold in TIER_THRESHOLDS.items() 
                 if avg_popularity >= threshold),
                max(TIER_THRESHOLDS.keys())  # Default to lowest tier
            )
            data["avg_popularity"] = avg_popularity

        return album_map

    except ValueError as e:
        st.warning("Issue with Spotify API credentials")
        return None
    except spotipy.exceptions.SpotifyException as e:
        st.warning(f"Spotify API error: {str(e)}")
        return None
    except Exception as e:
        st.warning(f"Unexpected error in get_playlist_albums: {str(e)}")
        return None