import React from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  Popup,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useLocation } from "react-router-dom";

const customIcons = {
  current: new L.Icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
    iconSize: [32, 32],
  }),
  pickup: new L.Icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/green-dot.png",
    iconSize: [32, 32],
  }),
  dropoff: new L.Icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
    iconSize: [32, 32],
  }),
  fuel: new L.Icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/yellow-dot.png",
    iconSize: [32, 32],
  }),
  rest: new L.Icon({
    iconUrl: "https://maps.google.com/mapfiles/ms/icons/purple-dot.png",
    iconSize: [32, 32],
  }),
};

const MapComponent = () => {
  const location = useLocation();
  const routeData = location.state || {};
  const {
    currentLocation,
    pickupLocation,
    dropoffLocation,
    fuelStops = [],
    restStops = [],
    routeToPickup = [],
    routeToDropoff = [],
    totalMiles,
    totalDuration,
  } = routeData;

  const bounds = L.latLngBounds(
    [
      currentLocation,
      pickupLocation,
      dropoffLocation,
      ...fuelStops,
      ...restStops,
    ].map((loc) => [loc.lat, loc.lng])
  );

  return (
    <div className="w-full h-screen">
      <div className="p-4 bg-gray-100 shadow-md flex justify-between">
        <h2 className="text-lg font-bold">Trip Details</h2>
        <p>Total Miles: {parseFloat(totalMiles).toFixed(2)} miles</p>
        <p>Estimated Duration: {parseFloat(totalDuration).toFixed(2)} hours</p>
        <p>Pickup: {pickupLocation.name}</p>
        <p>Dropoff: {dropoffLocation.name}</p>
      </div>
      <MapContainer bounds={bounds} zoom={6} className="h-[85vh] w-full">
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {/* Markers */}
        <Marker
          position={[currentLocation.lat, currentLocation.lng]}
          icon={customIcons.current}
        >
          <Popup>Current Location</Popup>
        </Marker>

        <Marker
          position={[pickupLocation.lat, pickupLocation.lng]}
          icon={customIcons.pickup}
        >
          <Popup>Pickup: {pickupLocation.name}</Popup>
        </Marker>

        <Marker
          position={[dropoffLocation.lat, dropoffLocation.lng]}
          icon={customIcons.dropoff}
        >
          <Popup>Dropoff: {dropoffLocation.name}</Popup>
        </Marker>

        {fuelStops.map((stop, index) => (
          <Marker
            key={index}
            position={[stop.lat, stop.lng]}
            icon={customIcons.fuel}
          >
            <Popup>Fuel Stop - Price: ${stop.price}/gal</Popup>
          </Marker>
        ))}

        {restStops.map((stop, index) => (
          <Marker
            key={index}
            position={[stop.lat, stop.lng]}
            icon={customIcons.rest}
          >
            <Popup>Rest Stop - Amenities: {stop.amenities.join(", ")}</Popup>
          </Marker>
        ))}

        {/* Routes */}
        {routeToPickup.length > 0 && (
          <Polyline
            positions={routeToPickup}
            color="blue"
            dashArray="5, 10"
            weight={3}
          />
        )}
        {routeToDropoff.length > 0 && (
          <Polyline positions={routeToDropoff} color="green" weight={4} />
        )}
      </MapContainer>
    </div>
  );
};

export default MapComponent;
