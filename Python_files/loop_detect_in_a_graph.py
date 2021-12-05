######################################################
# Directory for making a graph                       #
# Made by Botond Fulop                               #
######################################################

import networkx as nx
import matplotlib.pyplot as plt

def loop_detect_in_a_graph(list_of_directed_nodes,source_node,destination_node):
    #Creating a graph 
    G = nx.DiGraph()
    G.add_edges_from(list_of_directed_nodes)
    #
    #Searching for a loop in the directed graph 
    list_for_loop=[]
    for a in nx.simple_cycles(G):
        list_for_loop=a.copy()
    #Empty sequences are false
    if list_for_loop:
        print("\033[1;31;40mLoop found in the route to the destination network or address, and this is the loop:\n\033[0m",list_for_loop)
        if nx.has_path(G,source_node,destination_node):
            print("\033[1;33;40mBut this loop is not affecting this source to reach the destination.\033[0m")
        else:
            print("\033[1;31;40mThis loop is affecting this source to reach the destination.\033[0m")
    else:            
        print("\033[1;32;40mNo loop found in the route to the destination network or address.\033[0m")
        if nx.has_path(G,source_node,destination_node):
            print("\033[1;32;40mThe source has a path to the destination.\033[0m")
        else:
            print("\033[1;31;40mBut there is a tear in the route to the destination.\033[0m")
        
        
    

def plot_the_graph_of_nodes(list_of_directed_nodes):
    #Creating a graph and getting ready to plot it 
    G = nx.DiGraph()
    G.add_edges_from(list_of_directed_nodes)
    pos = nx.planar_layout(G)
    options = {"edgecolors": "black", "node_size": 800, "alpha": 1}
    nx.draw_networkx_nodes(G, pos, node_color='tab:blue',**options)
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrowsize=30, width=2, edge_color="black")
    nx.draw_networkx_labels(G, pos, font_color="whitesmoke")
    #Plot the graph           
    plt.show()


if __name__=='__main__':
    #test
    x=[('P', 'I0'), ('I0', 'I1'),('I3', 'I2'), ('I2', 'I5'), ('I5', 'C7'), ('C7', 'C6'), ('C6', 'I3'),('I4', 'C9'),('I1', 'C9')]
    loop_detect_in_a_graph(x,"P","C9")

