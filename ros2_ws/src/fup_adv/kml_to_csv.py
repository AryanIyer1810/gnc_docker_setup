#!/usr/bin/env python3
import os
import sys
import fiona
import math
import numpy as np
import pandas as pd 
import geopandas as gpd 
import matplotlib.pyplot as plt

fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 kml_to_csv.py <your_file.kml>")
        sys.exit(1)

    filename = sys.argv[1]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kml_file = os.path.join(base_dir, filename)
    csv_file = os.path.join(base_dir, 'waypoints.csv')

    if not os.path.exists(kml_file):
        print(f"ERROR: KML file not found at {kml_file}")
        sys.exit(1)

    print("Parsing Geographic KML Data...")
    geo_df = gpd.read_file(kml_file, driver='KML', layer='Items')
    df = pd.DataFrame(geo_df)

    # Extract coordinates
    df['lat'] = df.geometry.apply(lambda p: p.y)
    df['lon'] = df.geometry.apply(lambda p: p.x)
    df['alt'] = df.geometry.apply(lambda p: p.z)

    lat = np.array(df['lat'])
    lon = np.array(df['lon'])
    alt = np.array(df['alt'])

    # Return to home logic
    returnToHome = True
    if returnToHome:
        lat = np.append(lat, lat[1])
        lon = np.append(lon, lon[1])
        alt = np.append(alt, alt[1])    
        lat = np.append(lat, lat[0])
        lon = np.append(lon, lon[0])
        alt = np.append(alt, alt[0])    

    waypoints = np.vstack((lat, lon, alt))
    lat_ref = waypoints[0][0]
    lon_ref = waypoints[1][0]
    h_ref = waypoints[2][0]

    for i in range(len(waypoints[0])):
        in_lat = waypoints[0][i]
        in_lon = waypoints[1][i]
        h = waypoints[2][i]

        # 1. Standard Spherical Differences (Corrected d_lon sign)
        d_lat = np.deg2rad(in_lat - lat_ref)
        d_lon = np.deg2rad(in_lon - lon_ref)

        f = 1/298.257223563 
        R = 6378137 
        minusf2 = 2*f - f**2
        R_n = R/math.sqrt(1-minusf2*(math.sin(np.deg2rad(lat_ref)))**2)
        R_m = R_n * (1 - minusf2) / (1-minusf2*(math.sin(np.deg2rad(lat_ref)))**2)
        
        # 2. Pure Geodetic Distances in meters
        d_N = R_m * d_lat
        d_E = R_n * math.cos(np.deg2rad(lat_ref)) * d_lon

        # 3. ENU to NED Mapping (The crucial fix)
        p_x = d_N           # PX4 X is North
        p_y = d_E           # PX4 Y is East
        p_z = -(h - h_ref)  # PX4 Z is Down (so Up is negative)

        waypoints[0][i] = p_x
        waypoints[1][i] = p_y
        waypoints[2][i] = p_z

    # Note: Z is already negative from the mapping above, so we don't multiply by -1 here anymore.
    waypoints_df = pd.DataFrame({'x': waypoints[0], 'y': waypoints[1], 'z': waypoints[2]})
    waypoints_df.to_csv(csv_file, index=False, header=False)
    print(f"[SUCCESS] Projected NED Waypoints saved to {csv_file}")

    # Plot (Mapping East to horizontal axis and North to vertical axis to look like a map)
    start_x = waypoints[0][0] # North
    start_y = waypoints[1][0] # East
    fig, ax = plt.subplots()
    ax.plot(waypoints[1], waypoints[0], linewidth=2) 
    ax.plot(start_y, start_x, 'ro')
    plt.title("Waypoint Trajectory (NED Local Frame)")
    plt.xlabel("East (Y)")
    plt.ylabel("North (X)")
    plt.grid(True)
    plt.axis('equal') # Ensures the map isn't stretched
    plt.show()

if __name__ == '__main__':
    main()
