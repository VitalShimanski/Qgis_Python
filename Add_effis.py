from qgis.core import QgsRasterLayer, QgsProject
import requests


url="url=https://ies-ows.jrc.ec.europa.eu/effis?"

request="request=GetMap&"
service="service=wms&"
ver="version=1.1.1&"
single="singletile=false&"
transp="transparent=true&"
layers="layers=ecmwf007.fwi&"
format="format=image/tiff&"
styles="styles&"
srs="srs=EPSG:4326&"
crs="crs=EPSG:4326&"
width="width=596&"
height="height=330&"
bbox="BBOX=-35.0,25.0,50.0,72.0"
time="TIME=2020-07-28&"

urlWithParams = url+request+service+ver+single+transp+layers+format+styles+srs+crs+width+height+bbox+time
print (urlWithParams)

raster_layer = QgsRasterLayer(urlWithParams, 'FWI', 'wms')
if not raster_layer.isValid():
  print("Layer failed to load!")
else:
    QgsProject.instance().addMapLayer(raster_layer)
    
    
