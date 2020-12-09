import pandas as pd
import rasterio
import scipy
import numpy as np
from scipy import ndimage
import glob

# file set up

from lab5functions import slopeAspect, reclassAspect, reclassByHisto

dem = rasterio.open(r"C:\Users\catan\Desktop\GEOG5092\lab5\data\data\bigElk_dem.tif")
dem_read = dem.read(1)
slope, aspect = slopeAspect(dem_read, 30)

dem_aspect = reclassAspect(aspect)
dem_slope = reclassByHisto(slope, 10)

landsat_path = glob.glob(r"C:\Users\catan\Desktop\GEOG5092\lab5\data\data\L5_big_elk\*.tif")

with rasterio.open(r"C:\Users\catan\Desktop\GEOG5092\lab5\data\data\fire_perimeter.tif") as fire_file:
    fire_perimeter = fire_file.read()

# part 1

band3 = []
band4 = []
NDVIarr = []
final_printlist = []
flat_rr = []
year = []


for image in landsat_path:
    if 'B3.tif' in image:
        band3.append(image)
    if 'B4.tif' in image:
        band4.append(image)
        
healthy_area = np.where(fire_perimeter == 2)
burned_area = np.where(fire_perimeter == 1)
    
for b3, b4 in zip(band3, band4):
    year.append(b3[-11:-7])
    with rasterio.open(b3, 'r') as data:
        band3_arr = data.read()
    with rasterio.open(b4, 'r') as beta:
        band4_arr = beta.read()
    NDVI = (band4_arr - band3_arr) / (band4_arr + band3_arr)
    healthy_area = np.where(fire_perimeter == 2)
    burned_area = np.where(fire_perimeter == 1)
    ndviMean = NDVI[healthy_area].mean()
    rr = NDVI / ndviMean
    burnt_mean = rr[burned_area].mean()
    final_printlist.append(burnt_mean)
    
    flat = rr.flatten()
    flat_rr.append(flat)
    
stacked = np.vstack(flat_rr)
coeff_recov = np.polyfit(range(10), stacked, 1)[0]
final_recov = coeff_recov.reshape(280,459)
mean_coef = np.where(fire_perimeter == 1, final_recov, np.nan)
rrMean_coeff = np.nanmean(mean_coef)

for yr,rat in zip(year,final_printlist):
    print("In ", yr, "the mean recovery ratio was", rat)
print("The mean coefficient of recovery is", rrMean_coeff)

# zonal statistics function

def zonal_stats_table(zone_raster, value_raster, csv_output):
          
    min_list = []
    max_list = []
    mean_list = []
    std_list = []
    count_list = []
    zone = []
    
    for u in np.unique(zone_raster):
        ras = np.where(zone_raster == u, u, np.nan)
        min_list.append(np.nanmin(ras * value_raster))
        max_list.append(np.nanmax(ras * value_raster))
        mean_list.append(np.nanmean(ras * value_raster))
        std_list.append(np.nanstd(ras * value_raster))
        count_list.append(np.where(zone_raster == u, 1, 0).sum())
        zone.append(int(u))
    
    stats = {'zone': zone, 'min': min_list, 'max': max_list, 'mean': mean_list,
             'std': std_list, 'count': count_list}
    df = pd.DataFrame(stats)
    df.to_csv(csv_output)
    return df

zonal_stats_table(dem_slope, final_recov, "slope.csv")
zonal_stats_table(dem_aspect, final_recov, "aspect.csv")

with rasterio.open(f'Coeff_recov.tif', 'w',
                 driver = 'GTiff',
                 height= final_recov.shape[0],
                 width=final_recov.shape[1],
                 count=1,
                 dtype=np.float64,
                 crs=data.crs,
                 transform=data.transform,
                 ndata =data.nodata
                 ) as tif_data:
        tif_data.write(final_recov,1)

print("The mean recovery coeffecient for the slope is higher meaning that the vegetation has recovered faster than the aspect which has a lower mean recovery coeffecient. Elevation did not impact recovery of the vegetation as much as direction of the slope.")
