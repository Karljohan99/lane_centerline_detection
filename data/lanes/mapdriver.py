from subprocess import Popen
import os.path
from lxml import etree
from time import sleep
import fiona
import geopandas as gpd
from shapely.geometry import Polygon


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

        for anode in nodes:
            tmp = {}
            tmp['node'] = anode
            tmp['lat'] = float(anode.get('lat'))
            tmp['lon'] = float(anode.get('lon'))
            tmp['to'] = {}
            tmp['from'] = {}

            self.nodedict.update({anode.get('id'):tmp})


        for away in ways:
            highway = 'None'
            lanes = -1
            width = -1
            layer = 0

            parking = False

            oneway = 0

            cycleway = "none"


            info_dict = {}

            for atag in away.findall('tag'):
                info_dict[atag.get('k')] = atag.get('v')

                if atag.get('k').startswith("cycleway"):
                    cycleway = atag.get('v')


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



class GeopackageMapLoader:
    def __init__(self, region, file_name, layer):
        #sub_range = f"{region[1]},{region[0]},{region[3]},{region[2]}"

        self.nodedict = {}
        self.waydict = {}
        self.roadlist = []
        self.roaddict = {}
        self.edge2edgeid = {}
        self.edgeid2edge = {}
        self.edgeProperty = {}
        self.edgeId = 0


        data = {}
        for l in fiona.listlayers(file_name):
            data[l] = gpd.read_file(file_name, layer=l)
            
        driving_lanes = data[layer][(data[layer]["type"] == "1") & (data[layer]["export_to_lanelet2"])]

        roi = driving_lanes.geometry.intersection(Polygon(region))
        roi = roi[~roi.is_empty]
        roi = roi.to_crs(4326)

        for lane in roi:
            if lane is None:
                continue
            if lane.geom_type == "MultiLineString":
                lanes = lane.geoms
                for lane in lanes:
                    for i in range(len(lane.coords)):
                        point = lane.coords[i]
                        point_id = f"{point[0]};{point[1]}"
                        
                        tmp = {}
                        tmp['lat'] = point[0]
                        tmp['lon'] = point[1]
                        tmp['to'] = {}
                        tmp['from'] = {}

                        if i > 0:
                            last_point = lane.coords[i-1]
                            last_point_id = f"{last_point[0]};{last_point[1]}"
                            tmp['from'][last_point_id] = 1

                        if i < len(lane.coords) - 1:
                            next_point = lane.coords[i+1]
                            next_point_id = f"{next_point[0]};{next_point[1]}"
                            tmp['to'][next_point_id] = 1
                        
                        if point_id in self.nodedict:
                            self.nodedict[point_id]['to'].update(tmp['to'])
                            self.nodedict[point_id]['from'].update(tmp['from'])
                        else:
                            self.nodedict.update({point_id:tmp})

            else:
                for i in range(len(lane.coords)):
                    point = lane.coords[i]
                    point_id = f"{point[0]};{point[1]}"
                    
                    tmp = {}
                    tmp['lat'] = point[0]
                    tmp['lon'] = point[1]
                    tmp['to'] = {}
                    tmp['from'] = {}

                    if i > 0:
                        last_point = lane.coords[i-1]
                        last_point_id = f"{last_point[0]};{last_point[1]}"
                        tmp['from'][last_point_id] = 1

                    if i < len(lane.coords) - 1:
                        next_point = lane.coords[i+1]
                        next_point_id = f"{next_point[0]};{next_point[1]}"
                        tmp['to'][next_point_id] = 1
                    
                    if point_id in self.nodedict:
                        self.nodedict[point_id]['to'].update(tmp['to'])
                        self.nodedict[point_id]['from'].update(tmp['from'])
                    else:
                        self.nodedict.update({point_id:tmp})



