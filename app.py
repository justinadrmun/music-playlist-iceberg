import streamlit as st
import pandas as pd
from spotify_client import get_playlist_albums
from visualizer import create_iceberg_visual

TIER_THRESHOLDS: dict = {
    1: 60,
    2: 50,
    3: 40,
    4: 30,
    5: 20,
    6: 10,
    7: 5,
    8: 1
}

def main():
    st.title("Playlist Iceberg Visualiser")
    url = "https://developer.spotify.com/documentation/web-api/reference/get-several-tracks#:~:text=of%20the%20track.-,popularity,-integer"
    st.write("Enter a Spotify playlist URL to see an iceberg visualisation of [album popularity](%s)." % url)
    tier_frame = pd.DataFrame({"threshold": list(TIER_THRESHOLDS.values())}).T
    tier_frame.columns = [f"Tier {i}" for i in range(1, len(tier_frame.columns) + 1)]

    with st.expander("Tier threshold definition (optional)", expanded=False):
        st.caption("""
        Edit the lower limit threshold values for each tier. 
        Album popularity is a score between 0 and 100.
        """
        )
        tier_frame = st.data_editor(tier_frame, hide_index=True)
        for tier, threshold in zip(tier_frame.columns, tier_frame.iloc[0]):
            TIER_THRESHOLDS[int(tier.replace("Tier ", ""))] = threshold
        st.caption("""
            _We recommend using a threshold of 1 for the last tier as some albums may return 
            an unexpected popularity score of 0. Also, it is worth noting that tiers are capped at **11 albums** each._
            """
        )

    st.session_state["warning_msg"] = None
    playlist_url = st.text_input("Playlist URL:")

    if st.button("Submit", key="submit_button"):
        if not all(isinstance(value, int) for value in TIER_THRESHOLDS.values()):
            st.warning("Tier thresholds must contain integer values.")
            return

        if not all(0 <= value <= 100 for value in TIER_THRESHOLDS.values()):
            st.warning("Tier thresholds must be a value between 0 and 100.")
            return

        if not all(TIER_THRESHOLDS[idx+1] > TIER_THRESHOLDS[idx + 2] for idx in range(len(TIER_THRESHOLDS) - 2)):
            st.warning("Tier thresholds must be in descending order.")
            return

        if not playlist_url:
            st.warning("Please provide a Spotify playlist URL.")
            return

        with st.spinner(f"Fetching album data..."):
            albums_data = get_playlist_albums(playlist_url, TIER_THRESHOLDS)

            if albums_data is not None:
                albums_frame = pd.DataFrame(albums_data).T.sort_values("popularity", ascending=False)

                # filter out albums below the lower limit, only for iceberg
                lower_limit = TIER_THRESHOLDS[max(TIER_THRESHOLDS.keys())]
                albums_data = {album: data for album, data in albums_data.items() if data["popularity"] >= lower_limit}

                if len(albums_data) >= 100:
                    st.warning("""
                    Your playlist has more than 100 unique albums. 
                    Only the first 100 albums are visualised.
                    """
                    )
                st.write("")
                st.session_state["iceberg_image"] = create_iceberg_visual(albums_data)
                tab1, tab2 = st.tabs(["Iceberg", "Data"])
                tab1.image(st.session_state["iceberg_image"], caption="Save iceberg image with right-click")
                tab2.dataframe(albums_frame.drop(columns=["image_url"]), 
                    use_container_width=True, 
                    height=int(35.2*(len(albums_frame)+1)) 
                )
            else:
                if st.session_state["warning_msg"] is None:
                    st.warning("Issue fetching album data. Please check the playlist URL or try again later.")
                else:
                    st.warning(st.session_state["warning_msg"])

if __name__ == "__main__":
    main()
