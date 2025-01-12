# -*- coding: utf-8 -*-
"""
Python module for system reliability. Contains the functions directly called by the main file:
    - Load Network Data: Creates a graph object based on the line exposure and node damage information (i.e. prob. of failure). 
    Network fragility defines which node taxonomy corresponds to source and consumer nodes
    - Evaluate System Loads: estimates the loads at nodes and edges, based on shortest path algorithm between source and consumer nodes
    - Assign Initial Capacities: assign capacities to nodes and edges based on precomputed loads and a given safety factor
    - Monte Carlo Simulation: simulates the hazard action and cascading effects for multiple random nodal damage states
    - Compute output: based on the samples, returns sample of global values (total affected population) and probability of affectation for 
    each consumer area

Created on Tue Aug 13 10:52:00 2019

@author: hfrv2
"""

import numpy as np
import networkx as nx
import copy
import Constants as cons
import Netsim as ns
##### ----------------------------- Functions called in the main file ---------------------------------########

'''Create the graph from geojson files''' 
def load_network_data(DamageNodes,ExposureLines,NetworkFragility):
    G=nx.Graph()#initialize graph
    EdgesFea=ExposureLines[cons.FEATURES]#extract edge features
    NodesFea=DamageNodes[cons.FEATURES] #extract node features
    #Initialize attributes for nodes and edges
    NodeBunch={NodesFea[i][cons.PROPERTIES][cons.NODE_NAME]:{
            cons.TAXONOMY:'',
            cons.COORDINATES:NodesFea[i][cons.GEOMETRY][cons.COORDINATES],
            cons.NODE_DAMAGE:0.0,
            cons.NODE_DELTADAMAGE:0.0,
            cons.NODE_POF:0.0
            } for i in range(0,len(NodesFea))}
    EdgeBunch=[(EdgesFea[i][cons.PROPERTIES][cons.FROM],EdgesFea[i][cons.PROPERTIES][cons.TO],{
            cons.LINE_NAME:'',
            cons.LENGTH:1.0,
            cons.COORDINATES:EdgesFea[i][cons.GEOMETRY][cons.COORDINATES],
            cons.VOLTAGE:1.0,
            cons.WEIGHT:1.0,
            cons.RESISTANCE:1.0,
            cons.REACTANCE:1.0,
            cons.LINE_DAMAGE:0.0,
            cons.LINE_DELTADAMAGE:0.0,
            cons.LOAD:1.0,
            cons.CAPACITY:1.0
            }) for i in range(0,len(EdgesFea))]
    # add edges to G (nodes are initialized too, without attributes)
    G.add_edges_from(EdgeBunch)
    del EdgeBunch# save memory
    # add attributes to the initialized nodes     
    nx.set_node_attributes(G,NodeBunch)
    #set node attributes (only from 'properties' key)
    for attr in NodesFea[0][cons.PROPERTIES].keys():
        if attr==cons.NODE_NAME:
           continue
        NodeAttr={NodesFea[i][cons.PROPERTIES][cons.NODE_NAME]:{attr:NodesFea[i][cons.PROPERTIES][attr]} for i in range(0,len(NodesFea))}
        nx.set_node_attributes(G,NodeAttr)
    #set edge attributes (only from 'properties' key)
    for attr in EdgesFea[0][cons.PROPERTIES].keys():
        EdgeAttr={(EdgesFea[i][cons.PROPERTIES][cons.FROM],EdgesFea[i][cons.PROPERTIES][cons.TO]):{attr:EdgesFea[i][cons.PROPERTIES][attr]} for i in range(0,len(EdgesFea))}
        nx.set_edge_attributes(G,EdgeAttr)
    #update the weights; depending on available data 
    EdgeWeights={}
    #try the desired case: weightL*X, (L*sqrt(R^2+X^2), R<<X), R: resistance, X: reactance
    try:
        #EdgeWeights={(EdgesFea[i][cons.PROPERTIES][cons.FROM],EdgesFea[i][cons.PROPERTIES][cons.TO]):
            #{cons.WEIGHT:float(EdgesFea[i][cons.PROPERTIES][cons.LENGTH])*
            # np.sqrt((float(EdgesFea[i][cons.PROPERTIES][cons.REACTANCE])**2+
             #         float(EdgesFea[i][cons.PROPERTIES][cons.RESISTANCE])**2))} for i in range(0,len(EdgesFea))}
        EdgeWeights={(EdgesFea[i][cons.PROPERTIES][cons.FROM],EdgesFea[i][cons.PROPERTIES][cons.TO]):
                {cons.WEIGHT:float(EdgesFea[i][cons.PROPERTIES][cons.LENGTH])*
                 float(EdgesFea[i][cons.PROPERTIES][cons.REACTANCE])} for i in range(0,len(EdgesFea))}
    except:
        #otherwise, try just with the resistance: weight=L*R
        try:
            EdgeWeights={(EdgesFea[i][cons.PROPERTIES][cons.FROM],EdgesFea[i][cons.PROPERTIES][cons.TO]):
                {cons.WEIGHT:float(EdgesFea[i][cons.PROPERTIES][cons.LENGTH])*
                 float(EdgesFea[i][cons.PROPERTIES][cons.RESISTANCE])} for i in range(0,len(EdgesFea))}
        #otherwise, just assume weight~length/voltage
        except:
            EdgeWeights={(EdgesFea[i][cons.PROPERTIES][cons.FROM],EdgesFea[i][cons.PROPERTIES][cons.TO]):
                {cons.WEIGHT:float(EdgesFea[i][cons.PROPERTIES][cons.LENGTH])/(float(EdgesFea[i][cons.PROPERTIES][cons.VOLTAGE]))} for i in range(0,len(EdgesFea))}
    nx.set_edge_attributes(G,EdgeWeights)
    # create a dictionary of node lists by taxonomy
    Types=nx.get_node_attributes(G,cons.NODE_TYPE)
    source=NetworkFragility[cons.META][cons.SOURCE]
    terminal=NetworkFragility[cons.META][cons.TERMINAL]
    s_nodes=[nod for nod in G.nodes() if Types[nod] in source]
    t_nodes=[nod for nod in G.nodes() if Types[nod] in terminal]
    return G,s_nodes,t_nodes

