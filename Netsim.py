# -*- coding: utf-8 -*-
"""
Python module for network simulation. Contains the main steps of the Monte Carlo Simulation:
    - Direct Hazard Action: applies a random damage state to the system, given probabilities of failures assigned to the nodes by the damage web service
    - Cascading Effects: simulates systemic failures due to overloading. Affects nodes and lines
    - State of consumer areas: estimates the affectation to the consumer areas, based on the damage level of the supplier lines
    - other functions:
        - Network update: removes failed/isolated source and consumer nodes, and updates surviving component capacities, 
        for recomputing the loads during the simulation of cascading effects
        - Is edge in path?: returns true or false, depending whether an edge is in a given path.

Created on Wed Aug 14 14:49:53 2019

@author: hfrv2
"""

import numpy as np
import networkx as nx
import Constants as cons

def direct_hazard_action(G): 
        # Evaluate Component Fragilities
        for node in G.nodes():
            n_pof=G.nodes[node][cons.NODE_POF]
            # if component is certainly damaged
            if n_pof>1-cons.EPS:
                G.nodes[node][cons.NODE_DAMAGE]=1
            # if component is certainly working
            elif n_pof<cons.EPS:
                G.nodes[node][cons.NODE_DAMAGE]=0
            else:
                #generate random value between 0 and 1
                r_value=np.random.rand()
                #query probability of failure
                if r_value<n_pof:
                    G.nodes[node][cons.NODE_DAMAGE]=1

# UPDATE SOURCE AND CONSUMER NODES; AND EDGE WEIGHTS
# The damage increment DELTADAMAGE is reset to zero after updating the damage of the components
def update_network(G,s_nodes,c_nodes):
    # first, reduce node capacities
    for node in G.nodes():
        # if damage is close to 1 (e.g. by hazard action), set capacity to zero
        if G.node[node][cons.NODE_DAMAGE]>1.0-cons.MIN_DAMAGE:
            if node in s_nodes:
                s_nodes.remove(node)
            if node in c_nodes:
                c_nodes.remove(node)
            G.node[node][cons.CAPACITY]=0.0
            # damaged node also makes its edges unavailable
            for edge in G.edges(node):
               G.edges[edge][cons.WEIGHT]=1/cons.EPS 
                
        #otherwise, only reduce capacity
        else:
            G.node[node][cons.CAPACITY]-=G.node[node][cons.NODE_DELTADAMAGE]*G.node[node][cons.CAPACITY]
            #we already applied the damage increment
            G.node[node][cons.NODE_DELTADAMAGE]=0.0
    # now, increase edge cost and reduce their capacities
    for edge in G.edges():
        G.edges[edge][cons.CAPACITY]-=G.edges[edge][cons.LINE_DELTADAMAGE]*G.edges[edge][cons.CAPACITY]
        G.edges[edge][cons.WEIGHT]/=max(1-G.edges[edge][cons.LINE_DELTADAMAGE],cons.EPS)
        #we already applied the damage increment
        G.edges[edge][cons.LINE_DELTADAMAGE]=0.0


def evaluate_system_loads(G,s_nodes,c_nodes):

    loads_initial={}
    edge_loads_initial={}   
    # Determine shortest path between all source and target nodes and set
    # the nr of shortest paths passing through each node in network as
    # initialize loads with 1 for assigning a minimum non zero capacity to each component
    loads_initial={no:1 for no in G.nodes()}
    edge_loads_initial={ed:1 for ed in G.edges()}
    # evaluate inital origin-destination betweenness centrality
    # determine initial number of connecting paths from all source node to
    # each supply node
    for s_node in s_nodes:
        for c_node in c_nodes:
            path_list=nx.all_shortest_paths(G,s_node,c_node,weight=cons.WEIGHT)
            path_list=list(path_list)               
            if len(path_list)>0:
                for a_path in path_list:
                    for node in G.nodes():
                        if node in a_path:
                            loads_initial[node]+=1
                    for edge in G.edges():
                        if is_edge_in_path(edge,a_path):
                            edge_loads_initial[edge]+=1
    
    # calculate initial capacity of each node using alpha factors
    node_attribs={no:{cons.LOAD:loads_initial[no]} for no in G.nodes()}
    edge_attribs={ed:{cons.LOAD:edge_loads_initial[ed]} for ed in G.edges()}
    nx.set_node_attributes(G,node_attribs)
    nx.set_edge_attributes(G,edge_attribs)

