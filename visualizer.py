from PIL import Image, ImageDraw
import requests
from io import BytesIO
import streamlit as st
import logging
import os

@st.cache_data(show_spinner=False)
def create_iceberg_visual(albums_data):
    try:
        if not os.path.exists("iceberg_base.png"):
            logging.error("Base iceberg image not found.")
            return None
        base_img = Image.open("iceberg_base.png").convert("RGBA")
    except Exception as e:
        logging.error(f"Error opening base image: {e}")
        return None

    draw = ImageDraw.Draw(base_img)
    tier_positions = {
        1: (30, 50),
        2: (30, 300),
        3: (30, 600),
        4: (30, 900),
        5: (30, 1200),
        6: (30, 1460),
        7: (30, 1730),
        8: (30, 2000)
    }
    x_offset_increment = 250
    standard_size = (200, 200)
    half_size = (100, 100)
    
    # Group albums by tier
    tiers = {}
    for _, data in albums_data.items():
        tier = data["tier"]
        tiers.setdefault(tier, []).append(data)
    
    # Sort albums within each tier by popularity descending
    for tier in tiers:
        tiers[tier].sort(key=lambda x: x["popularity"], reverse=True)
    
    for tier, albums in tiers.items():
        pos_x, pos_y = tier_positions[tier]
        for index, data in enumerate(albums):
            if index < 11:
                if data["image_url"]:
                    try:
                        response = requests.get(data["image_url"], timeout=5)
                        response.raise_for_status()
                        with Image.open(BytesIO(response.content)) as album_img:
                            resize_cond = (len(albums) <= 5 or index < 3)
                            resized_img = album_img.resize(standard_size if resize_cond else half_size)
                            if len(albums) > 5:
                                if index < 3:
                                    base_img.paste(resized_img, (pos_x, pos_y), resized_img.convert("RGBA"))
                                    pos_x += x_offset_increment
                                elif 3 <= index < 7:
                                    row, col = divmod(index - 3, 2)
                                    new_x, new_y = pos_x + col * (half_size[0] + 10), pos_y + row * (half_size[1] + 10)
                                    base_img.paste(resized_img, (new_x, new_y), resized_img.convert("RGBA"))
                                elif 7 <= index < 11:
                                    row, col = divmod(index - 7, 2)
                                    new_x, new_y = pos_x + col * (half_size[0] + 10) + 250, pos_y + row * (half_size[1] + 10)
                                    base_img.paste(resized_img, (new_x, new_y), resized_img.convert("RGBA"))
                            else:
                                base_img.paste(resized_img, (pos_x, pos_y), resized_img.convert("RGBA"))
                                pos_x += x_offset_increment
                    except Exception as e:
                        logging.error(f"Error fetching or opening album image: {e}")
                        st.warning(f"Error fetching or opening album image. Skipping album: {data['album_name']}")
                        continue
    return base_img