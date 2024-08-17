import numpy as np
import matplotlib.pyplot as plt
from srtm import get_data
import matplotlib.colors as colors
from matplotlib.patches import Circle
import json
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt
import io
from urllib.request import urlopen, Request
from PIL import Image

# Initialize SRTM data
srtm_data = get_data()

def image_spoof(self, tile):
    url = self._image_url(tile)
    req = Request(url)
    req.add_header('User-agent', 'Anaconda 3')
    fh = urlopen(req)
    im_data = io.BytesIO(fh.read())
    fh.close()
    img = Image.open(im_data)
    img = img.convert(self.desired_tile_form)
    return img, self.tileextent(tile), 'lower'

cimgt.OSM.get_image = image_spoof

def load_last_coordinates():
    if os.path.exists('last_coordinates.json'):
        with open('last_coordinates.json', 'r') as f:
            return json.load(f)
    return {"lat": 30.368449, "lon": -98.0621764}  # Default coordinates

def save_coordinates(lat, lon):
    with open('last_coordinates.json', 'w') as f:
        json.dump({"lat": lat, "lon": lon}, f)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def line_of_sight(start_lat, start_lon, end_lat, end_lon, start_height=2):
    start_elev = srtm_data.get_elevation(start_lat, start_lon)
    end_elev = srtm_data.get_elevation(end_lat, end_lon)
    
    if start_elev is None or end_elev is None:
        return False

    distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)
    elevation_difference = end_elev - (start_elev + start_height)
    angle = np.arctan2(elevation_difference, distance * 1000)
    
    visibility_threshold = 0
    return angle > visibility_threshold

def generate_los_map(center_lat, center_lon, radius_miles=30):
    radius_km = radius_miles * 1.60934
    resolution = 300
    los_map = np.zeros((resolution, resolution))
    elevations = np.zeros((resolution, resolution))

    for i in range(resolution):
        for j in range(resolution):
            angle = 2 * np.pi * i / resolution
            distance = radius_km * j / (resolution - 1)

            target_lat = center_lat + (distance / 111.32) * np.cos(angle)
            target_lon = center_lon + (distance / (111.32 * np.cos(np.radians(center_lat)))) * np.sin(angle)

            elevation = srtm_data.get_elevation(target_lat, target_lon)
            elevations[i, j] = elevation if elevation is not None else 0

            if line_of_sight(center_lat, center_lon, target_lat, target_lon):
                los_map[i, j] = 1
            else:
                los_map[i, j] = 0

    return los_map, elevations

def plot_los_map(los_map, elevations, center_lat, center_lon):
    fig = plt.figure(figsize=(15, 15))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # Set map extent
    extent_deg = 0.5  # Approximately 30 miles
    ax.set_extent([center_lon - extent_deg, center_lon + extent_deg, 
                   center_lat - extent_deg, center_lat + extent_deg], 
                  crs=ccrs.PlateCarree())

    # Add OpenStreetMap tiles as the background
    osm_tiles = cimgt.OSM()
    ax.add_image(osm_tiles, 12)  # Adjust zoom level as needed

    # Create custom colormap for LOS
    cmap = colors.ListedColormap(['black', 'none'])
    bounds = [0, 0.5, 1]
    norm = colors.BoundaryNorm(bounds, cmap.N)
    
    # Overlay line of sight
    los_plot = ax.imshow(los_map, cmap=cmap, norm=norm, 
                         extent=[center_lon - extent_deg, center_lon + extent_deg, 
                                 center_lat - extent_deg, center_lat + extent_deg], 
                         transform=ccrs.PlateCarree(), alpha=0.5, zorder=2)

    # Add 1km red circle around the center point
    circle_radius = 1 / 111.32
    ax.add_patch(Circle((center_lon, center_lat), circle_radius, 
                        fill=False, edgecolor='red', linewidth=2, 
                        transform=ccrs.PlateCarree(), zorder=3))

    plt.title('Line of Sight Map with OpenStreetMap Background (30-mile Radius)')
    ax.gridlines(draw_labels=True, zorder=4)

    # Add legend
    ax.plot([], [], color='red', linewidth=2, label='1km radius')
    ax.plot([], [], color='black', linewidth=5, label='No line of sight')
    ax.legend(loc='upper right')

    plt.show()
def main():
    last_coords = load_last_coordinates()
    
    lat_input = input(f"Enter latitude (default {last_coords['lat']}): ")
    lon_input = input(f"Enter longitude (default {last_coords['lon']}): ")
    
    center_lat = float(lat_input) if lat_input else last_coords['lat']
    center_lon = float(lon_input) if lon_input else last_coords['lon']
    
    save_coordinates(center_lat, center_lon)

    print(f"Generating line of sight map for coordinates: {center_lat}, {center_lon}")
    los_map, elevations = generate_los_map(center_lat, center_lon, radius_miles=30)
    print("LOS map contains zeros:", np.any(los_map == 0))

    plot_los_map(los_map, elevations, center_lat, center_lon)

if __name__ == "__main__":
    main()