'''evaluation of system loads
load is computed as the number of shortest paths that pass through the component (node or edge)'''
def evaluate_system_loads(G,s_nodes,t_nodes):
    ns.evaluate_system_loads(G,s_nodes,t_nodes)

'''Assign component capacities'''
def assign_initial_capacities(G,alpha):
    node_caps={no:{cons.CAPACITY:alpha*G.nodes[no][cons.LOAD]} for no in G.nodes()}
    edge_caps={ed:{cons.CAPACITY:alpha*G.edges[ed][cons.LOAD]} for ed in G.edges()}
    nx.set_node_attributes(G,node_caps)
    nx.set_edge_attributes(G,edge_caps)

'''MONTE CARLO SIMULATION''' 
def run_Monte_Carlo_simulation(Graph,s_nodes0,t_nodes0,ExposureConsumerAreas,mcs):
    #component_state_dha=[]
    #component_state_idp=[]
    #store samples of affected areas in a list
    affected_areas=[]
    max_iteration=5#max number of iterations in simulation of cascading effects
    # here starts the MCS
    for i in range(0,mcs):
        i_component_state_dha={}
        #i_component_state_casc={}
        #modify the network in a copy
        NetG=copy.deepcopy(Graph)
        #likewise for the source and terminal list
        s_nodes=copy.deepcopy(s_nodes0)
        t_nodes=copy.deepcopy(t_nodes0)
        ## Direct Hazard Action
        # Simulate effects of hazard action on components
        ns.direct_hazard_action(NetG)
        
        # store coponent damage states
        i_component_state_dha={cons.NODES:nx.get_node_attributes(NetG,cons.NODE_DAMAGE),cons.EDGES:nx.get_edge_attributes(NetG,cons.LINE_DAMAGE)}
        #component_state_dha.append(i_component_state_dha)
        
        # Update network description: weights and capacities, and remove damaged nodes from source and terminal lists
        ns.update_network(NetG,s_nodes,t_nodes)    

        # if at least one component has significant damage, we simulate cascading effects
        if max(i_component_state_dha[cons.NODES].values())>cons.MIN_DAMAGE or max(i_component_state_dha[cons.EDGES].values())>cons.MIN_DAMAGE:
            #i_component_state_casc=i_component_state_dha
            ## Damage Propagation
            # if there are surviving source and terminal nodes
            if len(s_nodes)>0 and len(t_nodes)>0:
                # cascading effects
                ns.simulate_cascading_effects(NetG,s_nodes,t_nodes,max_iteration)
            #otherwise, loss of functionality, i.e. no more flow in network
            # in any case, update the network
            ns.update_network(NetG,s_nodes,t_nodes)                         
                  
        # otherwise, no disconnection or cascading failures in this network              
            
        # Save Results (here the consumer areas)
        #component_state_idp.append(i_component_state_casc)
        i_affected_areas=ns.set_state_consumers(ExposureConsumerAreas,NetG)
        affected_areas.append(i_affected_areas)
        print("MCS iteration: "+str(i))
                     
    return affected_areas


#Post Processing: transform damaged areas into affected population
def compute_output(SampleDamageAreas,ExposureConsumerAreas,nmcs):
    SampleDamageNetwork=[int(np.sum([SampleDamageAreas[i][i_area]*ExposureConsumerAreas[cons.FEATURES][i_area][cons.PROPERTIES][cons.AREA_POPULATION]
    for i_area in range(0,len(SampleDamageAreas[0]))])) for i in range(0,nmcs)]
    for i_area in range(0,len(ExposureConsumerAreas[cons.FEATURES])):
        est_apof=np.mean([SampleDamageAreas[i][i_area]for i in range(0,nmcs)])
        ExposureConsumerAreas[cons.FEATURES][i_area][cons.PROPERTIES][cons.AREA_POF]=est_apof
    return ExposureConsumerAreas,SampleDamageNetwork