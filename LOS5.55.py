import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from srtm import get_data
import matplotlib.colors as colors
from matplotlib.patches import Circle
import json
import os
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import io
from urllib.request import urlopen, Request
from PIL import Image
from tqdm import tqdm
import time
import tkinter as tk
from tkinter import ttk

# Initialize SRTM data
srtm_data = get_data()



def map_point_picker(last_settings):
    def on_map_click(event):
        if event.button == 1 and event.xdata is not None and event.ydata is not None:  # Left click within map area
            lon, lat = event.xdata, event.ydata
            if point_select.get() == "Point 1":
                point1_var.set(f"Point 1: {lat:.6f}, {lon:.6f}")
            else:
                point2_var.set(f"Point 2: {lat:.6f}, {lon:.6f}")

    def close_window():
        root.quit()
        root.destroy()

    root = tk.Tk()
    root.title("Map Point Picker")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Create a frame for the dropdown and button
    control_frame = ttk.Frame(frame)
    control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))

    point_select = ttk.Combobox(control_frame, values=["Point 1", "Point 2"])
    point_select.set("Point 1")
    point_select.pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(control_frame, text="DONE", command=close_window).pack(side=tk.LEFT)

    point1_var = tk.StringVar(value=f"Point 1: {last_settings['point1']['lat']:.6f}, {last_settings['point1']['lon']:.6f}")
    point2_var = tk.StringVar(value=f"Point 2: {last_settings['point2']['lat']:.6f}, {last_settings['point2']['lon']:.6f}")

    ttk.Label(frame, textvariable=point1_var).grid(row=1, column=0, columnspan=2)
    ttk.Label(frame, textvariable=point2_var).grid(row=2, column=0, columnspan=2)

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    map_tiles = cimgt.OSM()
    ax.add_image(map_tiles, 8)  # Adjust zoom level as needed

    # Set initial map extent (you may want to adjust this based on your default points)
    ax.set_extent([last_settings['point1']['lon'] - 1, last_settings['point1']['lon'] + 1,
                   last_settings['point1']['lat'] - 1, last_settings['point1']['lat'] + 1])

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.mpl_connect('button_press_event', on_map_click)
    canvas.get_tk_widget().grid(row=3, column=0, columnspan=2)

    root.mainloop()

    # Extract coordinates from StringVars
    point1_coords = point1_var.get().split(": ")[1].split(", ")
    point2_coords = point2_var.get().split(": ")[1].split(", ")

    return {
        "point1": {"lat": float(point1_coords[0]), "lon": float(point1_coords[1]), "height": last_settings['point1']['height']},
        "point2": {"lat": float(point2_coords[0]), "lon": float(point2_coords[1]), "height": last_settings['point2']['height']}
    }

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

# Define OpenTopoMap
class OpenTopoMap(cimgt.OSM):
    def _image_url(self, tile):
        x, y, z = tile
        url = 'https://a.tile.opentopomap.org/{}/{}/{}.png'.format(z, x, y)
        return url

OpenTopoMap.get_image = image_spoof

def load_last_settings():
    if os.path.exists('last_settings.json'):
        with open('last_settings.json', 'r') as f:
            return json.load(f)
    return {
        "point1": {"lat": 30.368449, "lon": -98.0621764, "height": 2},
        "point2": {"lat": 30.378449, "lon": -98.0721764, "height": 2}
    }

def save_settings(settings):
    with open('last_settings.json', 'w') as f:
        json.dump(settings, f)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def line_of_sight(start_lat, start_lon, end_lat, end_lon, start_height, end_height):
    try:
        start_elev = srtm_data.get_elevation(start_lat, start_lon)
        end_elev = srtm_data.get_elevation(end_lat, end_lon)
        
        if start_elev is None or end_elev is None:
            return False

        # Calculate the distance between the two points
        distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)
        
        # Calculate the total heights
        start_total_height = start_elev + start_height
        end_total_height = end_elev + end_height

        # Sample elevations along the line of sight
        steps = 100
        for i in range(steps + 1):
            fraction = i / steps
            inter_lat = start_lat + fraction * (end_lat - start_lat)
            inter_lon = start_lon + fraction * (end_lon - start_lon)
            inter_elev = srtm_data.get_elevation(inter_lat, inter_lon)
            
            if inter_elev is None:
                continue
            
            # Calculate the height of the line of sight at this point
            los_height = start_total_height + fraction * (end_total_height - start_total_height)
            
            # Check if the terrain is higher than the line of sight
            if inter_elev > los_height:
                return False

        return True
    except Exception as e:
        print(f"Error in line_of_sight: {str(e)}")
        print(f"Start: {start_lat}, {start_lon}, End: {end_lat}, {end_lon}")
        return False

