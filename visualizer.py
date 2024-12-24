from PIL import Image, ImageDraw
import requests
from io import BytesIO
import streamlit as st

@st.cache_data(show_spinner=False)
def create_iceberg_visual(albums_data):
    base_img = Image.open("iceberg_base.png").convert("RGBA")
    draw = ImageDraw.Draw(base_img)
    tier_positions = {
        1: (30, 50),
        2: (30, 300),
        3: (30, 600),
        4: (30, 900),
        5: (30, 1200),
        6: (30, 1450),
        7: (30, 1750),
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
    
    # Sort albums within each tier by avg_popularity descending
    for tier in tiers:
        tiers[tier].sort(key=lambda x: x["avg_popularity"], reverse=True)
    
    for tier, albums in tiers.items():
        pos_x, pos_y = tier_positions[tier]
        for index, data in enumerate(albums):
            if index < 11:
                if data["image_url"]:
                    response = requests.get(data["image_url"])
                    album_img = Image.open(BytesIO(response.content))
                    
                    if len(albums) > 5:
                        if index < 3:
                            resized_img = album_img.resize(standard_size)
                            base_img.paste(resized_img, (pos_x, pos_y), resized_img.convert("RGBA"))
                            pos_x += x_offset_increment
                        elif 3 <= index < 7:
                            row = (index - 3) // 2
                            col = (index - 3) % 2
                            resized_img = album_img.resize(half_size)
                            new_x = pos_x + col * (half_size[0] + 10)
                            new_y = pos_y + row * (half_size[1] + 10)
                            base_img.paste(resized_img, (new_x, new_y), resized_img.convert("RGBA"))
                        elif 7 <= index < 11:
                            row = (index - 7) // 2
                            col = (index - 7) % 2
                            resized_img = album_img.resize(half_size)
                            new_x = pos_x + col * (half_size[0] + 10) + 250
                            new_y = pos_y + row * (half_size[1] + 10)
                            base_img.paste(resized_img, (new_x, new_y), resized_img.convert("RGBA"))
                    else:
                        resized_img = album_img.resize(standard_size)
                        base_img.paste(resized_img, (pos_x, pos_y), resized_img.convert("RGBA"))
                        pos_x += x_offset_increment   
    return base_img