#   CASCADING EFFECTS
#   Updates component state vector with failures due to nodes disconnection
#   and overloading
def simulate_cascading_effects(G,s_nodes,c_nodes,max_iteration):
    iteration_casc=0
    component_state=0
    component_state_upd=1
    # new failures occur
    while iteration_casc<max_iteration and component_state_upd!=component_state: 
       
        component_state=component_state_upd 
        
        # DISCONNECTION FAILURE
        # assess perturbed network
        evaluate_system_loads(G,s_nodes,c_nodes)
        n_loads=nx.get_node_attributes(G,cons.LOAD)
        e_loads=nx.get_edge_attributes(G,cons.LOAD)
        n_caps=nx.get_node_attributes(G,cons.CAPACITY)
        e_caps=nx.get_edge_attributes(G,cons.CAPACITY)
        for node in G.nodes():
            #if new node load exceeds its capacity
            if n_caps[node]>cons.EPS:
                n_ratio=n_loads[node]/n_caps[node]
                if n_ratio>1:
                    #print('Casc effects nodes')
                    #reduce capacity and store de damage increment
                    n_state=1-G.nodes[node][cons.NODE_DAMAGE]
                    #update the damage level
                    G.nodes[node][cons.NODE_DAMAGE]=1-(1/n_ratio)*n_state
                    #store the damage increment
                    if n_state<cons.EPS:
                        G.nodes[node][cons.NODE_DELTADAMAGE]=n_state
                    else:
                        G.nodes[node][cons.NODE_DELTADAMAGE]=G.nodes[node][cons.NODE_DAMAGE]-(1-n_state)
        
        for edge in G.edges():
            #if new node load exceeds its capacity
            if e_caps[edge]>cons.EPS:
                e_ratio=e_loads[edge]/e_caps[edge]
                if e_ratio>1:
                    #print('Casc effects edges')
                    #reduce capacity and store de damage increment
                    e_state=1-G.edges[edge][cons.LINE_DAMAGE]
                    #update the damage level
                    G.edges[edge][cons.LINE_DAMAGE]=1-(1/e_ratio)*e_state
                    #store the damage increment
                    if e_state<cons.EPS:
                        G.edges[edge][cons.LINE_DELTADAMAGE]=e_state
                    else:
                        G.edges[edge][cons.LINE_DELTADAMAGE]=G.edges[edge][cons.LINE_DAMAGE]-(1-e_state)
        update_network(G,s_nodes,c_nodes)
        component_state_upd={cons.NODES:nx.get_node_attributes(G,cons.NODE_DAMAGE),cons.EDGES:nx.get_edge_attributes(G,cons.LINE_DAMAGE)}
        iteration_casc+=1
    #return component_state_upd
        
# estimate affectation to consumer areas

def set_state_consumers(ExposureConsumerAreas,Graph):
    areas_damage=[]
    for i in range(0,len(ExposureConsumerAreas[cons.FEATURES])):
        key_a_name=ExposureConsumerAreas[cons.FEATURES][i][cons.PROPERTIES][cons.AREA_NAME]
        if len(Graph.edges(key_a_name))>0:
            supply_edge_dam=[Graph.edges[edge][cons.LINE_DAMAGE] for edge in Graph.edges(key_a_name)]
            areas_damage.append(np.mean(supply_edge_dam))
        else:#it is an isolated consumer area
            areas_damage.append(0)
    return areas_damage

# IS AN EDGE IN A PATH?
def is_edge_in_path(edge,path):
    G=nx.Graph()
    G.add_path(path)
    if edge in G.edges():
        return True
    else:
        return False
