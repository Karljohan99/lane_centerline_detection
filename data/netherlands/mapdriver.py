from subprocess import Popen
import os.path
from lxml import etree
from time import sleep


class OSMLoader:
    def __init__(self, region, noUnderground = False, osmfile=None, includeServiceRoad = False):
        
        sub_range = f"{region[1]},{region[0]},{region[3]},{region[2]}"
        #sub_range = str(region[1])+","+str(region[0])+","+str(region[3])+","+str(region[2])

        if osmfile is None:
            while not os.path.exists("tmp/map?bbox="+sub_range):
                Popen("wget http://overpass-api.de/api/map?bbox="+sub_range, shell = True).wait()
                Popen("mv \"map?bbox="+sub_range+"\" tmp/", shell = True).wait()
                if not os.path.exists("tmp/map?bbox="+sub_range):
                    print("Error. Wait for one minitue")
                    sleep(60)   

            filename = "tmp/map?bbox="+sub_range

        else:
            filename = osmfile


        roadForMotorDict = {'motorway','trunk','primary','secondary','tertiary','residential'}
        roadForMotorBlackList = {'None','pedestrian','footway','bridleway','steps','path','sidewalk','cycleway',
                                 'proposed','construction','bus_stop','crossing','elevator','emergency_access_point',
                                 'escape','give_way','platform','track','service'}

        xml_parser = etree.XMLParser(recover=True)
        mapxml = etree.parse(filename, xml_parser).getroot()

        nodes = mapxml.findall('node')
        ways = mapxml.findall('way')
        #relations = mapxml.findall('relation')

        self.nodedict = {}
        self.waydict = {}
        self.roadlist = []
        self.roaddict = {}
        self.edge2edgeid = {}
        self.edgeid2edge = {}
        self.edgeProperty = {}
        self.edgeId = 0
        way_c = 0


        #self.minlat = float(mapxml.find('bounds').get('minlat'))
        #self.maxlat = float(mapxml.find('bounds').get('maxlat'))    
        #self.minlon = float(mapxml.find('bounds').get('minlon'))
        #self.maxlon = float(mapxml.find('bounds').get('maxlon'))

        for anode in nodes:
            tmp = {}
            tmp['node'] = anode
            tmp['lat'] = float(anode.get('lat'))
            tmp['lon'] = float(anode.get('lon'))
            tmp['to'] = {}
            tmp['from'] = {}

            self.nodedict.update({anode.get('id'):tmp})


        #self.buildings = []

        for away in ways:
            #nds = away.findall('nd')
            highway = 'None'
            lanes = -1
            width = -1
            layer = 0

            #hasLane = False
            #hasWidth = False

            parking = False

            oneway = 0

            #isBuilding = False

            #building_height = 6

            cycleway = "none"


            info_dict = {}

            for atag in away.findall('tag'):
                info_dict[atag.get('k')] = atag.get('v')

                if atag.get('k').startswith("cycleway"):
                    cycleway = atag.get('v')

                if atag.get('k') == 'building':
                    #if atag.get('v') == "yes":
                        #print("find buildings")
                    isBuilding = True


                if atag.get('k') == 'highway':
                    highway = atag.get('v')
                if atag.get('k') == 'lanes':
                    try:
                        lanes = float(atag.get('v').split(';')[0])
                    except ValueError:
                        lanes = -1 

                    hasLane = True
                if atag.get('k') == 'width':
                    #print(atag.get('v'))
                    try:
                        width = float(atag.get('v').split(';')[0].split()[0])
                    except ValueError:

                        width == -1

                    hasWidth = True
                if atag.get('k') == 'layer':
                    try:
                        layer = int(atag.get('v'))
                    except ValueError:
                        print("ValueError for layer", atag.get('v'))
                        layer = -1

                if atag.get('k') == 'amenity':
                    if atag.get('v') == 'parking':
                        parking = True

                if atag.get('k') == 'service':
                    if atag.get('v') == 'parking_aisle':
                        parking = True

                if atag.get('k') == 'service':
                    if atag.get('v') == 'driveway':
                        parking = True

                if atag.get('k') == 'oneway':
                    if atag.get('v') == 'yes':
                        oneway = 1
                    if atag.get('v') == '1':
                        oneway = 1
                    if atag.get('v') == '-1':
                        oneway = -1

                """
                if atag.get('k') == 'height':
                    try:
                        building_height = float(atag.get('v').split(' ')[0])
                    except ValueError:
                        print(atag.get('v'))


                if atag.get('k') == 'ele':
                    try:
                        building_height = float(atag.get('v').split(' ')[0]) * 3
                    except ValueError:
                        print(atag.get('v'))
                """

            if width == -1 :
                if lanes == -1 :
                    width = 6.6
                else :
                    if lanes == 1:
                        width = 6.6
                    else:
                        width = 3.7 * lanes

            if lanes != -1:
                if width > lanes * 3.7 * 2:
                    width = width / 2
                if lanes == 1:
                    width = 6.6
                else:
                    width = lanes * 3.7

            if noUnderground:
                if layer < 0 :
                    continue 


            """
            if isBuilding :
                idlink = []
                for anode in away.findall('nd'):
                    refid = anode.get('ref')
                    idlink.append(refid)

                    self.buildings.append([[(self.nodedict[x]['lat'],self.nodedict[x]['lon']) for x in idlink],building_height])
            """


            #if highway in roadForMotorDict: #and hasLane and hasWidth and fromMassGIS: 
            #if highway not in roadForMotorBlackList:
            #if highway in roadForMotorDict:

            #if highway not in roadForMotorBlackList and parking == False:
            if highway not in roadForMotorBlackList and (includeServiceRoad == True or parking == False): # include parking roads!
            
                idlink = []
                for anode in away.findall('nd'):
                    refid = anode.get('ref')
                    idlink.append(refid)

                for i in range(len(idlink)-1):
                    link1 = (idlink[i], idlink[i+1])
                    link2 = (idlink[i+1], idlink[i])

                    if link1 not in self.edge2edgeid.keys():
                        self.edge2edgeid[link1] = self.edgeId
                        self.edgeid2edge[self.edgeId] = link1
                        self.edgeProperty[self.edgeId] = {"width":width, "lane":lanes, "layer":layer, "roadtype": highway, "cycleway":cycleway, "info":dict(info_dict)}
                        self.edgeId += 1

                    if link2 not in self.edge2edgeid.keys():
                        self.edge2edgeid[link2] = self.edgeId
                        self.edgeid2edge[self.edgeId] = link2
                        self.edgeProperty[self.edgeId] = {"width":width, "lane":lanes, "layer":layer, "roadtype": highway, "cycleway":cycleway, "info":dict(info_dict)}
                        self.edgeId += 1


                if oneway >= 0:
                    for i in range(len(idlink)-1):
                        self.nodedict[idlink[i]]['to'][idlink[i+1]] = 1
                        self.nodedict[idlink[i+1]]['from'][idlink[i]] = 1

                    self.waydict[way_c] = idlink
                    way_c += 1
                    
                idlink.reverse()

                if oneway == -1:
                    for i in range(len(idlink)-1):
                        self.nodedict[idlink[i]]['to'][idlink[i+1]] = 1
                        self.nodedict[idlink[i+1]]['from'][idlink[i]] = 1

                    self.waydict[way_c] = idlink
                    way_c += 1

                if oneway == 0:
                    for i in range(len(idlink)-1):
                        self.nodedict[idlink[i]]['to'][idlink[i+1]] = 1
                        self.nodedict[idlink[i+1]]['from'][idlink[i]] = 1



