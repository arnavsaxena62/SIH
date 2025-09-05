

from io import BytesIO
from PIL import Image
import mercantile
from dotenv import load_dotenv
import os
import requests

load_dotenv()


def download_and_stitch(api_key, proc, bbox, zoom=12, save_as="stitched.png",
                        layer="global_monthly_2020_01_mosaic",
                        tilematrixset="GoogleMapsCompatible_Level9"):
    """
    Download and stitch tiles for a bounding box from Planet Basemaps API.

    Parameters:
        api_key (str): Planet API key
        proc (str): "ndvi" or "ndwi"
        bbox (tuple): (min_lon, min_lat, max_lon, max_lat) in WGS84
        zoom (int): Zoom level (higher = more detail, larger image)
        save_as (str): File to save final stitched PNG
        layer (str): Mosaic layer ID from /mosaics
        tilematrixset (str): Tile matrix set (default: GoogleMapsCompatible_Level9)

    Returns:
        Image object (stitched PIL.Image)
    """
    min_lon, min_lat, max_lon, max_lat = bbox

    # Get all tiles that intersect the bbox at given zoom
    tiles = list(mercantile.tiles(min_lon, min_lat, max_lon, max_lat, zoom))

    # Find grid size
    xs = sorted(set(t.x for t in tiles))
    ys = sorted(set(t.y for t in tiles))
    width, height = len(xs), len(ys)

    print(f"Downloading {width} x {height} = {len(tiles)} tiles...")

    # Create blank canvas
    stitched = Image.new("RGB", (256 * width, 256 * height))

    for t in tiles:
        url = (
            f"https://api.planet.com/basemaps/v1/mosaics/wmts"
            f"?api_key={api_key}"
            f"&SERVICE=WMTS"
            f"&REQUEST=GetTile"
            f"&VERSION=1.0.0"
            f"&LAYER={layer}"
            f"&STYLE="
            f"&TILEMATRIXSET={tilematrixset}"
            f"&TILEMATRIX={zoom}"
            f"&TILEROW={t.y}"
            f"&TILECOL={t.x}"
            f"&FORMAT=image/png"
            f"&proc={proc}"
        )

        print(f"Fetching: {url}")

        r = requests.get(url)
        if r.status_code == 200:
            img = Image.open(BytesIO(r.content))

            # Paste into canvas
            x_idx = xs.index(t.x)
            y_idx = ys.index(t.y)
            stitched.paste(img, (x_idx * 256, y_idx * 256))
        else:
            print(f"❌ Failed to fetch tile {t}: {r.status_code} {r.text}")

    stitched.save(save_as)
    print(f"✅ Saved stitched image as {save_as}")
    return stitched


api_key = os.getenv("API_KEY")
user_id = os.getenv("USER_ID")
bbox = (77.0, 28.5, 77.2, 28.7)  # (min_lon, min_lat, max_lon, max_lat)
download_and_stitch(api_key, "ndvi", bbox, zoom=12,
                    save_as="ndvi_stitched.png")
