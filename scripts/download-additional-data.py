#!/usr/bin/env python3
"""
Download additional data from Google My Maps and extract Place IDs.

This script:
1. Downloads the HTML from a Google My Maps viewer URL
2. Extracts and parses the _pageData JavaScript object
3. Finds Google Place IDs for each map item
4. Updates map.json with the extracted place IDs
"""

import re
import json
import urllib.request
import os

# Google My Maps viewer URL
MYMAPS_URL = "https://www.google.com/maps/d/viewer?mid=1wSGRzmK0rwrPnqdQAtz0p5h_NvKCjgY&ll=-3.81666561775622e-14%2C-43.436418757038496&z=1"

# Path to map.json (relative to script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_JSON_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'map.json')
PUBLIC_MAP_JSON_PATH = os.path.join(SCRIPT_DIR, '..', 'public', 'data', 'map.json')


def download_html(url):
    """Download HTML content from the given URL."""
    print(f"Downloading HTML from {url}...")
    
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    )
    
    with urllib.request.urlopen(request) as response:
        html = response.read().decode('utf-8')
    
    print(f"Downloaded {len(html)} bytes")
    return html


def extract_page_data(html):
    """
    Extract and parse the _pageData object from the HTML.
    
    The _pageData is embedded as a JavaScript string literal that contains
    a JavaScript array literal (not JSON).
    """
    print("Extracting _pageData from HTML...")
    
    # Find the _pageData assignment in the HTML
    # Pattern: var _pageData = "...";
    match = re.search(r'var _pageData\s*=\s*"(.+?)";', html, re.DOTALL)
    
    if not match:
        # Try alternative pattern without quotes (direct array)
        match = re.search(r'var _pageData\s*=\s*(\[.+?\]);', html, re.DOTALL)
        if match:
            raw_data = match.group(1)
        else:
            raise ValueError("Could not find _pageData in HTML")
    else:
        # The value is a JS string literal, need to decode escape sequences
        raw_data = match.group(1)
        # Decode common JS escape sequences
        raw_data = raw_data.encode().decode('unicode_escape')
    
    print(f"Extracted raw _pageData ({len(raw_data)} chars)")
    
    # The raw_data is a JavaScript array literal, not JSON
    # We need to convert it to valid JSON
    # Replace JavaScript-specific values with JSON equivalents
    json_data = raw_data
    
    # Handle NaN (replace with null)
    json_data = re.sub(r'\bNaN\b', 'null', json_data)
    
    # Handle undefined (replace with null)
    json_data = re.sub(r'\bundefined\b', 'null', json_data)
    
    # Handle trailing commas (invalid in JSON)
    json_data = re.sub(r',\s*]', ']', json_data)
    json_data = re.sub(r',\s*}', '}', json_data)
    
    try:
        page_data = json.loads(json_data)
        print("Successfully parsed _pageData as JSON")
        return page_data
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        # Save the raw data for debugging
        with open('debug_pagedata.txt', 'w') as f:
            f.write(json_data[:10000])  # First 10k chars
        raise


def extract_places_with_ids(page_data):
    """
    Extract place information including Google Place IDs from the parsed pageData.
    
    Based on the schema:
    - pageData[1] is the map data
    - map[6] contains layers
    - Each layer has feature details with place IDs
    """
    places = []
    
    # pageData = [meta, map]
    if len(page_data) < 2:
        print("Warning: pageData doesn't have expected structure")
        return places
    
    map_data = page_data[1]
    
    if not isinstance(map_data, list) or len(map_data) < 7:
        print("Warning: map data doesn't have expected structure")
        return places
    
    # map[6] = layers
    layers = map_data[6] if len(map_data) > 6 else []
    
    print(f"Found {len(layers)} layers")
    
    for layer_idx, layer in enumerate(layers):
        if not isinstance(layer, list):
            continue
        
        layer_name = layer[2] if len(layer) > 2 else f"Layer {layer_idx}"
        print(f"Processing layer: {layer_name}")
        
        # Look for feature details in the layer
        # The layer structure varies, so we need to search for feature records
        feature_count = 0
        
        # Recursively search for feature records in the layer
        found_features = find_feature_records(layer)
        
        for feature in found_features:
            place_info = extract_place_info(feature)
            if place_info:
                places.append(place_info)
                feature_count += 1
        
        print(f"  Found {feature_count} features with data")
    
    return places


