from osgeo import gdal
import os
import re
import requests
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from pyproj import CRS, Transformer
import pprint

def downloadhdfs():
    load_dotenv()
    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")

    PRODUCT = "MOD13Q1"
    VERSION = "061"
    START_DATE = "2023-08-01T00:00:00Z"
    END_DATE = "2023-08-02T23:59:59Z"
    BBOX = "77,28,78,29"
    SAVE_DIR = Path("modis_downloads")
    SAVE_DIR.mkdir(exist_ok=True)

    search_url = (
        f"https://cmr.earthdata.nasa.gov/search/granules.json?"
        f"short_name={PRODUCT}&version={VERSION}"
        f"&temporal={START_DATE},{END_DATE}"
        f"&bounding_box={BBOX}&page_size=2000"
    )

    resp = requests.get(search_url)
    resp.raise_for_status()
    data = resp.json()

    download_links = []
    for item in data.get("feed", {}).get("entry", []):
        for link in item.get("links", []):
            href = link.get("href", "")
            if href.startswith("https://") and href.endswith(".hdf"):
                download_links.append(href)

    TOKEN = os.getenv("TOKEN")
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {TOKEN}"})

    for url in download_links:
        filename = url.split("/")[-1]
        out_path = SAVE_DIR / filename

        if out_path.exists():
            continue

        r = session.get(url, stream=True)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)


from osgeo import gdal
import numpy as np
from pyproj import CRS, Transformer

def average_ndvi(hdf_path, bbox):
    hdf = gdal.Open(hdf_path, gdal.GA_ReadOnly)
    subdatasets = hdf.GetSubDatasets()
    ndvi_path = None
    for sds_name, sds_desc in subdatasets:
        if "250m 16 days NDVI" in sds_desc:
            ndvi_path = sds_name
            break
    if ndvi_path is None:
        raise RuntimeError("NDVI subdataset not found in HDF")
    ndvi_ds = gdal.Open(ndvi_path, gdal.GA_ReadOnly)
    ndvi = ndvi_ds.ReadAsArray().astype(float)
    fill = ndvi_ds.GetRasterBand(1).GetNoDataValue()
    ndvi = np.where(ndvi == fill, np.nan, ndvi)
    ndvi *= 0.0001
    gt = ndvi_ds.GetGeoTransform()
    proj = ndvi_ds.GetProjection()
    src_crs = CRS.from_wkt(proj)
    dst_crs = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    nrows, ncols = ndvi.shape
    x = np.arange(ncols) * gt[1] + gt[0] + gt[1] / 2
    y = np.arange(nrows) * gt[5] + gt[3] + gt[5] / 2
    xx, yy = np.meshgrid(x, y)
    lon, lat = transformer.transform(xx, yy)
    min_lon, min_lat, max_lon, max_lat = bbox
    mask = (lon >= min_lon) & (lon <= max_lon) & (lat >= min_lat) & (lat <= max_lat)
    return np.nanmean(ndvi[mask])

def main():
    hdf_file = "./modis_downloads/MOD13Q1.A2023209.h24v06.061.2023226000418.hdf"
    bbox = (77, 28, 78, 29)
    avg = average_ndvi(hdf_file, bbox)
    print("Average NDVI:", avg)

