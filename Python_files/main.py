######################################################
# Program to detect errors in static routing entries #
# Made by Botond Fulop                               #
######################################################

import loop_detect_in_a_graph as ld
import os
import netaddr as net

class Node():
    number_of_nodes=0
    node_names=[]

    def __init__(self, location_of_the_routing_table,node_name):
        Node.number_of_nodes+=1
        Node.node_names.append(node_name)
        self.name=node_name
        self.gateway=""
        self.up_directly_connected_networks=[]
        self.up_interface_addresses=[]
        self.static_routes_info=[]
        with open(location_of_the_routing_table, 'r') as read_obj:
            # Read all lines in the file one by one
            for line in read_obj:
                if "Gateway" in line:
                    #not set OR ip address of the gateway 
                    self.gateway=line.replace("Gateway of last resort is ","").replace(" to network 0.0.0.0", "").replace("\n","")
                elif line[0] =="C" :
                    network=line.replace("C        ","").replace("is directly connected, ","").replace("\n","")
                    network=network.split(" ",1)
                    self.up_directly_connected_networks.append(network)
                #getting the up interfaces addresses from the routing table   
                elif line[0]=="L":
                    interface_ip=line.replace("L        ","").replace("/32 is directly connected,","").replace("\n","")
                    interface_ip=interface_ip.split(" ",1)
                    self.up_interface_addresses.append(interface_ip)
                #getting the directly connected networks from the routing table
                elif line[0]=="S":
                    if line[7]!=" ":
                        static=line[6:].replace("\n","")
                        self.static_routes_info.append(static)
                    else:
                        substatic=line[9:].replace("\n","").replace(" [",subnetworkmask+" [")
                        self.static_routes_info.append(substatic)
                elif line[0] == " " and line[6]!= " ":
                    subnetwork=line.split(" is",1)[0]
                    subnetworkmask="/"+subnetwork.split("/",1)[1]
                        
      

#creating node isntances from the routing tables       
def create_node_instance(FOLDER_PATH):
    nodes_list=[]
    file_names=os.listdir(FOLDER_PATH)
    for file_name in file_names:
        x=os.path.abspath(os.path.join(FOLDER_PATH, file_name))
        split_string = file_name.split(".",1)
        node_name=split_string[0]
        nodes_list.append(Node(x,node_name))
    return nodes_list

#check if the addresses are the same or the address or network is in a network
def is_in_the_network(checked,checked_against):
    return net.IPNetwork(checked) in net.IPNetwork(checked_against)  
     
#returns the location where the interface or network is attached to
def where_is_a_network_or_address_is_connected(checked,nodes):
    location=""
    check_list=[]
    for x in range(0,Node.number_of_nodes):
        number_of_directly_connected_networks=len(nodes[x].up_directly_connected_networks)
        for y in range(0,number_of_directly_connected_networks):            
            if is_in_the_network(checked,nodes[x].up_directly_connected_networks[y][0]):
                check_list.append(nodes[x].name)
    if len(check_list)==1:
        location=check_list[0]            
        return location
    elif not check_list:
        return location
    else:
        print("\033[1;31;40mThe address or network is connected to more than one routers.\033[0m")
        return check_list

def make_the_graph_edges(source,destination,nodes,source_name,destination_name):
    edge_list=[]
    #adding the source to the list if it is attahed 
    source_connected=where_is_a_network_or_address_is_connected(source,nodes)
    if source_connected:
        edge_list.append((source_name,source_connected))
    else:
        #the source is not connected to the network
        return False
    #adding the destination to the list if it is attahed 
    destination_connected=where_is_a_network_or_address_is_connected(destination,nodes)
    if destination_connected:
        edge_list.append((destination_connected,destination_name))
    else:
        #the destination is not connected to the network
        return False
    #add the router connections
    for current_hop in range(0,Node.number_of_nodes):
        next_hop=determine_the_path(current_hop,destination)
        if next_hop == "yes":
            pass
        elif next_hop != "":
            edge_list.append((nodes[current_hop].name,next_hop))
        else:
            edge_list.append((nodes[current_hop].name,False)) 
    return edge_list


