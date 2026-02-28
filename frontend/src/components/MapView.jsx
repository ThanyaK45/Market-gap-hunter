import { MapContainer, TileLayer, Marker, Circle, Popup, useMapEvents, useMap } from 'react-leaflet'

const DEFAULT_CENTER = [13.734469, 100.528346]

function MapController({ selectedPos }) {
  const map = useMap()
  if (selectedPos) {
    map.setView(selectedPos, 15)
  }
  return null
}

function LocationMarker({ setPos }) {
  useMapEvents({
    click(e) { setPos(e.latlng) },
  })
  return null
}

function MapView({ selectedPos, setSelectedPos, radius, result }) {
  return (
    <div className="map-wrapper">
      <MapContainer center={DEFAULT_CENTER} zoom={15} scrollWheelZoom={true}>
        <TileLayer attribution='&copy; OSM' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <LocationMarker setPos={setSelectedPos} />
        <MapController selectedPos={selectedPos} />
        
        {selectedPos && <Marker position={selectedPos}></Marker>}
        {selectedPos && <Circle center={selectedPos} radius={radius} pathOptions={{ color: 'blue', fillOpacity: 0.05 }} />}
        
        {result && result.supply_points.map((p, idx) => (
          <Circle key={`s-${idx}`} center={[p.lat, p.lon]} radius={15} pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.8 }}>
            <Popup>{p.name}</Popup>
          </Circle>
        ))}
        {result && result.demand_points.map((p, idx) => (
          <Circle key={`d-${idx}`} center={[p.lat, p.lon]} radius={8} pathOptions={{ color: 'green', fillColor: 'green', fillOpacity: 0.4, stroke: false }} />
        ))}
      </MapContainer>
    </div>
  )
}

export default MapView