def find_feature_records(data, depth=0):
    """
    Recursively search for feature records in the data structure.
    
    A feature record has:
    - A feature ID (string like "44A273877D20D12D")
    - Geometry (nested arrays with lat/lng)
    - Fields array containing name, description, and possibly place ID
    """
    features = []
    
    if depth > 20:  # Prevent infinite recursion
        return features
    
    if not isinstance(data, list):
        return features
    
    # Check if this looks like a feature record
    # featureRecord = [featureId, geometry, null, null, type, fields, titleTuple, numericIndex]
    if len(data) >= 6:
        # Check if first element looks like a feature ID (hex string)
        if isinstance(data[0], str) and re.match(r'^[A-F0-9]{16}$', data[0]):
            # This might be a feature record
            features.append(data)
            return features
    
    # Recurse into nested arrays
    for item in data:
        if isinstance(item, list):
            features.extend(find_feature_records(item, depth + 1))
    
    return features


def extract_place_info(feature_record):
    """
    Extract place information from a feature record.
    
    Returns dict with: name, coordinates, place_id (if available)
    """
    try:
        feature_id = feature_record[0]
        geometry = feature_record[1]
        fields = feature_record[5] if len(feature_record) > 5 else []
        
        if not isinstance(fields, list):
            return None
        
        # Extract coordinates from geometry
        lat, lng = None, None
        if isinstance(geometry, list):
            coords = find_coordinates(geometry)
            if coords:
                lat, lng = coords
        
        # Extract name, description, and place_id from fields
        name = None
        description = None
        place_id = None
        
        for field in fields:
            if not isinstance(field, list):
                continue
            
            # Field format: ['name', ['value'], 1] or ['description', ['value'], 1]
            if len(field) >= 2:
                field_name = field[0]
                
                if field_name == 'name' and isinstance(field[1], list) and len(field[1]) > 0:
                    name = field[1][0]
                elif field_name == 'description' and isinstance(field[1], list) and len(field[1]) > 0:
                    description = field[1][0]
                
                # Place ID is in a tuple like [null, 'ChIJ...', true]
                elif field_name is None and len(field) >= 3:
                    potential_place_id = field[1]
                    if isinstance(potential_place_id, str) and (
                        potential_place_id.startswith('ChIJ') or 
                        potential_place_id.startswith('Ej')
                    ):
                        place_id = potential_place_id
        
        # Also search for place_id in other parts of the fields array
        if not place_id:
            place_id = find_place_id(fields)
        
        if name:
            return {
                'feature_id': feature_id,
                'name': name,
                'description': description,
                'lat': lat,
                'lng': lng,
                'place_id': place_id
            }
        
        return None
        
    except Exception as e:
        print(f"Error extracting place info: {e}")
        return None


def find_coordinates(geometry, depth=0):
    """Find lat/lng coordinates in a nested geometry structure."""
    if depth > 10:
        return None
    
    if not isinstance(geometry, list):
        return None
    
    # Check if this is a coordinate pair [lat, lng]
    if len(geometry) == 2:
        if isinstance(geometry[0], (int, float)) and isinstance(geometry[1], (int, float)):
            lat, lng = geometry[0], geometry[1]
            # Validate ranges
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return (lat, lng)
    
    # Recurse into nested arrays
    for item in geometry:
        if isinstance(item, list):
            coords = find_coordinates(item, depth + 1)
            if coords:
                return coords
    
    return None


def find_place_id(data, depth=0):
    """Recursively search for a Google Place ID in the data structure."""
    if depth > 15:
        return None
    
    if isinstance(data, str):
        if data.startswith('ChIJ') or data.startswith('Ej'):
            return data
        return None
    
    if isinstance(data, list):
        for item in data:
            result = find_place_id(item, depth + 1)
            if result:
                return result
    
    return None


def round_coordinates(lat, lng, precision=5):
    """
    Round coordinates to specified decimal places for matching.
    
    5 decimal places = ~1.1m precision
    6 decimal places = ~11cm precision
    """
    if lat is None or lng is None:
        return None
    return (round(lat, precision), round(lng, precision))


