import traci
import time
import traci.constants as tc
import pytz
import datetime
from random import randrange
import pandas as pd

# cette fonction recupere le fuseau horaire en utc et le convertit en heure locale du pays designer
def getdatetime():
        utc_now = pytz.utc.localize(datetime.datetime.utcnow())
        # utc_now = pytz.utc.localize(datetime.timezone.utc())
        currentDT = utc_now.astimezone(pytz.timezone("Africa/Dakar"))
        #currentDT = utc_now.astimezone(pytz.timezone("Europe/Paris"))
        DATIME = currentDT.strftime("%Y-%m-%d %H:%M:%S")
        return DATIME

# cette fonction a pour but de "applatir" une liste 2D en une liste 1D
# par exemple: [[1,2],[3,4]] devient [1,2,3,4]
# Elle permet d'uniformiser les donnees extraites avant de les stocker dans un tableau
def flatten_list(_2d_list):
    flat_list = []
    for element in _2d_list:
        if type(element) is list:
            for item in element:
                flat_list.append(item)
        else:
            flat_list.append(element)
    return flat_list

# 1. lancement de la simulation
sumoCmd = ["sumo", "-c", "osm.sumocfg"]
traci.start(sumoCmd)

packVehicleData = []
packTLSData = []
packBigData = []