def generate_los_map(point1, point2, radius_miles=10):  # Reduced radius to 10 km
    radius_km = radius_miles * 1.60934
    resolution = 1500  # Increased resolution to 1500x1500
    los_map = np.zeros((resolution, resolution))
    elevations = np.zeros((resolution, resolution))

    center_lat = point1['lat']
    center_lon = point1['lon']

    print(f"Center coordinates: {center_lat}, {center_lon}")
    print(f"Starting LOS map generation for {resolution}x{resolution} grid")

    total_iterations = resolution * resolution
    start_time = time.time()

    try:
        with tqdm(total=total_iterations, desc="Generating LOS map", unit="cell") as pbar:
            for i in range(resolution):
                for j in range(resolution):
                    angle = 2 * np.pi * i / resolution
                    distance = radius_km * (j / (resolution - 1)) ** 2  # Non-linear distance

                    target_lat = center_lat + (distance / 111.32) * np.cos(angle)
                    target_lon = center_lon + (distance / (111.32 * np.cos(np.radians(center_lat)))) * np.sin(angle)

                    # Check if the target point is within the 10 km radius
                    if haversine_distance(point1['lat'], point1['lon'], target_lat, target_lon) <= radius_km:
                        elevation = srtm_data.get_elevation(target_lat, target_lon)
                        elevations[i, j] = elevation if elevation is not None else 0

                        if line_of_sight(point1['lat'], point1['lon'], target_lat, target_lon, point1['height'], 0):
                            los_map[i, j] = 1  # Mark as visible
                        else:
                            los_map[i, j] = 0  # Mark as not visible
                    else:
                        los_map[i, j] = 0  # Mark as not visible (outside radius)
                    
                    pbar.update(1)

    except Exception as e:
        print(f"Error occurred at i={i}, j={j}")
        print(f"Current target: lat={target_lat}, lon={target_lon}")
        print(f"Exception: {str(e)}")
        raise

    end_time = time.time()
    total_time = end_time - start_time

    print("\nLOS map statistics:")
    print(f"Total cells: {los_map.size}")
    print(f"Visible cells: {np.sum(los_map == 1)}")
    print(f"Non-visible cells: {np.sum(los_map == 0)}")
    print(f"Total computation time: {total_time:.2f} seconds")

    return los_map, elevations, center_lat, center_lon