def load_map_json():
    """Load the existing map.json file."""
    # Try public path first, then data path
    for path in [PUBLIC_MAP_JSON_PATH, MAP_JSON_PATH]:
        if os.path.exists(path):
            print(f"Loading map.json from {path}")
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f), path
    
    raise FileNotFoundError("Could not find map.json")


def update_map_json(map_data, places_with_ids, all_places, output_path):
    """
    Update map.json with extracted place IDs.
    
    Matches places by coordinates (rounded to 5 decimal places for tolerance).
    """
    print(f"\nUpdating map.json with {len(places_with_ids)} extracted places...")
    
    # Build a lookup by coordinates
    place_id_lookup = {}
    for place in places_with_ids:
        if place.get('place_id') and place.get('lat') is not None and place.get('lng') is not None:
            coords_key = round_coordinates(place['lat'], place['lng'])
            if coords_key:
                place_id_lookup[coords_key] = {
                    'place_id': place['place_id'],
                    'name': place['name']
                }
    
    print(f"Found {len(place_id_lookup)} places with Google Place IDs and coordinates")
    
    # Update the map data
    updated_count = 0
    already_has_count = 0
    not_matched_count = 0
    
    for place_id, place_data in map_data.get('places', {}).items():
        coords = place_data.get('coordinates')
        
        if coords and len(coords) >= 2:
            # map.json has [lng, lat] format (GeoJSON standard)
            lng, lat = coords[0], coords[1]
            coords_key = round_coordinates(lat, lng)
            
            if coords_key in place_id_lookup:
                google_place_id = place_id_lookup[coords_key]['place_id']
                
                if 'googlePlaceId' in place_data:
                    already_has_count += 1
                else:
                    place_data['googlePlaceId'] = google_place_id
                    updated_count += 1
            else:
                not_matched_count += 1
    
    print(f"Updated {updated_count} places with new Google Place IDs")
    print(f"Skipped {already_has_count} places that already had Place IDs")
    print(f"Could not match {not_matched_count} places by coordinates")
    
    # Save the updated map.json
    print(f"Saving updated map.json to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(map_data, f, indent=2, sort_keys=True, ensure_ascii=False)
    
    # Also update src/map.json if it exists
    src_path = os.path.join(SCRIPT_DIR, '..', 'src', 'map.json')
    if os.path.exists(src_path):
        print(f"Also updating {src_path}")
        with open(src_path, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, indent=2, sort_keys=True, ensure_ascii=False)
    
    return updated_count


def main():
    """Main entry point."""
    print("=" * 60)
    print("Google My Maps Place ID Extractor")
    print("=" * 60)
    
    # Step 1: Download HTML
    html = download_html(MYMAPS_URL)
    
    # Step 2: Extract and parse pageData
    page_data = extract_page_data(html)
    
    # Save pageData for debugging
    debug_path = os.path.join(SCRIPT_DIR, '..', 'data', 'pagedata_debug.json')
    with open(debug_path, 'w', encoding='utf-8') as f:
        json.dump(page_data, f, indent=2, ensure_ascii=False)
    
    # Step 3: Extract places with IDs
    places = extract_places_with_ids(page_data)
    
    print(f"\nExtracted {len(places)} total places from My Maps (_pageData)")
    
    places_with_ids = [p for p in places if p.get('place_id')]
    print(f"Of which {len(places_with_ids)} have Google Place IDs")
    
    # Step 4: Load and update map.json
    map_data, map_path = load_map_json()
    
    total_in_map_json = len(map_data.get('places', {}))
    print(f"\nmap.json contains {total_in_map_json} places")
    print(f"Difference: {abs(len(places) - total_in_map_json)} places")
    if len(places) > total_in_map_json:
        print(f"  (_pageData has {len(places) - total_in_map_json} more places than map.json)")
    elif total_in_map_json > len(places):
        print(f"  (map.json has {total_in_map_json - len(places)} more places than _pageData)")
    else:
        print(f"  (Both sources have the same number of places)")
    
    updated = update_map_json(map_data, places_with_ids, places, map_path)
    
    print("\n" + "=" * 60)
    print(f"Done! Updated {updated} places with Google Place IDs")
    print("=" * 60)


if __name__ == '__main__':
    main()
