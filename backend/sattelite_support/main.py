import math
import requests
from pathlib import Path
import datetime
import rasterio
import rasterio.mask
from shapely.geometry import box, mapping
import dotenv
import os


# -------------------------------
# Helpers
# -------------------------------

def latlon_to_modis_tile(lat, lon):
    """
    Convert lat/lon to MODIS Sinusoidal tile (h, v).
    MODIS grid: 36 tiles wide (h00-h35), 18 tall (v00-v17).
    """
    R = 6371007.181
    T = 1111950
    xmin, ymax = -20015109, 10007555

    x = math.radians(lon) * R
    y = math.log(math.tan((90 + lat) * math.pi / 360)) * R
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


def date_to_doy(date_str):
    """Convert YYYY-MM-DD to DOY string (001-366)."""
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.timetuple().tm_yday:03d}"


# -------------------------------
# MODIS Downloader
# -------------------------------

def download_modis_ndvi(token, h, v, date, save_dir="modis_tiles"):
    """
    Download MODIS NDVI HDF file for given tile (h,v) and date.
    """
    Path(save_dir).mkdir(exist_ok=True)
    product = "MOD13Q1.061"
    year = date.split("-")[0]
    doy = date_to_doy(date)

    filename = f"MOD13Q1.A{year}{doy}.h{h:02d}v{v:02d}.061.hdf"
    url = f"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/{product}/{year}/{doy}/{filename}"

    out_path = Path(save_dir) / filename
    if not out_path.exists():
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(url, headers=headers, stream=True)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)
            print(f"Downloaded {filename}")
        else:
            raise RuntimeError(f"Failed to download {filename}: {r.status_code}\n{r.text[:200]}")
    return out_path


# -------------------------------
# Extract NDVI from HDF
# -------------------------------

def extract_ndvi_subdataset(hdf_path, out_tif="ndvi.tif"):
    pass


# -------------------------------
# Crop to BBOX
# -------------------------------

def crop_to_bbox(raster_path, bbox, save_as="cropped_ndvi.tif"):
    """
    Crop a raster (GeoTIFF) to bounding box (lon/lat).
    """
    geom = box(*bbox)  # (min_lon, min_lat, max_lon, max_lat)
    with rasterio.open(raster_path) as src:
        out_image, out_transform = rasterio.mask.mask(src, [mapping(geom)], crop=True)
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


# -------------------------------
# Example Usage
# -------------------------------

if __name__ == "__main__":
    bbox = (77, 28, 78, 29)

    dotenv.load_dotenv(".env")
    token = os.getenv("TOKEN")
    
    tiles = bbox_to_tiles(*bbox)
    print("Tiles needed:", tiles)

    for (h, v) in tiles:
        hdf_path = download_modis_ndvi(token, h, v, date="2023-08-01")
        ndvi_tif = extract_ndvi_subdataset(hdf_path, out_tif=f"ndvi_h{h:02d}v{v:02d}.tif")
        # cropped = crop_to_bbox(ndvi_tif, bbox, save_as=f"ndvi_cropped_h{h:02d}v{v:02d}.tif")