def plot_los_map(los_map, elevations, center_lat, center_lon, point1, point2, map_type='street'):
    fig = plt.figure(figsize=(15, 15))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # Set map extent to a 12 km square centered on point1
    extent_km = 6  # 6 km in each direction from the center
    ax.set_extent([point1['lon'] - (extent_km / 111.32), point1['lon'] + (extent_km / 111.32), 
                   point1['lat'] - (extent_km / 111.32), point1['lat'] + (extent_km / 111.32)], 
                  crs=ccrs.PlateCarree())

    # Add map tiles based on selection
    if map_type == 'street':
        map_tiles = cimgt.OSM()
    else:
        map_tiles = OpenTopoMap()
    
    ax.add_image(map_tiles, 12)  # Adjust zoom level as needed

    # Create custom colormap for LOS with solid black for shadows
    cmap = colors.ListedColormap(['black', 'none'])
    bounds = [0, 1]
    norm = colors.BoundaryNorm(bounds, cmap.N)
    
    # Overlay line of sight
    los_plot = ax.imshow(los_map, cmap=cmap, norm=norm, 
                         extent=[point1['lon'] - (extent_km / 111.32), point1['lon'] + (extent_km / 111.32), 
                                 point1['lat'] - (extent_km / 111.32), point1['lat'] + (extent_km / 111.32)], 
                         transform=ccrs.PlateCarree(), alpha=1.0, zorder=2)  # No transparency

    # Add 10km circle around Point 1
    circle_radius = 10 / 111.32  # Convert km to degrees
    ax.add_patch(Circle((point1['lon'], point1['lat']), circle_radius, 
                        fill=False, edgecolor='orange', linewidth=2, 
                        transform=ccrs.PlateCarree(), zorder=3, label='10 km Radius'))

    # Add labels for Point 1 and Point 2
    ax.text(point1['lon'], point1['lat'], 'Point 1', color='red', fontweight='bold', 
            ha='right', va='bottom', transform=ccrs.PlateCarree())
    ax.text(point2['lon'], point2['lat'], 'Point 2', color='blue', fontweight='bold', 
            ha='left', va='top', transform=ccrs.PlateCarree())

    plt.title('Line of Sight Map ({} Background)'.format('Street' if map_type == 'street' else 'Topographic'))
    
    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linestyle='--', color='gray', alpha=0.5, zorder=4)
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    # Add legend
    ax.plot([], [], color='red', linewidth=2, label='Point 1 (1km radius)')
    ax.plot([], [], color='blue', linewidth=2, label='Point 2 (1km radius)')
    ax.plot([], [], color='black', linewidth=5, label='No line of sight')
    ax.plot([], [], color='orange', linewidth=2, label='10 km Radius')
    ax.legend(loc='upper right')

    plt.show()

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm  # Import tqdm for progress bar

import numpy as np
import math

def find_intersection(ray_start, ray_end, elevations, distances):
    """
    Find the intersection between a ray and an elevation profile.
    
    :param ray_start: (x, y) coordinates of the ray's start point
    :param ray_end: (x, y) coordinates of the ray's end point
    :param elevations: array of elevation values
    :param distances: array of corresponding distances
    :return: (x, y) coordinates of the intersection point and the horizontal component,
             or None if no intersection
    """
    # Create line equations
    x1, y1 = ray_start
    x2, y2 = ray_end
    
    # Ray equation: y = mx + b
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    
    # Calculate y values for the ray at each distance point
    ray_y = m * distances + b
    
    # Find where the ray crosses the elevation profile
    signs = np.sign(ray_y - elevations)
    sign_changes = np.where(np.diff(signs) != 0)[0]
    
    if len(sign_changes) > 0:
        # Get the index just before the intersection
        idx = sign_changes[0]
        
        # Interpolate to find the exact intersection point
        x_intersect = distances[idx] + (distances[idx+1] - distances[idx]) * \
                      (ray_y[idx] - elevations[idx]) / \
                      ((elevations[idx+1] - elevations[idx]) - (ray_y[idx+1] - ray_y[idx]))
        y_intersect = m * x_intersect + b
        
        # Calculate the horizontal component
        ray_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        intersection_length = math.sqrt((x_intersect - x1)**2 + (y_intersect - y1)**2)
        horizontal_component = x_intersect - x1
        
        return x_intersect, y_intersect, horizontal_component
    
    return None  # No intersection found

