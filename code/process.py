import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from glob import glob
import os
import pandas as pd

# === USER INPUT: SET YEAR AND MONTH ===
year = "2025"
month = "02" # Make sure month is two digits, e.g., "02" for February
date_str = f"{year}-{month}-01"

# === CONFIGURATION ===
data_dir = f"1-data"
output_file = f"ch4_surface_{year}{month}.nc" # Consider adding year and month to output file
lat_min, lat_max = -15, 30
lon_min, lon_max = 90, 150
grid_res = 0.25  # degrees

# === TARGET GRID ===
target_lat = np.arange(lat_min, lat_max + grid_res, grid_res)
target_lon = np.arange(lon_min, lon_max + grid_res, grid_res)
grid_lon, grid_lat = np.meshgrid(target_lon, target_lat)

# === INTERPOLATION LOOP ===
interpolated_stack = []

# --- MODIFICATION START ---
# Construct the filename pattern based on year and month
# The pattern is TROPESS_AIRS-Aqua_L2_Summary_CH4_yyyymm*.nc
filename_pattern = f"TROPESS_AIRS-Aqua_L2_Summary_CH4_{year}{month}*.nc"

# Construct the full search pattern to look in data_dir and its subdirectories
# The use of "**" and recursive=True allows finding files in subdirectories of data_dir
search_path_pattern = os.path.join(data_dir, "**", filename_pattern)
file_list = sorted(glob(search_path_pattern, recursive=True))
# --- MODIFICATION END ---

if not file_list:
    # Updated error message to reflect the specific pattern
    raise FileNotFoundError(f"No NetCDF files found in '{data_dir}' matching pattern '{filename_pattern}'")

print(f"Found {len(file_list)} files matching the pattern: {filename_pattern}")
for f_path in file_list:
    print(f" - {os.path.basename(f_path)}")


for file_path in file_list: # Renamed 'file' to 'file_path' to avoid conflict with 'file' type
    print(f"Processing file: {file_path}")
    try:
        ds = xr.open_dataset(file_path)

        # Assuming 'target' dimension exists and pressure is under 'target=0' or similar
        # This part might need adjustment based on exact data structure if it varies
        if "target" in ds["pressure"].dims and ds["pressure"].sizes["target"] > 0:
            surface_index = np.argmin(np.abs(ds["pressure"].isel(target=0).values - 1000))
        elif "level" in ds["pressure"].dims and ds["pressure"].sizes["level"] > 0: # Common alternative dimension name
            surface_index = np.argmin(np.abs(ds["pressure"].isel(level=0).values - 1000)) # Or appropriate selection logic
        else: # Fallback or if pressure is 1D without 'target' or 'level' but is the vertical profile
            surface_index = np.argmin(np.abs(ds["pressure"].values - 1000))


        mask = (
            (ds["latitude"] >= lat_min) & (ds["latitude"] <= lat_max) &
            (ds["longitude"] >= lon_min) & (ds["longitude"] <= lon_max)
        )
        if mask.sum() == 0:
            print(f"No data within specified lat/lon bounds for {os.path.basename(file_path)}. Skipping.")
            continue

        lats = ds["latitude"].values[mask]
        lons = ds["longitude"].values[mask]
        
        # Ensure 'x' variable (CH4 data) has dimensions compatible with the mask and surface_index
        # Original script had ds["x"].values[mask, surface_index]
        # Check if 'x' is 2D (e.g., obs, pressure_level) or needs different indexing
        if len(ds["x"].shape) == 2 and ds["x"].shape[0] == mask.size : # e.g. (num_observations, num_pressure_levels)
             ch4_surface = ds["x"].values[mask, surface_index]
        elif len(ds["x"].shape) == ds["latitude"].ndim + ds["pressure"].ndim -1 : # Assuming x matches lat/lon spatial dims then pressure
             # This case needs more careful handling based on actual dimensions of 'x'
             # For example, if x is (lat, lon, pressure), mask would need to be applied differently
             # The original code ds["x"].values[mask, surface_index] implies 'mask' applies to the spatial/observation dimension
             # and 'surface_index' to the pressure dimension.
             # This example assumes 'x' data aligns with how 'latitude' and 'longitude' are structured before masking.
             # If ds["x"] has same dimension length as unmasked latitude/longitude, then:
            temp_x_values = ds["x"].values
            if temp_x_values.shape[0] == ds["latitude"].shape[0]: # if first dim of x matches spatial obs
                 ch4_surface = temp_x_values[mask, surface_index]
            else: # Need specific logic if dimensions don't align as simply
                 print(f"Skipping {file_path} due to unexpected 'x' dimensions: {ds['x'].shape}")
                 continue
        else:
            print(f"Skipping {file_path} due to incompatible 'x' dimensions: {ds['x'].shape}")
            continue


        points = np.column_stack((lons, lats))
        grid_linear = griddata(points, ch4_surface, (grid_lon, grid_lat), method='linear')
        grid_nearest = griddata(points, ch4_surface, (grid_lon, grid_lat), method='nearest')
        grid_combined = np.where(np.isnan(grid_linear), grid_nearest, grid_linear)

        interpolated_stack.append(grid_combined)
        ds.close() # Close the dataset
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        # Optionally, decide if you want to continue or stop on error
        # continue

# === AVERAGING ===
if not interpolated_stack:
    print("No data was successfully interpolated. Exiting.")
    exit() # Or handle as appropriate

mean_ch4_grid = np.nanmean(interpolated_stack, axis=0).astype("float32")

# === CF TIME COORDINATE ===
base_time_str = "2000-01-01 00:00:00"
time_units = f"hours since {base_time_str}"
calendar = "standard"
hours_offset = int((pd.to_datetime(date_str) - pd.to_datetime(base_time_str)).total_seconds() / 3600)

# === CREATE GRADS-COMPATIBLE DATASET ===
mean_ch4_da = xr.DataArray(
    data=mean_ch4_grid[np.newaxis, :, :],
    coords=dict(
        time=("time", [hours_offset], {"units": time_units, "calendar": calendar}),
        lat=("lat", target_lat.astype("float32"), {"units": "degrees_north", "standard_name": "latitude"}),
        lon=("lon", target_lon.astype("float32"), {"units": "degrees_east", "standard_name": "longitude"})
    ),
    dims=["time", "lat", "lon"],
    name="ch4"
)
mean_ch4_da.attrs["long_name"] = "CH₄ VMR at Surface (~1000 hPa)"
mean_ch4_da.attrs["units"] = "ppb"

# === SAVE OUTPUT ===
# Consider making output_file name more dynamic if year/month change often
output_path = os.path.join(os.path.dirname(data_dir), output_file) # Save outside 1-data
mean_ch4_da.to_dataset().to_netcdf(output_path)
print(f"✅ Saved: {output_path}")

# === OPTIONAL PLOT ===
plt.figure(figsize=(10, 6))
im = plt.pcolormesh(target_lon, target_lat, mean_ch4_grid, cmap='plasma', shading='auto', vmin=np.nanmin(mean_ch4_grid), vmax=np.nanmax(mean_ch4_grid))
plt.colorbar(im, label="Surface-Level CH₄ VMR (ppb)")
plt.title(f"Mean Surface-Level CH₄ - {year}-{month}")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
# Save the plot
plot_file = f"ch4_surface_{year}{month}.png"
plot_path = os.path.join(os.path.dirname(data_dir), plot_file) # Save outside 1-data
plt.savefig(plot_path)
print(f"✅ Saved plot: {plot_path}")
plt.show() # Keep if interactive display is needed
