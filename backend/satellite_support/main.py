import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load Earthdata credentials from .env file

def downloadhdfs():

    load_dotenv()
    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")

    # Parameters
    PRODUCT = "MOD13Q1"
    VERSION = "061"
    START_DATE = "2023-08-01T00:00:00Z"
    END_DATE = "2023-08-02T23:59:59Z"
    BBOX = "77,28,78,29"   # min_lon,min_lat,max_lon,max_lat (Delhi area)
    SAVE_DIR = Path("modis_downloads")
    SAVE_DIR.mkdir(exist_ok=True)

    # Step 1: Query CMR API
    search_url = (
        f"https://cmr.earthdata.nasa.gov/search/granules.json?"
        f"short_name={PRODUCT}&version={VERSION}"
        f"&temporal={START_DATE},{END_DATE}"
        f"&bounding_box={BBOX}&page_size=2000"
    )

    print("Querying CMR...")
    resp = requests.get(search_url)
    resp.raise_for_status()
    data = resp.json()

    # Step 2: Extract download URLs
    download_links = []
    for item in data.get("feed", {}).get("entry", []):
        for link in item.get("links", []):
            href = link.get("href", "")
            if href.startswith("https://") and href.endswith(".hdf"):
                download_links.append(href)

    print(f"Found {len(download_links)} HTTPS files")

    TOKEN = os.getenv("TOKEN")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {TOKEN}"})

    for url in download_links:
        filename = url.split("/")[-1]
        out_path = SAVE_DIR / filename

        if out_path.exists():
            print(f"Already downloaded: {filename}")
            continue

        print(f"Downloading {filename}...")
        r = session.get(url, stream=True)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Saved: {out_path}")
        else:
            print(f"Failed {filename}: {r.status_code} -> {r.text[:200]}")

import numpy as np
from pyhdf.SD import SD, SDC
from pyproj import CRS, Transformer

def average_ndvi(hdf_path, bbox):
    """
    Compute average NDVI for a bounding box from MOD13Q1 HDF file.
    
    Parameters
    ----------
    hdf_path : str
        Path to MOD13Q1 .hdf file
    bbox : tuple
        (min_lon, min_lat, max_lon, max_lat)
    """
    # Open HDF file
    hdf = SD(hdf_path, SDC.READ)

    # NDVI dataset
    ndvi_ds = hdf.select("250m_16_days_NDVI")
    ndvi = ndvi_ds[:].astype(float)

    # Attributes
    attrs = ndvi_ds.attributes(full=1)
    scale = attrs["scale_factor"][0]
    offset = attrs["add_offset"][0]
    fill = attrs["_FillValue"][0]

    # Apply scaling and mask fill
    ndvi = np.where(ndvi == fill, np.nan, ndvi)
    ndvi = ndvi * scale + offset

    # --- Build coordinate grid ---
    # MODIS sinusoidal CRS
    sinusoidal = CRS.from_proj4(
        "+proj=sinu +R=6371007.181 +nadgrids=@null +wktext"
    )
    wgs84 = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(sinusoidal, wgs84, always_xy=True)

    # Tile size and resolution
    n = ndvi.shape[0]  # 4800
    res = 231.656358  # meters per pixel at 250m resolution
    xmin, ymax = -20015109, 10007555  # MODIS global bounds in sinusoidal

    # Extract tile indices from filename (h??v??)
    import re
    m = re.search(r"h(\d{2})v(\d{2})", hdf_path)
    h, v = int(m.group(1)), int(m.group(2))

    # Tile upper-left corner in sinusoidal coords
    tile_xmin = xmin + h * (4800 * res)
    tile_ymax = ymax - v * (4800 * res)

    # Pixel centers
    x = tile_xmin + (np.arange(n) + 0.5) * res
    y = tile_ymax - (np.arange(n) + 0.5) * res
    xx, yy = np.meshgrid(x, y)

    # Convert to lat/lon
    lon, lat = transformer.transform(xx, yy)

    # Mask by bbox
    min_lon, min_lat, max_lon, max_lat = bbox
    mask = (
        (lon >= min_lon) & (lon <= max_lon) &
        (lat >= min_lat) & (lat <= max_lat)
    )

    # Compute average
    avg = np.nanmean(ndvi[mask])
    return avg


hdf_file = "modis_downloads/MOD13Q1.A2023217.h24v06.061.hdf"
bbox = (77, 28, 78, 29)  # Delhi region
avg = average_ndvi(hdf_file, bbox)
print("Average NDVI:", avg)