def plot_cross_section(point1, point2):
    print("Starting plot_cross_section function...")
    
    # Determine which point is westernmost
    if point1['lon'] > point2['lon']:
        west_point, east_point = point2, point1
    else:
        west_point, east_point = point1, point2
    
    # Generate elevation profile from west to east
    latitudes = np.linspace(west_point['lat'], east_point['lat'], num=100)
    longitudes = np.linspace(west_point['lon'], east_point['lon'], num=100)
    elevations = [srtm_data.get_elevation(lat, lon) for lat, lon in zip(latitudes, longitudes)]
    
    print("Elevation profile generated.")
    
    # Calculate the total distance between the two points
    distance_km = haversine_distance(west_point['lat'], west_point['lon'], east_point['lat'], east_point['lon'])
    
    print(f"Total distance between points: {distance_km:.2f} km")
    
    # Create the cross-section plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 15), gridspec_kw={'height_ratios': [2, 1]})
    
    # Plot the street map
    ax1 = plt.subplot(211, projection=ccrs.PlateCarree())
    map_tiles = cimgt.OSM()
    ax1.add_image(map_tiles, 12)  # Adjust zoom level as needed
    
    # Set map extent
    buffer = 0.02  # Adjust this value to change the map extent
    ax1.set_extent([
        min(point1['lon'], point2['lon']) - buffer,
        max(point1['lon'], point2['lon']) + buffer,
        min(point1['lat'], point2['lat']) - buffer,
        max(point1['lat'], point2['lat']) + buffer
    ])
    
    # Plot Points 1 and 2
    ax1.plot(west_point['lon'], west_point['lat'], 'ro', markersize=10, transform=ccrs.PlateCarree(), label='West Point')
    ax1.plot(east_point['lon'], east_point['lat'], 'bo', markersize=10, transform=ccrs.PlateCarree(), label='East Point')
    
    # Add 1km circles around Points 1 and 2
    circle_radius = 1 / 111.32  # 1km in degrees
    ax1.add_patch(Circle((west_point['lon'], west_point['lat']), circle_radius, 
                         fill=False, edgecolor='red', transform=ccrs.PlateCarree()))
    ax1.add_patch(Circle((east_point['lon'], east_point['lat']), circle_radius, 
                         fill=False, edgecolor='blue', transform=ccrs.PlateCarree()))
    
    # Plot elevation profile
    ax2.plot(np.linspace(0, distance_km, num=100), elevations, color='blue', label='Elevation Profile')
    
    # Get the height of west and east points
    west_elevation = west_point['height'] + srtm_data.get_elevation(west_point['lat'], west_point['lon'])
    east_elevation = east_point['height'] + srtm_data.get_elevation(east_point['lat'], east_point['lon'])

    print(f"West point elevation: {west_elevation:.2f} m")
    print(f"East point elevation: {east_elevation:.2f} m")

    # Draw the line between west and east points
    ax2.plot([0, distance_km], [west_elevation, east_elevation], color='black', label='Line from West to East')

    # Prepare to store ray information
    ray_info = []

    # Generate distance array
    distances = np.linspace(0, distance_km, num=100)

    # Find the highest elevation point
    highest_elev_index = np.argmax(elevations)
    highest_elev = elevations[highest_elev_index]
    highest_elev_distance = distances[highest_elev_index]

    # Draw the first ray from west point to the highest elevation point
    ax2.plot([0, highest_elev_distance], [west_elevation, highest_elev], color='red', linewidth=2, label='First Ray (To Highest Point)')
    first_ray_angle = np.degrees(np.arctan2(highest_elev - west_elevation, highest_elev_distance))
    ray_info.append((1, first_ray_angle, highest_elev_distance))

    # Draw subsequent lines from the highest elevation point to 50 feet below east point until elevation reaches 0
    current_elevation = highest_elev
    ray_number = 1  # Start from 2 as we've already drawn the first ray
    angle = first_ray_angle  # Initialize angle with the first ray's angle

    print("Starting ray tracing...")
    
    # Use tqdm to create a progress bar
    with tqdm(total=90, desc="Processing rays") as pbar:
        while angle > -89:
            # Calculate the angle for the ray
            angle = np.degrees(np.arctan2(current_elevation - west_elevation, distance_km))  # Angle in degrees

            print(f"Processing ray {ray_number + 1} at angle {angle:.2f} degrees")

            # Calculate ray end point
            ray_end = (distance_km, current_elevation)

            # Find intersection
            intersection_point = find_intersection((0, west_elevation), ray_end, elevations, distances)

            if intersection_point:
                x_intersect, y_intersect, horizontal_component = intersection_point
                # Plot the ray up to the intersection point
                ax2.plot([0, x_intersect], [west_elevation, y_intersect], color='black', alpha=0.3)
                # Store ray information
                ray_info.append((ray_number + 1, angle, horizontal_component))
                print(f"Ray {ray_number + 1} intersects at {x_intersect:.2f} km")
            else:
                # If no intersection, plot the full ray
                ax2.plot([0, distance_km], [west_elevation, current_elevation], color='black', alpha=0.3)
                ray_info.append((ray_number + 1, angle, distance_km))
                print(f"Ray {ray_number + 1} does not intersect")

            # Decrease current elevation by 50 feet (converted to meters)
            current_elevation -= 50 * 0.3048  

            ray_number += 1  # Increment ray number
            pbar.update(1)  # Update progress bar

    print("Ray tracing completed.")

    ax2.axhline(y=west_elevation, color='red', linestyle='--', label='West Point Height')
    ax2.axhline(y=east_elevation, color='blue', linestyle='--', label='East Point Height')

    # Add labels for west and east points with coordinates
    ax2.text(0, west_elevation + 5, f'West Point\n({west_point["lat"]:.6f}, {west_point["lon"]:.6f})', 
             color='red', fontsize=10, ha='left', va='bottom')
    ax2.text(distance_km, 
             east_elevation + 5, f'East Point\n({east_point["lat"]:.6f}, {east_point["lon"]:.6f})', 
             color='blue', fontsize=10, ha='right', va='bottom')

    ax2.set_title('Elevation Profile with Rays (West to East)')
    ax2.set_xlabel('Distance (km)')
    ax2.set_ylabel('Elevation (m)')
    ax2.grid()
    ax2.legend()

    # Plot intersection points on the map
    for _, _, intersection_distance in ray_info:
        # Calculate the position of the intersection point
        frac = intersection_distance / distance_km
        lat = west_point['lat'] + frac * (east_point['lat'] - west_point['lat'])
        lon = west_point['lon'] + frac * (east_point['lon'] - west_point['lon'])
        ax1.plot(lon, lat, 'ko', markersize=3, transform=ccrs.PlateCarree())

    ax1.set_title('Map with Intersection Points (West to East)')
    ax1.legend()

    # Print the ray information table
    print("\nRay Number | Angle (degrees) | Intersection Distance (km)")
    print("---------------------------------------------------------")
    for ray_num, angle, intersection_distance in ray_info:
        print(f"{ray_num:>10} | {angle:>15.2f} | {intersection_distance:>25.2f}")

    plt.tight_layout()
    plt.show()

    print("plot_cross_section function completed.")
