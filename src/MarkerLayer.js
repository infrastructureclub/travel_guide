import * as React from "react"
import L from 'leaflet'
import { Marker } from "react-leaflet";

import iconUrl from "./images/marker-icon.png"
import iconRetinaUrl from "./images/marker-icon-2x.png"
import iconUrlSelected from "./images/marker-icon-selected.png"
import iconRetinaUrlSelected from "./images/marker-icon-selected-2x.png"

export const MarkerLayer = ({ places, onSelect, selectedId }) => {
    const markers = Object.entries(places).map(([id, place]) => {
        const isSelected = id === selectedId;
        return <Marker zIndexOffset={isSelected ? 100000 : undefined} key={id} eventHandlers={{
            click: () => onSelect(id),
        }} icon={L.icon({
            iconUrl: isSelected ? iconUrlSelected : iconUrl,
            iconRetinaUrl: isSelected ? iconRetinaUrlSelected : iconRetinaUrl,
            iconSize: new L.Point(25, 41),
            iconAnchor: new L.Point(13, 41),
        })} position={[place.coordinates[1], place.coordinates[0]]} />
    });
    return <>
        {markers}
    </>
};
