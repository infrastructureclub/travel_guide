import * as React from "react"
import { MapContainer, TileLayer } from "react-leaflet"
import 'leaflet/dist/leaflet.css';
import { MarkerLayer } from "./MarkerLayer";
import mapData from "./map.json";
import {useHash} from './useHash.js';
import './App.css';
import Linkify from 'react-linkify';

const {places, categories} = mapData;

export const App = () => {

  const [categoryFilters, setCategoryFilters] = React.useState(Object.keys(categories));
  const filteredPlaces = React.useMemo(() => Object.fromEntries(
    Object.entries(places).filter(([k, p]) => categoryFilters.includes(p.category))
  ), [categoryFilters]);
  const [selectedId, setSelectedId] = useHash();
  const selected = (selectedId && selectedId !== '') ? places[selectedId] : null;
  const initialViewport = React.useMemo(() => {
    if (selected) {
      return {center: [selected.coordinates[1], selected.coordinates[0]], zoom: 12};
    }
    return {center: [51.505, -0.09], zoom: 2};
  }, [selected]);
  return (
    <main className="page">
      <MapContainer className="map" {...initialViewport} scrollWheelZoom={true}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MarkerLayer selectedId={selectedId} places={filteredPlaces} onSelect={setSelectedId} />
      </MapContainer>
      <div className="panel">
        {selected === null ?
          <>
            <h1>Infrastructure Club Travel Guide</h1>
            {Object.entries(categories).map(([id, category]) =>
              <div key={id}>
                <input type="checkbox" name={id} id={id} checked={categoryFilters.includes(id)} onChange={e => {
                  setCategoryFilters(filters => e.target.checked ? [...filters, id] : filters.filter(f => f !== id))
                }} />
                <label htmlFor={id}>{category.name} ({category.count})</label>
              </div>)}
          </>
          : <>
            <button className="back-link" onClick={() => setSelectedId(null)}>&lt; back to categories</button>
            <h1>{selected.name}</h1>
            <p><Linkify>{selected.description}</Linkify></p>
            {selected.img && selected.img.map(url => <img alt="User provided" className="place-image" src={url} />)}
          </>}
      </div>
    </main>
  )
}