def main():
    last_settings = load_last_settings()
    
    use_map = input("Do you want to pick points from a map? (y/n): ").lower().strip() == 'y'
    
    if use_map:
        new_settings = map_point_picker(last_settings)
        point1 = new_settings['point1']
        point2 = new_settings['point2']
    else:
        # Input for Point 1
        print("Enter details for Point 1:")
        lat1 = input(f"Enter latitude (default {last_settings['point1']['lat']}): ")
        lon1 = input(f"Enter longitude (default {last_settings['point1']['lon']}): ")
        height1 = input(f"Enter height above ground in meters (default {last_settings['point1']['height']}): ")
        
        # Input for Point 2
        print("\nEnter details for Point 2:")
        lat2 = input(f"Enter latitude (default {last_settings['point2']['lat']}): ")
        lon2 = input(f"Enter longitude (default {last_settings['point2']['lon']}): ")
        height2 = input(f"Enter height above ground in meters (default {last_settings['point2']['height']}): ")
        
        # Update settings
        point1 = {
            'lat': float(lat1) if lat1 else last_settings['point1']['lat'],
            'lon': float(lon1) if lon1 else last_settings['point1']['lon'],
            'height': float(height1) if height1 else last_settings['point1']['height']
        }
        point2 = {
            'lat': float(lat2) if lat2 else last_settings['point2']['lat'],
            'lon': float(lon2) if lon2 else last_settings['point2']['lon'],
            'height': float(height2) if height2 else last_settings['point2']['height']
        }
    
    # Ask for heights separately
    point1['height'] = float(input(f"Enter height above ground for Point 1 in meters (default {point1['height']}): ") or point1['height'])
    point2['height'] = float(input(f"Enter height above ground for Point 2 in meters (default {point2['height']}): ") or point2['height'])
    
    # Save the new settings
    save_settings({"point1": point1, "point2": point2})
    
    # Generate the cross-section
    plot_cross_section(point1, point2)

if __name__ == "__main__":
    main()