def determine_the_path(current_hop,destination):
    next_hop =""
    #check if the destination is the current hop's interface or not 
    x = has_that_interface(destination)
    if x == nodes[current_hop].name:
        return "yes"
    #check the directly connected
    #if it is in the directly connected then return an empty string because we already added it to the graph
    number_of_directly=len(nodes[current_hop].up_directly_connected_networks)
    for current_directly_connected in range(0,number_of_directly):
        if is_in_the_network(destination,nodes[current_hop].up_directly_connected_networks[current_directly_connected][0]):
            return "yes"
    # #check the static routes
    next_hop=best_static_route(current_hop,destination)
    return next_hop


#returns the name of the node that has that interface or returns False if it is not on any of the nodes
def has_that_interface(interface_ip):
    for current_node in range(0,Node.number_of_nodes):
        number_of_up_interfaces=len(nodes[current_node].up_interface_addresses)
        for current_interface in range(0,number_of_up_interfaces):
            if interface_ip == nodes[current_node].up_interface_addresses[current_interface][0]:
                return nodes[current_node].name
    return False


#finds the best static route towards the destination and returns the next hop name or an empty string in there is no route 
def best_static_route(current_hop,destination):
    best_path=""
    netmask=""
    network=""
    next_hop_address=""
    #to store the netmask network and next hop address 
    static_list=[]
    #filling up the list
    number_of_static_routes = len(nodes[current_hop].static_routes_info)
    for current_static_route in range(0,number_of_static_routes):
        #removing the exit interface if it is in the static route info
        split_str=nodes[current_hop].static_routes_info[current_static_route].split(",",1)[0]
        #getting the next hop address 
        netmask_and_network, next_hop_address=split_str.split(" via ",1)
        #getting the network and netmask
        netmask_and_network=netmask_and_network.split(" [",1)[0]
        network, netmask =netmask_and_network.split("/",1)
        #adding it to the list
        static_list.append([netmask,network,next_hop_address,netmask_and_network])

    #sorting the list so the routes with the most matching bits are in the front
    static_list.sort(reverse=True) 
    #checking the routes to have the destination in them 
    #the first match will be the best path that the packet will take to the destination 
    for i in range(0,len(static_list)):
        if is_in_the_network(destination,static_list[i][3]):
            return has_that_interface(static_list[i][2]) 
    return best_path


