from owslib.wms import WebMapService
from osgeo import gdal, osr
import processing

url='https://ies-ows.jrc.ec.europa.eu/effis?'
folder = '~/output'
wms = WebMapService(url, version='1.1.1')
wms_layers= list(wms.contents)

print (wms[wms_layers[35]])
#for layerno in range(0,len(wms_layers)):
#    print (layerno)

raw_tiff=os.path.join(folder,'_raw'+str('ecmwf007')+'.tif')

img = wms.getmap(layers='ecmwf.fwi', styles='', srs='EPSG:4326', bbox=(-35.0,25.0,50.0,72.0),singletile='false', transparent='true', size=(596, 330), format='image/tiff' , time = '2020-07-28')
out = open(raw_tiff, 'wb')
out.write(img.read())
out.close()
out = None