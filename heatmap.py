import plotly.graph_objects as go
import pandas as pd
import numpy as np
import meshtastic
import meshtastic.tcp_interface
import time
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

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

def create_dynamic_heatmap(data):
    if not data:
        print("No data available for heatmap.")
        return

    print("Creating dynamic heatmap...")
    df = pd.DataFrame(data)

    fig = go.Figure()

    for _, node in df.iterrows():
        lats = []
        lons = []
        colors = []
        sizes = []

        for i in range(50):  # Create 50 concentric circles for each node
            radius = i * 0.06  # 3km / 50 = 0.06km per step
            for angle in range(0, 360, 10):  # Create points around the circle
                lat = node['latitude'] + (radius / 111.32) * cos(radians(angle))
                lon = node['longitude'] + (radius / (111.32 * cos(radians(node['latitude'])))) * sin(radians(angle))
                lats.append(lat)
                lons.append(lon)
                colors.append(f"rgba(255, 165, 0, {1 - i/50})")  # Transition from orange to transparent
                sizes.append(5)  # Constant size for all points

        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.7
            ),
            hoverinfo='none',
            showlegend=False
        ))

    # Add the actual node points on top
    fig.add_trace(go.Scattermapbox(
        lat=df['latitude'],
        lon=df['longitude'],
        mode='markers',
        marker=dict(
            size=10,
            color='red',
            opacity=1
        ),
        text=df.apply(lambda row: f"Short Name: {row['short_name']}<br>"
                                  f"Long Name: {row['long_name']}<br>"
                                  f"Latitude: {row['latitude']:.6f}<br>"
                                  f"Longitude: {row['longitude']:.6f}<br>"
                                  f"SNR: {row['snr']}<br>"
                                  f"Last Heard: {row['last_heard']}", axis=1),
        hoverinfo='text'
    ))

    fig.update_layout(
        title='Meshtastic Node SNR Heatmap (3km radius)',
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
            zoom=10
        ),
        showlegend=False,
        height=800
    )

    fig.write_html("dynamic_snr_heatmap_3km.html")
    print("Dynamic heatmap saved as dynamic_snr_heatmap_3km.html")

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