if __name__=='__main__':
    #ip address of the error reporter PC
    SOURCE_IP="192.168.1.2"
    SOURCE_NAME="PC-0"
    #ip address of the PC wanted to be accessed 
    DESTINATION_IP="192.168.2.100" 
    DESTINATION_NAME="PC-1"
    #paths of the routing tables
    FOLDER_PATH =[r'D:\\VillamosMernok\\Szakdolgozat\\Ansible_files\\routing_tables',
    r'D:\\VillamosMernok\\Szakdolgozat\\halozati_esetek\\1eset_R5_rossz_config\\routing_tables',
    r'D:\\VillamosMernok\\Szakdolgozat\\halozati_esetek\\2eset_R1_hurkos_statikus_route\\routing_tables',
    r'D:\\VillamosMernok\\Szakdolgozat\\halozati_esetek\\3eset_szakadas_az_utakban\\routing_tables',
    r'D:\\VillamosMernok\\Szakdolgozat\\halozati_esetek\\4eset_rossz_netmaszk\\routing_tables',
    r'D:\\VillamosMernok\\Szakdolgozat\\halozati_esetek\\5eset_csak_1iranyban_van_ut\\routing_tables',
    r'D:\\VillamosMernok\\Szakdolgozat\\halozati_esetek\\plusz_eset_tobb_routerhez_van_a_celcim\\routing_tables']
    #creating the nodes
    nodes=create_node_instance(FOLDER_PATH[3])
    print("\nNumber of nodes" , Node.number_of_nodes)
    # check the nodes and warn if they have no Gateway or static route
    print("\033[1;33;40mWARNING these nodes have no static route or gateway:\033[0m")
    for x in range(0,Node.number_of_nodes):
        if "not set" in nodes[x].gateway:
            print("\033[1;33;40mNode",nodes[x].name,"has no Gateway\033[0m")
        if not nodes[x].static_routes_info:
            print("\033[1;33;40mNode",nodes[x].name,"has no static route\033[0m")
    print()
    #check if the network or address is attached to any of the routers
    is_the_destination_on=where_is_a_network_or_address_is_connected(DESTINATION_IP,nodes)
    #check the source    
    is_the_source_on=where_is_a_network_or_address_is_connected(SOURCE_IP,nodes)
    #if the source or the destination is connected to more than one router lists the directly connected networks of those routers
    if type(is_the_destination_on)==list or type(is_the_source_on)==list :
        if type(is_the_destination_on)==list:
            print("\033[1;31;40mThe destination is connected to more than one routers:\n\033[0m",is_the_destination_on)
            for node in is_the_destination_on:
                for x in range(0,Node.number_of_nodes):
                    if nodes[x].name==node:
                        print("\n\033[0;30;47m",nodes[x].name,"\033[0m",sep="")
                        print("Directly connected networks:\n",nodes[x].up_directly_connected_networks)
        if type(is_the_source_on)==list :
            print("\033[1;31;40mThe source is connected to more than one routers:\n\033[0m",is_the_source_on)
            for node in is_the_source_on:
                for x in range(0,Node.number_of_nodes):
                    if nodes[x].name==node:
                        print("\n\033[0;30;47m",nodes[x].name,"\033[0m",sep="")
                        print("Directly connected networks:\n",nodes[x].up_directly_connected_networks)      
    else:
        if is_the_destination_on and is_the_source_on:
            print("The destination is attached to:",is_the_destination_on)
            print("The source is attached to:",is_the_source_on)
            graph_of_the_route=make_the_graph_edges(SOURCE_IP,DESTINATION_IP,nodes,SOURCE_NAME,DESTINATION_NAME)
            #print(graph_of_the_route) #prints the graph in the console#
            ld.loop_detect_in_a_graph(graph_of_the_route,SOURCE_NAME,DESTINATION_NAME)
            for x in range(0,len(graph_of_the_route)):
                if False in graph_of_the_route[x]:
                    for y in range(0,Node.number_of_nodes):
                        if nodes[y].name in graph_of_the_route[x]:
                            print("\033[0;30;47m",nodes[y].name," is the last hop before the tear.\033[0m",sep="")
                            print("This is the information about it:")
                            print("\033[0;30;47mDirectly connected networks:\033[0m\n",nodes[y].up_directly_connected_networks)
                            print("\033[0;30;47mInterfaces:\033[0m\n",nodes[y].up_interface_addresses)
                            print("\033[0;30;47mStatic routes:\033[0m\n",nodes[y].static_routes_info)
                            print("\033[0;30;47mGateway:\033[0m\n",nodes[y].gateway)
            ld.plot_the_graph_of_nodes(graph_of_the_route)
        
        #prints an error message that the destination and/or the source is not attached   
        else:
            if not is_the_destination_on:
                print("\033[1;31;40mThe destination is not connected to any of the routers.\033[0m")
                print("Check the router interface that the destination is supposed to be connected and the address and netmask of the destination!")
            if not is_the_source_on:
                print("\033[1;31;40mThe source is not connected to any of the routers.\033[0m")
                print("Check the router interface that the source is supposed to be connected and the address and netmask of the source!")
            print("Here are the interfaces and directly connected networks of the routers:")
            for x in range(0,Node.number_of_nodes):
                print("\n\033[0;30;47m",nodes[x].name,"\033[0m",sep="")
                print("Directly connected networks and the interface:\n",nodes[x].up_directly_connected_networks,sep="")
                print("\nInterfaces and their addresses:\n",nodes[x].up_interface_addresses,sep="")
                #static route and gateway info can be added if desired 
                #print("static routes\n",nodes[x].static_routes_info)
                #print("gateway\n",nodes[x].gateway)
    