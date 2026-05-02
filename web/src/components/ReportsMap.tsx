import { GoogleMap, useJsApiLoader, Marker, InfoWindow } from '@react-google-maps/api';
import { useState, useMemo, useCallback } from 'react';
import { Report } from '../types';

const containerStyle = {
  width: '100%',
  height: '100%'
};

const DEFAULT_CENTER = {
  lat: 31.9539,
  lng: 35.9106
};

const SEVERITY_COLORS: Record<string, string> = {
  low: '#7dd3a6',
  medium: '#d7ff64',
  high: '#f59e0b',
  critical: '#ef4444',
};

function formatLabel(value?: string) {
  if (!value) return 'Unknown';
  return value.split('_').map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
}

export default function ReportsMap({ reports }: { reports: Report[] }) {
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: "AIzaSyA8YRxFBluIvHiVSgQwxGM1_Kd3S1-UHy4"
  });

  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  const onLoad = useCallback(function callback(mapInstance: google.maps.Map) {
    if (reports.length === 0) {
      mapInstance.setCenter(DEFAULT_CENTER);
      mapInstance.setZoom(8);
    } else {
      const bounds = new window.google.maps.LatLngBounds();
      reports.forEach((report) => {
        bounds.extend({
          lat: report.latitude,
          lng: report.longitude
        });
      });
      mapInstance.fitBounds(bounds);
      if (reports.length === 1) {
        mapInstance.setZoom(14);
      }
    }
    setMap(mapInstance);
  }, [reports]);

  const onUnmount = useCallback(function callback() {
    setMap(null);
  }, []);

  // Update bounds if reports change
  useMemo(() => {
    if (map && reports.length > 0) {
      const bounds = new window.google.maps.LatLngBounds();
      reports.forEach((report) => {
        bounds.extend({
          lat: report.latitude,
          lng: report.longitude
        });
      });
      map.fitBounds(bounds);
      if (reports.length === 1) {
        map.setZoom(14);
      }
    } else if (map && reports.length === 0) {
      map.setCenter(DEFAULT_CENTER);
      map.setZoom(8);
    }
  }, [reports, map]);

  return isLoaded ? (
      <GoogleMap
        mapContainerStyle={containerStyle}
        center={DEFAULT_CENTER}
        zoom={8}
        onLoad={onLoad}
        onUnmount={onUnmount}
        options={{
          styles: [
            { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
            {
              featureType: "administrative.locality",
              elementType: "labels.text.fill",
              stylers: [{ color: "#d59563" }],
            },
            {
              featureType: "poi",
              elementType: "labels.text.fill",
              stylers: [{ color: "#d59563" }],
            },
            {
              featureType: "poi.park",
              elementType: "geometry",
              stylers: [{ color: "#263c3f" }],
            },
            {
              featureType: "poi.park",
              elementType: "labels.text.fill",
              stylers: [{ color: "#6b9a76" }],
            },
            {
              featureType: "road",
              elementType: "geometry",
              stylers: [{ color: "#38414e" }],
            },
            {
              featureType: "road",
              elementType: "geometry.stroke",
              stylers: [{ color: "#212a37" }],
            },
            {
              featureType: "road",
              elementType: "labels.text.fill",
              stylers: [{ color: "#9ca5b3" }],
            },
            {
              featureType: "road.highway",
              elementType: "geometry",
              stylers: [{ color: "#746855" }],
            },
            {
              featureType: "road.highway",
              elementType: "geometry.stroke",
              stylers: [{ color: "#1f2835" }],
            },
            {
              featureType: "road.highway",
              elementType: "labels.text.fill",
              stylers: [{ color: "#f3d19c" }],
            },
            {
              featureType: "transit",
              elementType: "geometry",
              stylers: [{ color: "#2f3948" }],
            },
            {
              featureType: "transit.station",
              elementType: "labels.text.fill",
              stylers: [{ color: "#d59563" }],
            },
            {
              featureType: "water",
              elementType: "geometry",
              stylers: [{ color: "#17263c" }],
            },
            {
              featureType: "water",
              elementType: "labels.text.fill",
              stylers: [{ color: "#515c6d" }],
            },
            {
              featureType: "water",
              elementType: "labels.text.stroke",
              stylers: [{ color: "#17263c" }],
            },
          ],
          disableDefaultUI: true,
          zoomControl: true,
        }}
      >
        {reports.map((report) => {
          const color = SEVERITY_COLORS[report.severity] || '#34d399';
          
          return (
            <Marker
              key={report.id}
              position={{
                lat: report.latitude,
                lng: report.longitude
              }}
              icon={{
                path: window.google.maps.SymbolPath.CIRCLE,
                fillColor: color,
                fillOpacity: 1,
                strokeColor: 'rgba(15, 23, 42, 0.92)',
                strokeWeight: 3,
                scale: 10,
              }}
              onClick={() => setSelectedReport(report)}
            />
          );
        })}

        {selectedReport && (
          <InfoWindow
            position={{
              lat: selectedReport.latitude,
              lng: selectedReport.longitude
            }}
            onCloseClick={() => setSelectedReport(null)}
          >
            <div className="min-w-[180px] space-y-2 text-sm text-slate-800 p-1">
              <p className="text-base font-semibold text-slate-900">
                {formatLabel(selectedReport.category)}
              </p>
              <div className="space-y-1 text-slate-600">
                <p>Status: {formatLabel(selectedReport.status)}</p>
                <p>Severity: {formatLabel(selectedReport.severity)}</p>
                <p>
                  Reported: {new Date(selectedReport.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
  ) : <></>;
}
