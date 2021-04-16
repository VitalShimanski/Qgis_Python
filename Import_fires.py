from qgis.core import *
from processing.core.Processing import Processing
Processing.initialize()
import processing


uri = "MySQL:lestorftrava,host=172.26.200.15,port=3306,user=Ompchs,password=Ompchs|layername=firecard"
layer = QgsVectorLayer( uri, "fires", "ogr" )
layer.setProviderEncoding(u'UTF-8')
layer.dataProvider().setEncoding(u'UTF-8')
QgsProject.instance().addMapLayer(layer)

#date_fire_detect_from
#date_fire_detect_to
#ft
#o
vlayer = QgsVectorLayer("?query=select * from fires where date_fire_detect >= "+
    date_fire_detect_from+" and <= "+ date_fire_detect_to+
    "and ft ="+ ft
    ,"fires_filtered","virtual")

QgsProject.instance().addMapLayer(vlayer)

   
result=processing.run("qgis:createpointslayerfromtable", {'INPUT': vlayer,
              'XFIELD': vlayer.fields()[18].name(),
              'YFIELD': vlayer.fields()[17].name(),
              'TARGET_CRS': 'EPSG:4326',
              'OUTPUT': 'TEMPORARY_OUTPUT'
              })
              

QgsProject.instance().addMapLayer(result['OUTPUT'])
print ("OK")


