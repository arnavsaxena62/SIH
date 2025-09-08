import rasterio

file = "./modis_downloads/MOD13Q1.A2023209.h24v06.061.2023226000418.hdf"
with rasterio.open(file) as src:
  print(src.subdataset)