import plotly.graph_objects as go
import pandas as pd
import numpy as np
import meshtastic
import meshtastic.tcp_interface
import time
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from srtm import get_data

# Initialize SRTM data
srtm_data = get_data()

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def get_node_data(host_ip):
    print(f"Connecting to Meshtastic node at {host_ip}...")
    try:
        interface = meshtastic.tcp_interface.TCPInterface(hostname=host_ip)
        print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return []

    print("Waiting for node information...")
    time.sleep(5)

    nodes = interface.nodes
    print(f"Retrieved information for {len(nodes)} nodes.")

    data = []
    for node_id, node in nodes.items():
        print(f"Processing node: {node_id}")
        if 'position' in node and 'snr' in node:
            lat = node['position']['latitude']
            lon = node['position']['longitude']
            snr = node['snr']
            short_name = node.get('user', {}).get('shortName', 'Unknown')
            long_name = node.get('user', {}).get('longName', 'Unknown')
            last_heard = datetime.fromtimestamp(node.get('lastHeard', 0)).strftime('%Y-%m-%d %H:%M:%S')
            data.append({
                'latitude': lat,
                'longitude': lon,
                'snr': snr,
                'short_name': short_name,
                'long_name': long_name,
                'last_heard': last_heard
            })
            print(f"  Latitude: {lat}, Longitude: {lon}, SNR: {snr}, Short Name: {short_name}, Long Name: {long_name}, Last Heard: {last_heard}")
        else:
            print("  Incomplete data for this node, skipping...")

    interface.close()
    print("Connection closed.")
    return data

def get_color_for_distance(distance):
    # ROYGBIV color scheme
    colors = [
        (255, 165, 0),   # Orange
        (255, 0, 0),     # Red
        (255, 255, 0),   # Yellow
        (0, 255, 0),     # Green
        (0, 255, 255),   # Blue
        (0, 0, 255),     # Indigo
        (143, 0, 255)    # Violet
    ]
    
    # Normalize distance to 0-1 range
    t = min(distance / 3.5, 1.0)
    
    # Find the two colors to interpolate between
    idx = int(t * (len(colors) - 1))
    if idx == len(colors) - 1:
        return f'rgb{colors[-1]}'
    
    # Interpolate between the two colors
    color1 = colors[idx]
    color2 = colors[idx + 1]
    f = t * (len(colors) - 1) - idx
    r = int(color1[0] * (1-f) + color2[0] * f)
    g = int(color1[1] * (1-f) + color2[1] * f)
    b = int(color1[2] * (1-f) + color2[2] * f)
    
    return f'rgb({r},{g},{b})'


def line_of_sight(start_lat, start_lon, end_lat, end_lon, start_height=2):
    # Get elevations
    start_elev = srtm_data.get_elevation(start_lat, start_lon)
    end_elev = srtm_data.get_elevation(end_lat, end_lon)

    # Calculate distance
    distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)

    # Check if end point is visible
    if end_elev is None:
        return False

    # Simple line of sight check
    elevation_difference = end_elev - (start_elev + start_height)
    angle = np.arctan2(elevation_difference, distance * 1000)  # Convert km to m

    # Arbitrary threshold for visibility (you may need to adjust this)
    return angle > -0.1  # radians

import traceback

def create_dynamic_heatmap(data):
    if not data:
        print("No data available for heatmap.")
        return

    print("Creating dynamic heatmap...")
    df = pd.DataFrame(data)
    print(f"Number of nodes: {len(df)}")

    try:
        fig = go.Figure()

        for index, node in df.iterrows():
            print(f"Processing node {index + 1}/{len(df)}")
            lats = []
            lons = []
            colors = []
            hover_texts = []

            for radius in np.arange(0, 3.6, 0.2):
                color = get_color_for_distance(radius)

                for angle in range(0, 360, 20):
                    lat = node['latitude'] + (radius / 111.32) * cos(radians(angle))
                    lon = node['longitude'] + (radius / (111.32 * cos(radians(node['latitude'])))) * sin(radians(angle))
                    
                    if line_of_sight(node['latitude'], node['longitude'], lat, lon):
                        lats.append(lat)
                        lons.append(lon)
                        colors.append(color)
                        
                        if radius <= 0.3:
                            hover_text = (f"Short Name: {node['short_name']}<br>"
                                          f"Long Name: {node['long_name']}<br>"
                                          f"Latitude: {node['latitude']:.6f}<br>"
                                          f"Longitude: {node['longitude']:.6f}<br>"
                                          f"SNR: {node['snr']}<br>"
                                          f"Last Heard: {node['last_heard']}")
                            hover_texts.append(hover_text)
                        else:
                            hover_texts.append(None)
                    else:
                        break

            print(f"Node {index + 1}: {len(lats)} points plotted")

            fig.add_trace(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode='markers',
                marker=dict(
                    size=5,
                    color=colors,
                    opacity=0.7
                ),
                text=hover_texts,
                hoverinfo='text',
                showlegend=False
            ))

        print("All nodes processed. Updating layout...")
        fig.update_layout(
            title='Meshtastic Node SNR Heatmap (3.5km radius with Topography)',
            mapbox_style="open-street-map",
            mapbox=dict(
                center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
                zoom=10
            ),
            showlegend=False,
            height=800,
            hoverlabel=dict(
                bgcolor="rgba(0, 0, 255, 0.8)",
                font_size=12,
                font_family="Rockwell"
            )
        )

        print("Layout updated. Writing HTML file...")
        fig.write_html("dynamic_snr_heatmap_3.5km_topo.html")
        print("Dynamic heatmap saved as dynamic_snr_heatmap_3.5km_topo.html")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())

def main():
    host_ip = "192.168.1.95"  # The IP address of your Meshtastic node

    print("Starting Meshtastic Dynamic SNR Heatmap Generator")
    print("=================================================")

    try:
        data = get_node_data(host_ip)

        if not data:
            print("No valid node data found. Exiting.")
            return

        print(f"Retrieved data for {len(data)} nodes.")

        create_dynamic_heatmap(data)

        print("Dynamic heatmap generation complete.")
    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    main()