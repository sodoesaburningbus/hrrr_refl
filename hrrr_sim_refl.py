### This program pulls operational HRRR simulated
### composite reflectivity for the United States.

##### START OPTIONS #####

# Location of HRRR data
hrrr_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/"


# Location to save the gif
sdir = "hrrr_simZ/"

# Offset from current time when pulling model
# This is subtracted so if offset=2, the code pulls the HRRR
# run 2 hours before the current time
offset = 3

#####  END OPTIONS  #####

### Import modules
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime, timedelta
import matplotlib.pyplot as pp
from matplotlib.colors import Normalize
import numpy
import os
import pygrib

# Delete the old files
os.system("rm {}/*".format(sdir))

# Build the HRRR urls
urls = []
date = datetime.utcnow()-timedelta(hours=offset)
for i in range(48):
    urls.append(hrrr_url+"hrrr.{}/conus/hrrr.t{:02d}z.wrfprsf{:02d}.grib2".format(
        date.strftime("%Y%m%d"), date.hour, i))

### Loop over the urls, downloading just the reflectivity data
try:
    for i, url in enumerate(urls):

        # Download index file
        print(url)
        os.system("curl -o index {}".format(url+".idx"))

        # Open index file to find relevant bytes
        fn = open("index", "r")
        flag = False
        for line in fn:

            # Check if var already found
            if flag:
                byte_end = line.split(":")[1]
                break

            # Locate variable
            if ("REFC" in line):
                byte_start = line.split(":")[1]
                flag = True

        # Download the HRRR data
        os.system("curl -o hrrr_out -r {}-{} {}".format(byte_start, byte_end, url))

        # Grab the data
        grib = pygrib.open("hrrr_out")
        z = grib[1].values
        lons = grib[1].longitudes.reshape(z.shape)
        lats = grib[1].latitudes.reshape(z.shape)
        vd = grib[1].validDate
        ad = grib[1].analDate
        grib.close()

        # Mask out the boring stuff
        z[z<=5] = numpy.nan

        # Plot
        fig, ax = pp.subplots(figsize=(8,6), subplot_kw={"projection":ccrs.PlateCarree()})

        # Pretty map
        ax.coastlines()
        ax.add_feature(cfeature.STATES, edgecolor="black", zorder=3)
        ax.add_feature(cfeature.RIVERS, zorder=1)
        ax.add_feature(cfeature.LAKES, edgecolor="black", zorder=1)
        ax.add_feature(cfeature.OCEAN, edgecolor="black", zorder=1)

        # Add data
        cont = ax.contourf(lons, lats, z, cmap="gist_ncar", levels=numpy.arange(0, 85, 5),
            transform=ccrs.PlateCarree(), norm=Normalize(-25, 80), zorder=2)
        ax.set_extent((lons.min(), lons.max(), lats.min(), lats.max()))
        cb = fig.colorbar(cont, orientation="horizontal", pad=0.02)
        cb.set_label("Composite Reflectivity (dBZ)", fontsize=14, fontweight="bold")
        ax.set_title("Valid: {} UTC, {:02d}Z HRRR\nForecast Hour {:02d}".format(vd, ad.hour, i), fontsize=14, fontweight="bold", loc="left", ha="left")

        # Add inset plot
        ax2 = fig.add_axes([0.13, 0.22, 0.275, 0.275], projection=ccrs.PlateCarree())    # Create axis
        ax2.set_extent((-92.0, -80.0, 30.0, 37.0))           # Set extent
        ax2.contourf(lons, lats, z, cmap="gist_ncar", levels=numpy.arange(0, 85, 5),
            transform=ccrs.PlateCarree(), norm=Normalize(-25, 80), zorder=2)

        ax2.scatter(-86.5861, 34.7304, c="crimson", marker="*", zorder=4)
        ax2.coastlines()
        ax2.add_feature(cfeature.STATES, edgecolor="black", zorder=3)
        ax2.add_feature(cfeature.RIVERS, zorder=1)
        ax2.add_feature(cfeature.LAKES, edgecolor="black", zorder=1)
        ax2.add_feature(cfeature.OCEAN, edgecolor="black", zorder=1)
        ax2.outline_patch.set_linewidth(2)

        # Save the image
        pp.savefig(sdir+"hrrr_refl_{:02d}f".format(i))
        pp.close()
except Exception as err:
    print(err)

# Make the gif
os.system("convert -delay 100 -loop 0 {0}/*.png {0}/radar_loop.gif".format(sdir))

# Clean up dummy files
os.system("rm index")
os.system("rm hrrr_out")
