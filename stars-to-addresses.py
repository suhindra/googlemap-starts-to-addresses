# -*- coding: utf-8 -*-
"""
Go to Google Bookmarks: https://www.google.com/bookmarks/

On the bottom left, click "Export bookmarks": https://www.google.com/bookmarks/bookmarks.html?hl=en

After downloading the html file, run this script on it to get the addresses

This script is based on https://gist.github.com/endolith/3896948
"""

import sys
import csv

try:
	from lxml.html import document_fromstring
except ImportError:
	print "You need to install lxml"
	sys.exit()

try:
	from geopy.geocoders import Nominatim
except ImportError:
	print "You need to install geopy"
	sys.exit()

import simplekml
import json

from urllib2 import urlopen
import re
import time

filename = r'Bookmarks.html'

def main():
    with open(filename) as bookmarks_file:
        data = bookmarks_file.read()
    
    geolocator = Nominatim()

    kml = simplekml.Kml()

    lst = list()
    
    lat_re = re.compile('markers:[^\]]*latlng[^}]*lat:([^,]*)')
    lon_re = re.compile('markers:[^\]]*latlng[^}]*lng:([^}]*)')
    coords_in_url = re.compile('\?q=(-?\d{,3}\.\d*),\s*(-?\d{,3}\.\d*)')
    
    doc = document_fromstring(data)
    import csv
    with open('GoogleBookmarks.csv','w') as f1:
        writer=csv.writer(f1, delimiter='\t',lineterminator='\n',)

        for element, attribute, url, pos in doc.body.iterlinks():
            if 'maps.google' in url:
                description = element.text or ''
                print description.encode('UTF8')
                
                if coords_in_url.search(url):
                    latitude = coords_in_url.search(url).groups()[0]
                    longitude = coords_in_url.search(url).groups()[1]
                else:
                    try:
                        sock = urlopen(url.replace(' ','+').encode('UTF8'))
                    except Exception, e:
                        print 'Connection problem:'
                        print repr(e)
                        print 'Waiting 2 minutes and trying again'
                        time.sleep(120)
                        sock = urlopen(url.replace(' ','+').encode('UTF8'))
                    content = sock.read()
                    sock.close()
                    time.sleep(3)
                    try:
                        latitude = lat_re.findall(content)[0]
                        longitude = lon_re.findall(content)[0]
                    except IndexError:
                        try:
                            lines = content.split('\n')
                            for line in lines:
                                if re.search('cacheResponse\(', line):
                                    splitline = line.split('(')[1].split(')')[0] + '"]'
                                    null = None
                                    values = eval(splitline)
                                    print values[8][0][1]
                                    longitude = str(values[0][0][1])
                                    latitude = str(values[0][0][2])
                                    continue
                        except IndexError:
                            print '[Coordinates not found]'
                            continue
                        print
                
                print latitude, longitude
                try:
        			location = geolocator.reverse(latitude+", "+longitude)
        			print(location.address)
                except ValueError:
                    print '[Invalid coordinates]'
                print
                kml.newpoint(name=description, coords=[(float(longitude), float(latitude))])
                lst.append({'latitude': latitude,
                           'longitude': longitude,
                           'name': description,
                           'url': url.encode(encoding='utf-8', errors='replace'),
                           'address': location.address.encode(encoding='utf-8', errors='replace') if location else 'error'})

                kml.save("GoogleBookmarks.kml")
                with open('GoogleBookmarks.json', mode='w') as listdump:
                    listdump.write(json.dumps(lst))
                writer.writerow(["%s, %s, %s, %s" % (description.encode('UTF8'), latitude, longitude, location.address)]) 

            sys.stdout.flush()

    kml.save("GoogleBookmarks.kml")
    with open('GoogleBookmarks.json', mode='w') as listdump:
        listdump.write(json.dumps(lst))

if __name__ == '__main__':
    main()