while traci.simulation.getMinExpectedNumber() > 0:
# getMinExpectedNumber() retoune le nombre de vehicules qui sont attendus dans la simulation
# si ce nombre est supérieur à 0, la simulation continue  
# simulationStep() avance la simulation d'un pas de temps 
        traci.simulationStep()

        # 2. Récupération des Données des Véhicules
        vehicles=traci.vehicle.getIDList() # recupere la liste des ID des vehicules
        trafficlights=traci.trafficlight.getIDList() # recupere la liste des ID des feux de circulation

        for i in range(0,len(vehicles)):

                #Function descriptions
                #https://sumo.dlr.de/docs/TraCI/Vehicle_Value_Retrieval.html
                #https://sumo.dlr.de/pydoc/traci._vehicle.html#VehicleDomain-getSpeed
                vehid = vehicles[i]  # id des vehicules
                x, y = traci.vehicle.getPosition(vehicles[i])  # position des vehicules
                coord = [x, y]
                lon, lat = traci.simulation.convertGeo(x, y)  # conversion de la position en coordonnees GPS
                gpscoord = [lon, lat]
                spd = round(traci.vehicle.getSpeed(vehicles[i])*3.6,2) # vitesse des vehicules en km/h
                edge = traci.vehicle.getRoadID(vehicles[i]) # route actuelle 
                lane = traci.vehicle.getLaneID(vehicles[i]) # voie actuelle 
                displacement = round(traci.vehicle.getDistance(vehicles[i]),2)  # distance parcourue 
                turnAngle = round(traci.vehicle.getAngle(vehicles[i]),2)  # angle de direction 
                nextTLS = traci.vehicle.getNextTLS(vehicles[i])  # prochain feu de circulation

                #Packing of all the data for export to CSV/XLSX
                # donnees de la simulation a exporter en CSV/EXCEL
                vehList = [getdatetime(), vehid, coord, gpscoord, spd, edge, lane, displacement, turnAngle, nextTLS]
                
                
                print("Vehicle: ", vehicles[i], " at datetime: ", getdatetime())
                print(vehicles[i], " >>> Position: ", coord, " | GPS Position: ", gpscoord, " |", \
                                       "Speed (Vitesse): ", round(traci.vehicle.getSpeed(vehicles[i])*3.6,2), "km/h |", \
                                      #Returns the id of the edge the named vehicle was at within the last step.
                                       " EdgeID of veh (route): ", traci.vehicle.getRoadID(vehicles[i]), " |", \
                                      #Returns the id of the lane the named vehicle was at within the last step.
                                       " LaneID of veh (voie): ", traci.vehicle.getLaneID(vehicles[i]), " |", \
                                      #Returns the distance to the starting point like an odometer.
                                       " Distance: ", round(traci.vehicle.getDistance(vehicles[i]),2), "m |", \
                                      #Returns the angle in degrees of the named vehicle within the last step.
                                       " Vehicle orientation (angle d'orientation): ", round(traci.vehicle.getAngle(vehicles[i]),2), "deg |", \
                                      #Return list of upcoming traffic lights [(tlsID, tlsIndex, distance, state), ...]
                                       " Upcoming traffic lights (prochaine feu tricolors): ", traci.vehicle.getNextTLS(vehicles[i]), \
                       )
                # recupere l'ID de la voie du vehicule i
                idd = traci.vehicle.getLaneID(vehicles[i])

                tlsList = []

                # 3. Récupération des Données des Feux Tricolores
                # recupere les donnees des feux de circulation
                for k in range(0,len(trafficlights)):

                        #Function descriptions
                        #https://sumo.dlr.de/docs/TraCI/Traffic_Lights_Value_Retrieval.html#structure_of_compound_object_controlled_links
                        #https://sumo.dlr.de/pydoc/traci._trafficlight.html#TrafficLightDomain-setRedYellowGreenState
                        
                        if idd in traci.trafficlight.getControlledLanes(trafficlights[k]):

                                tflight = trafficlights[k]  # id du feu de circulation
                                tl_state = traci.trafficlight.getRedYellowGreenState(trafficlights[k]) # etat du feu tricolore
                                tl_phase_duration = traci.trafficlight.getPhaseDuration(trafficlights[k]) # duree de la phase actuelle
                                tl_lanes_controlled = traci.trafficlight.getControlledLanes(trafficlights[k]) # voies controlees par le feu
                                tl_program = traci.trafficlight.getCompleteRedYellowGreenDefinition(trafficlights[k]) # programme complet du feu
                                tl_next_switch = traci.trafficlight.getNextSwitch(trafficlights[k]) # temps avant le prochain changement de phase

                                #Packing of all the data for export to CSV/XLSX
                                tlsList = [tflight, tl_state, tl_phase_duration, tl_lanes_controlled, tl_program, tl_next_switch]
                                
                                print(trafficlights[k], " --->", \
                                      #Returns the named tl's state as a tuple of light definitions from rRgGyYoO, for red,
                                      #green, yellow, off, where lower case letters mean that the stream has to decelerate
                                        " TL state (etat du feu): ", traci.trafficlight.getRedYellowGreenState(trafficlights[k]), " |" \
                                      #Returns the default total duration of the currently active phase in seconds; To obtain the
                                      #remaining duration use (getNextSwitch() - simulation.getTime()); to obtain the spent duration
                                      #subtract the remaining from the total duration
                                        " TLS phase duration (duree de la phase en cours): ", traci.trafficlight.getPhaseDuration(trafficlights[k]), " |" \
                                      #Returns the list of lanes which are controlled by the named traffic light. Returns at least
                                      #one entry for every element of the phase state (signal index)                                
                                        " Lanes controlled (voies controllee par le feu): ", traci.trafficlight.getControlledLanes(trafficlights[k]), " |", \
                                      #Returns the complete traffic light program, structure described under data types                                      
                                        " TLS Program (programme complete du feu): ", traci.trafficlight.getCompleteRedYellowGreenDefinition(trafficlights[k]), " |"
                                      #Returns the assumed time (in seconds) at which the tls changes the phase. Please note that
                                      #the time to switch is not relative to current simulation step (the result returned by the query
                                      #will be absolute time, counting from simulation start);
                                      #to obtain relative time, one needs to subtract current simulation time from the
                                      #result returned by this query. Please also note that the time may vary in the case of
                                      #actuated/adaptive traffic lights
                                        " Next TLS switch (temps avant la prochaine phase) ", traci.trafficlight.getNextSwitch(trafficlights[k]))

                #Pack Simulated Data
                # Ajoute les donnees de vehicule et de feu de circulation dans une liste
                packBigDataLine = flatten_list([vehList, tlsList])
                packBigData.append(packBigDataLine)


                ##----------MACHINE LEARNING CODES/FUNCTIONS HERE----------##


                ##---------------------------------------------------------------##


                ##----------CONTROL Vehicles and Traffic Lights----------##

                #***SET FUNCTION FOR VEHICLES***
                #REF: https://sumo.dlr.de/docs/TraCI/Change_Vehicle_State.html
                NEWSPEED = 15 # value in m/s (15 m/s = 54 km/hr)

                # 4. Contrôle des Véhicules et Feux Tricolores
                # ciblage specifique du vehicule veh6 et augmenter sa vitesse a 15 m/s equivalent a 54 km/h
                if vehicles[i]=='veh6':
                        traci.vehicle.setSpeedMode('veh6',0) # desactiver le mode de vitesse
                        traci.vehicle.setSpeed('veh6',NEWSPEED) # changer la vitesse du vehicule veh2


                #***SET FUNCTION FOR TRAFFIC LIGHTS***
                #REF: https://sumo.dlr.de/docs/TraCI/Change_Traffic_Lights_State.html

                ## --------------------- Real-World TL Info --------------------

                ### Green (20-60s): depends on traffic volume
                ### Yellow (3-5s): standard for driver reaction
                ### Pedestrian phase (20-30s): if applicable
                ### Red is automatically implied when the other direction is green
                ### SUMO cycles between phases in order, so correct sequencing is key

                ### You are modeling:
                ### Main road (phases 0 & 1)
                ### Side road (phases 2 & 3)
                ### Pedestrian or turn (phases 4 & 5)

                ### trafficsignal = [
                ###        "rrrrrrGGGGgGGGrr",  # Green phase for a main direction (Phase 0 - duration 30s)
                ###        "yyyyyyyyrrrrrrrr",  # Yellow phase for main direction (Phase 1 - duration 4s)
                ###        "rrrrrGGGGGGrrrrr",  # Green phase for a side direction (Phase 2 - duration 25s)
                ###        "rrrrryyyyyyrrrrr",  # Yellow phase for side direction (Phase 3 - duration 4s)
                ###        "GrrrrrrrrrrGGGGg",  # Pedestrian or turn green (Phase 4 - duration 20s)
                ###        "yrrrrrrrrrryyyyy",  # Pedestrian or turn yellow (Phase 5 - duration 4s)
                ### ]

                ##-----------------------------------------------
                # Modification de la duree de la phase etat du feu de circulation
                trafficlightduration = [30,4,25,4,20,4] # duree de la phase en secondes
                trafficsignal = ["rrrrrrGGGGgGGGrr", "yyyyyyyyrrrrrrrr", "rrrrrGGGGGGrrrrr", "rrrrryyyyyyrrrrr", "GrrrrrrrrrrGGGGg", "yrrrrrrrrrryyyyy"]
                #tfl = "cluster_4260917315_5146794610_5146796923_5146796930_5704674780_5704674783_5704674784_5704674787_6589790747_8370171128_8370171143_8427766841_8427766842_8427766845"
                tfl="cluster_1247665033_1247665351_1247665381_5567115953_#1more"
                traci.trafficlight.setPhaseDuration(tfl, trafficlightduration[randrange(6)])
                traci.trafficlight.setRedYellowGreenState(tfl, trafficsignal[randrange(6)])
                ##------------------------------------------------------


traci.close()

#Generate Excel and CSV file
columnnames = ['dateandtime', 'vehid', 'coord', 'gpscoord', 'spd', 'edge', 'lane', 'displacement', 'turnAngle', 'nextTLS', \
                       'tflight', 'tl_state', 'tl_phase_duration', 'tl_lanes_controlled', 'tl_program', 'tl_next_switch']
dataset = pd.DataFrame(packBigData, index=None, columns=columnnames)
dataset.to_excel("output.xlsx", index=False)
dataset.to_csv("output.csv", index=False)
time.sleep(5)








