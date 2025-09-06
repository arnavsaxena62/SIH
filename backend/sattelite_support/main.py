import math
import requests
import rasterio
import rasterio.merge
import rasterio.mask
from shapely.geometry import box, mapping
from pathlib import Path
from rasterio.plot import show
import matplotlib.pyplot as plt
import dotenv
import os


def latlon_to_modis_tile(lat, lon):
    """
    Convert lat/lon to MODIS Sinusoidal tile (h, v).
    MODIS grid: 36 tiles wide (h00-h35), 18 tall (v00-v17).
    """
    R = 6371007.181  
    T = 1111950     
    xmin, ymax = -20015109, 10007555  

    x = math.radians(lon) * R
    y = math.log(math.tan((90 + lat) * math.pi / 360)) * R  # approx proj
    h = int((x - xmin) // T)
    v = int((ymax - y) // T)
    return h, v


def bbox_to_tiles(min_lon, min_lat, max_lon, max_lat):
    """Return list of MODIS tile IDs (h,v) that intersect a bbox."""
    corners = [
        (min_lat, min_lon), (min_lat, max_lon),
        (max_lat, min_lon), (max_lat, max_lon)
    ]
    tiles = set(latlon_to_modis_tile(lat, lon) for lat, lon in corners)
    return tiles


def download_modis_ndvi(username, password, h, v, date, save_dir="modis_tiles"):
    """
    Download a MODIS NDVI HDF file for given tile (h,v).
    """
    Path(save_dir).mkdir(exist_ok=True)
    product = "MOD13Q1.061"
    year, doy = date.split("-")[0], "001"  # TODO: map to DOY properly

    # Example file path (hardcoded, real query requires NASA CMR search API)
    filename = f"MOD13Q1.A{year}{doy}.h{h:02d}v{v:02d}.061.hdf"
    url = f"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/{product}/{year}/{doy}/{filename}"

    out_path = Path(save_dir) / filename
    if not out_path.exists():
        r = requests.get(url, auth=(username, password))
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(r.content)
            print(f"Downloaded {filename}")
        else:
            print(f"Failed: {r.status_code}")
    return out_path


def crop_to_bbox(raster_path, bbox, save_as="cropped_ndvi.tif"):
    """
    Crop a raster to bounding box (lon/lat).
    """
    geom = box(*bbox)  # (min_lon, min_lat, max_lon, max_lat)
    with rasterio.open(raster_path) as src:
        out_image, out_transform = rasterio.mask.mask(
            src, [mapping(geom)], crop=True)
        out_meta = src.meta.copy()
        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })
    with rasterio.open(save_as, "w", **out_meta) as dest:
        dest.write(out_image)
    print(f"Cropped image saved as {save_as}")
    return save_as


# --- Example Usage ---
if __name__ == "__main__":
    bbox = (77, 28, 78, 29)  # Delhi area
    tiles = bbox_to_tiles(*bbox)
    print("Tiles needed:", tiles)

    username, password = "somethingsaxena", "Somethingsaxena@667"
    for (h, v) in tiles:
        path = download_modis_ndvi(
            username, password, h, v, date="2023-08-01")
