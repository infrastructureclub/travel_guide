#!/usr/bin/env python3

from xml.etree import ElementTree
import re
import json

with open('./data/map.kml') as f:
    content = f.read()

#parse content as xml

tree = ElementTree.fromstring(content)
names = set()

def to_id(name):
    id = re.sub('[^0-9a-zA-Z\-\ ]+', '', name.lower())
    id = re.sub('[ -]+', '-', id)
    return id

def cleanup(text):
    text = re.sub('[\u00a0]+', ' ', text)
    text = re.sub('\u2019', '\'', text)
    text = re.sub('<br>', '\n', text)
    text = re.sub('<[^>]*>', '', text)
    return text.strip()

output = {"places": {}, "categories": {}}
for element in tree.findall('.//{http://www.opengis.net/kml/2.2}Folder'):
    category_name = element.find('.//{http://www.opengis.net/kml/2.2}name').text.strip()
    category_id = to_id(category_name)
    count = 0
    for place in element.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        count += 1
        result = {}
        result['name'] = place.find('.//{http://www.opengis.net/kml/2.2}name').text.strip()
        id = to_id(result['name'])
        i = 1
        while id in names:
            i += 1
            id = to_id(result['name']) + str(i)
            print("Duplicate id: " + result['name'] + " -> " + id)
        names.add(id)
        result['id'] = id
        result['coordinates'] = [float(e) for e in place.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.strip().split(',')[0:2]]
        if place.find('.//{http://www.opengis.net/kml/2.2}description') is not None:
            result['description'] = cleanup(place.find('.//{http://www.opengis.net/kml/2.2}description').text.strip())
        for extended in place.findall('.//{http://www.opengis.net/kml/2.2}ExtendedData/{http://www.opengis.net/kml/2.2}Data[@name="gx_media_links"]'):
            extended = extended.find('.//{http://www.opengis.net/kml/2.2}value')
            if 'img' not in result: 
                result['img'] = []
            for img in extended.text.split(' '):
                result['img'].append(img)
        result['category'] = category_id
        output['places'][id] = result
    output['categories'][category_id] = {"name": category_name, "count": count}

as_json = json.dumps(output, indent=2, sort_keys=True)
with open('./data/map.json', 'w') as f:
    f.write(as_json)

with open('./src/map.json', 'w') as f:
    f.write(as_json)

        