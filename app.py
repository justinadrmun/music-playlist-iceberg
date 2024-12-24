import streamlit as st
from spotify_client import get_playlist_albums
from visualizer import create_iceberg_visual

def main():
    st.title("Spotify Iceberg Visualiser")
    st.write("Enter a Spotify playlist URL to see an iceberg visualisation of album popularity.")
    st.caption("_Note: Tiers are capped at 11 items each._")

    playlist_url = st.text_input("Playlist URL:")

    if st.button("Submit", key="submit_button"):
        with st.spinner(f"Fetching album data..."):
            albums_data = get_playlist_albums(playlist_url)
            if albums_data is not None:
                st.write("")
                st.session_state["iceberg_image"] = create_iceberg_visual(albums_data)
                st.image(st.session_state["iceberg_image"], caption="Album Popularity Iceberg")
            else:
                st.warning("Issue fetching album data. Please check the playlist URL or try again later.")

if __name__ == "__main__":
    main()
