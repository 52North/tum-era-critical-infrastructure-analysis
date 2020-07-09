# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 13:54:57 2020

@author: hfrv2
"""

# -*- coding: utf-8 -*-
"""
Python module for network simulation with physics based models for computing loads.


Created on Thu Jul  2 13:54:57 2020

@author: hfrv2
"""

#import numpy as np
import networkx as nx
import Constants as cons
import random
import os, sys
import pandas as pd
import geopandas as gpd
import pycrs
import numpy
from shapely.geometry import Point, LineString, Polygon

def read_files():
    busesfp = 'red_chile/buses.csv'
    busesexposurefp = 'red_chile/buses_elec_exposure.csv'
    allnodesfp = 'red_chile/all_nodes.csv'

    linesexposurefp = 'red_chile/C1_EPN_ExposureLines_modified.shp'
    linesfp = 'red_chile/lines.csv'

    powerplantsconsumersfp = 'red_chile/power_plants_consumers.csv'

    loadsfp = 'red_chile/loads.csv'

    transformersfp = 'red_chile/transformers.csv'

    folderfp = 'network'
    networkfp = 'network/network_valparaiso'

    if not os.path.exists(folderfp):
        os.mkdir(folderfp)

    buses = pd.read_csv(busesfp)
    busesexposure = pd.read_csv(busesexposurefp)
    allnodes = pd.read_csv(allnodesfp)

    lines = pd.read_csv(linesfp)

    linesexposure = gpd.read_file(linesexposurefp)

    powerplantsconsumers = pd.read_csv(powerplantsconsumersfp)

    loads = pd.read_csv(loadsfp)
    transformers = pd.read_csv(transformersfp)

    #print(allnodes)
    
def build_buses():
    # Creates file for the buses including buses of electrical analysis, power plants and consumers of exposure file and loads GEOJson and shape formats and creates indiviual shape files
    # Code to convert DataFrame to GeodataFrame adapted from https://www.kaggle.com/learn-forum/111860
    buses_df_geometry = [Point(xy) for xy in zip(buses.x, buses.y)] # Buses as points in space with coordinates of buses
    buses_gdf = gpd.GeoDataFrame(buses, geometry=buses_df_geometry) # Dataframe of buses
    #print(buses_gdf.head())

     # include power plants and consumers
    pp_consumers_point = gpd.GeoDataFrame(columns=powerplantsconsumers.columns.values)
    pp_consumers_geometry_point = []

    pp_consumers_xy = gpd.GeoDataFrame(columns=powerplantsconsumers.columns.values)
    pp_consumers_geometry_xy = []

    for index2, row2 in powerplantsconsumers.iterrows():
        if(pd.isnull(row2['x'])):
            # part adapted from https://stackoverflow.com/questions/50155703/pandas-column-convert-string-to-shapely-point-using-map-function
            pieces = row2['wkt_geom'].split() # splits each record into a list of 3
            x = float(pieces[1].lstrip('(')) # latitude
            y = float(pieces[2].rstrip(')')) # longitude 
            pp_consumers_geometry_point.insert(len(pp_consumers_geometry_point), Point(x,y))
            pp_consumers_point.loc[len(pp_consumers_point)] = row2
        else:          
            pp_consumers_geometry_xy.insert(len(pp_consumers_geometry_xy), Point(row2['x'], row2['y']))
            pp_consumers_xy.loc[len(pp_consumers_xy)] = row2 
    pp_consumers_xy_gdf = gpd.GeoDataFrame(pp_consumers_xy, geometry=pp_consumers_geometry_xy)
    pp_consumers_point_gdf = gpd.GeoDataFrame(pp_consumers_point, geometry=pp_consumers_geometry_point)
    #print(pp_consumers_point_gdf)
    #print(pp_consumers_xy_gdf)

    # include loads
    loads_gdf = gpd.GeoDataFrame(columns = numpy.append(loads.columns.values,'geometry'))
    for index, row in loads.iterrows():
        if(len(buses_gdf.loc[buses_gdf['name'] == row['bus']].index) == 0):
            print('The bus: ', row['bus'], 'does not exist, please add it to the network')
        else:
            idxload = buses_gdf.loc[buses_gdf['name'] == row['bus']].index[0]
            loads_gdf.loc[len(loads_gdf)] = [row['name'], row['bus'], row['Name Node'], 
                                             row['FID'], row['taxonomy'], row['Assumption'], 
                                             row['p_factor'], row['Load Name Database'],
                                             row['Point of Connection'], row['User Type'],
                                             buses_gdf['geometry'][idxload]]
    #print(loads_gdf)

    # crs definition buses
    buses_gdf.crs = "EPSG:32719"
    #print(buses_gdf.crs)
    # re-projection
    buses_gdf = buses_gdf.to_crs("EPSG:4326")    
    # Write the data into the Shapefile
    #buses_gdf.to_file(networkfp + '_buses.shp')

    # crs definition straight lines
    lines_gdf.crs = "EPSG:32719"
    #print(lines_gdf.crs)
    # re-projection
    lines_gdf = lines_gdf.to_crs("EPSG:4326")    
    # Write the data into the Shapefile
    #lines_gdf.to_file(networkfp + '_lines.shp')

    # crs definition power plants and consumers with coordinates y x and y
    pp_consumers_xy_gdf.crs = "EPSG:32719"
    #print(pp_consumers_xy_gdf.crs)
    # re-projection
    pp_consumers_xy_gdf = pp_consumers_xy_gdf.to_crs("EPSG:4326")
    # Write the data into the Shapefile
    #pp_consumers_xy_gdf.to_file(networkfp + '_consumers_generators.shp')

    # crs definition power plants and consumers with coordinates by points
    pp_consumers_point_gdf.crs = "EPSG:4326"
    #print(pp_consumers_point_gdf.crs)
    # Write the data into the Shapefile

    loads_gdf.crs = "EPSG:32719"
    #print(loads_gdf.crs)
    # re-projection
    loads_gdf = loads_gdf.to_crs("EPSG:4326") 
    # Write the data into the Shapefile
    #loads_gdf.to_file(networkfp + '_loads.shp')

    # Join buses of electrical analysis, power plants and consumers of exposure file and loads and export as GeoJSON file
    pp_consumers = pd.concat([pp_consumers_xy_gdf, pp_consumers_point_gdf])
    all_buses_gdf = pd.concat([buses_gdf, pp_consumers_xy_gdf, pp_consumers_point_gdf, loads_gdf])
    del all_buses_gdf['wkt_geom']
    all_buses_gdf.to_file(networkfp + '_all_buses.shp')
    all_buses_gdf.to_file(networkfp + '_all_buses.geojson', driver='GeoJSON')
    #print(all_buses_gdf)

def straight_lines():
# Create straigth lines from buses coordinates
    lines_gdf = gpd.GeoDataFrame(columns=numpy.append(lines.columns.values, 'geometry'))
    for index, row in lines.iterrows():
        #print('row', row.values)
        p0 = row['bus0']
        p1 = row['bus1']

        #print(lines_gdf)
        if(len(buses_gdf.loc[buses_gdf['name'] == p0].index) == 0):
            print("There is no bus:", p0, "Please add the bus to the network")
            sys.exit( 1 )
        else:
            indexp0 = buses_gdf.loc[buses_gdf['name'] == p0].index[0]

            p0geom = buses_gdf['geometry'][indexp0] 

        if(len(buses_gdf.loc[buses_gdf['name'] == p1].index) == 0):
            print("There is no bus:", p1, "Please add the bus to the network")
            sys.exit( 1 )
        else:
            indexp1 = buses_gdf.loc[buses_gdf['name'] == p1].index[0]

            p1geom = buses_gdf['geometry'][indexp1] 
        line = LineString([p0geom, p1geom])

        lines_gdf.loc[index] = [row['name'], row['bus0'], row['bus1'], row['x'], row['r'], row['s_nom'], row['Nemotecnico'], row['Nombre'], row['Nombre Linea'], row['Nombre Tramo'], line]

    #print(lines_gdf)
    # crs definition straight lines
    lines_gdf.crs = "EPSG:32719"
    #print(lines_gdf.crs)
    # re-projection
    lines_gdf = lines_gdf.to_crs("EPSG:4326")    
    # Write the data into the Shapefile
    lines_gdf.to_file(networkfp + '_straigt_lines.shp')
    
def build_lines():
    # include lines considered in the electrical analysis, the distribution lines of exposure file, additional lines, the lines corresponding to transformers and the conection between generators and substations and Generate a GeoJSON file
    # Generate lines with real path from exposure file with numbers of the "bus0" and "bus1" columns of electrical analysis
    linesexposure_gdf = gpd.GeoDataFrame(columns=numpy.append(linesexposure.columns.values, lines.columns.values))
    for index, row in lines.iterrows():
        #print('row', row.values)
        p0 = row['bus0']
        p1 = row['bus1']

        p0idx = buses.loc[buses['name'] == p0].index[0]
        p1idx = buses.loc[buses['name'] == p1].index[0]
        p0exposure = buses['FID'][p0idx]
        p1exposure = buses['FID'][p1idx]

        name = row['name']
        lineexists = False
        for index2, row2 in linesexposure.iterrows():     
            if((row2['FROM_ID'] == p0exposure and row2['TO_ID'] == p1exposure) or (row2['FROM_ID'] == p1exposure and row2['TO_ID'] == p0exposure)):           
                lineexists = True
                idxline = index2
                break
        if (lineexists == False):
            print("The line: ", name, " is not in the  Exposure File, please add the line to the network")
            #sys.exit( 1 )
        else:
            linesexposure_gdf.loc[len(linesexposure_gdf)] = numpy.append(linesexposure.iloc[idxline], row)
            # Update FROM and TO values
            fromidx = buses.loc[buses['FID'] == row2['FROM_ID']].index[0]
            toidx = buses.loc[buses['FID'] == row2['TO_ID']].index[0]
            fromname = buses['Name Node'][fromidx]
            toname = buses['Name Node'][toidx]
            linesexposure_gdf.loc[(len(linesexposure_gdf)-1), 'FROM'] = fromname
            linesexposure_gdf.loc[(len(linesexposure_gdf)-1), 'TO'] = toname

    # Distribution lines and additional lines to the lines considered in the electrical analysis
    distlines_gdf = gpd.GeoDataFrame(columns=numpy.append(linesexposure.columns.values, lines.columns.values))
    for index, row in linesexposure.iterrows():
        fidline = row['FID']
        lineincluded = False
        for index2, row2 in linesexposure_gdf.iterrows():
            if(row['FID'] == row2['FID']):
                lineincluded = True
        if(lineincluded == False):
            distlines_gdf.loc[len(distlines_gdf)] = row
            # Update FROM and TO values
            fromidx = allnodes.loc[allnodes['FID'] == row['FROM_ID']].index[0]
            toidx = allnodes.loc[allnodes['FID'] == row['TO_ID']].index[0]
            fromname = allnodes['Name Node'][fromidx]
            toname = allnodes['Name Node'][toidx]
            distlines_gdf.loc[(len(distlines_gdf)-1), 'FROM'] = fromname
            distlines_gdf.loc[(len(distlines_gdf)-1), 'TO'] = toname

    #print(len(linesexposure_gdf))
    #print(len(distlines_gdf))

    # include transformers as lines between primary and secondary side nodes
    transformers_gdf = gpd.GeoDataFrame(columns = numpy.append(transformers.columns.values,['FROM','TO','FROM_ID','TO_ID','Reactance','geometry']))

    for index, row in transformers.iterrows():
        indexbus0 = buses_gdf.loc[buses_gdf['name'] == row['bus0']].index[0]
        indexbus1 = buses_gdf.loc[buses_gdf['name'] == row['bus1']].index[0]

        bus0 = buses_gdf['geometry'][indexbus0]
        bus1 = buses_gdf['geometry'][indexbus1]

        line = LineString([bus0, bus1])

        transformers_gdf.loc[len(transformers_gdf)] = [row['name'], row['bus0'], row['bus1'], row['s_nom'], row['x'], row['Nombre'], row['Nemotecnico'], row['FID'], row['taxonomy'], buses_gdf['Name Node'][indexbus0], buses_gdf['Name Node'][indexbus1], buses_gdf['FID'][indexbus0], buses_gdf['FID'][indexbus1], row['x'], line]
    #print(transformers_gdf)

    # include connection between generators and substations
    generators_lines_gdf = gpd.GeoDataFrame(columns = ['FID', 'FROM', 'TO', 'taxonomy', 'FROM_ID', 'TO_ID', 'Reactance', 'name', 'Nombre', 'geometry'])
    for index, row in pp_consumers.iterrows():
        if((row['taxonomy'] == "Power Plant") or (row['taxonomy'] == "Power Plant Equivalent")):
            indexbus1 = buses_gdf.loc[buses_gdf['name'] == row['bus']].index[0]
            bus1 = buses_gdf['geometry'][indexbus1]
            bus0 = row.geometry

            line = LineString([bus0, bus1])
            generators_lines_gdf.loc[len(generators_lines_gdf)] = [row['FID'], row['Name Node'], buses['Name Node'][indexbus1], 'generation', row['FID'], buses['FID'][indexbus1], row['Synchronous Reactance Xd - Ohms'], row['name'], row['Name Node'], line]
    #print(generators_lines_gdf)
    # Delete lines of generators which are already included in the exposure file
    print('index', generators_lines_gdf.loc[generators_lines_gdf['FID'] == 267].index[0])
    generators_lines_gdf.drop(generators_lines_gdf.loc[generators_lines_gdf['FID'] == 267].index[0], axis=0, inplace=True)
    generators_lines_gdf.drop(generators_lines_gdf.loc[generators_lines_gdf['FID'] == 268].index[0], axis=0, inplace=True)
    generators_lines_gdf.drop(generators_lines_gdf.loc[generators_lines_gdf['FID'] == 269].index[0], axis=0, inplace=True)
    generators_lines_gdf.drop(generators_lines_gdf.loc[generators_lines_gdf['FID'] == 270].index[0], axis=0, inplace=True)
    generators_lines_gdf.drop(generators_lines_gdf.loc[generators_lines_gdf['FID'] == 271].index[0], axis=0, inplace=True)

    # crs definition lines considered in the electrical analysis
    linesexposure_gdf.crs = "EPSG:4326"
    # Write the data into the Shapefile
    linesexposure_gdf.to_file(networkfp + '_lines_elec_exposure.shp')

    # crs definition Distribution lines
    distlines_gdf.crs = "EPSG:4326"
    # Write the data into the Shapefile
    distlines_gdf.to_file(networkfp + '_lines_distribution.shp')

    # crs definition transformers
    transformers_gdf.crs = "EPSG:4326"
    print(transformers_gdf.crs) 
    # Write the data into the Shapefile
    transformers_gdf.to_file(networkfp + '_transformers.shp')

    # crs definition lines generators
    generators_lines_gdf.crs = "EPSG:4326"
    print(generators_lines_gdf.crs) 
    # Write the data into the Shapefile
    generators_lines_gdf.to_file(networkfp + '_lines_generators.shp')

    # Join lines considered in the electrical analysis, the distribution lines of exposure file and the lines corresponding to transformers and the conection between generators and substations
    all_lines = pd.concat([linesexposure_gdf, distlines_gdf, transformers_gdf, generators_lines_gdf])
    # Reassing FID
    all_lines['FID'] = numpy.arange(len(all_lines))
    # Write the data into the Shapefile
    all_lines.to_file(networkfp + '_all_lines.shp')
    all_lines.to_file(networkfp + '_all_lines.geojson', driver='GeoJSON')
    
def evaluate_system_loads(G):
    read_files()
    build_buses()
    straight_lines()
    build_lines()
    return G


    
    
