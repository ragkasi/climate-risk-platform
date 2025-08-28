'use client'

import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

interface MapCanvasProps {
  center: [number, number]
  zoom: number
  layers: {
    flood: boolean
    heat: boolean
    smoke: boolean
    pm25: boolean
    uncertainty: boolean
  }
  timeHorizon: number
  riskData: any
  onCenterChange: (center: [number, number]) => void
  onZoomChange: (zoom: number) => void
}

export default function MapCanvas({
  center,
  zoom,
  layers,
  timeHorizon,
  riskData,
  onCenterChange,
  onZoomChange
}: MapCanvasProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [isMapLoaded, setIsMapLoaded] = useState(false)

  useEffect(() => {
    if (mapContainer.current && !map.current && center && center.length === 2) {
      // Validate coordinates before initializing map
      const [lat, lng] = center
      
      if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        const mapCoords = [lng, lat] // Convert [lat, lng] to [lng, lat]
        
        map.current = new maplibregl.Map({
          container: mapContainer.current,
          style: {
            version: 8,
            sources: {
              'raster-tiles': {
                type: 'raster',
                tiles: [
                  'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
                ],
                tileSize: 256,
                attribution: '© OpenStreetMap contributors'
              }
            },
            layers: [
              {
                id: 'background',
                type: 'raster',
                source: 'raster-tiles'
              }
            ]
          },
          center: mapCoords,
          zoom: zoom
        })
      } else {
        console.error('Invalid coordinates for map initialization:', center)
        return
      }

      map.current.on('load', () => {
        setIsMapLoaded(true)
      })

      map.current.on('moveend', () => {
        if (map.current) {
          const newCenter = map.current.getCenter()
          onCenterChange([newCenter.lng, newCenter.lat])
        }
      })

      map.current.on('zoomend', () => {
        if (map.current) {
          onZoomChange(map.current.getZoom())
        }
      })
    }

    return () => {
      if (map.current) {
        map.current.remove()
        map.current = null
      }
    }
  }, [])

  // Update map center and zoom when props change
  useEffect(() => {
    if (map.current && isMapLoaded && center && center.length === 2) {
      // Validate coordinates
      const [lat, lng] = center
      
      if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        const mapCoords = [lng, lat] // Convert [lat, lng] to [lng, lat]
        map.current.setCenter(mapCoords)
        map.current.setZoom(zoom)
      } else {
        console.warn('Invalid coordinates:', center)
      }
    }
  }, [center, zoom, isMapLoaded])

  // Add risk data as markers
  useEffect(() => {
    if (!map.current || !isMapLoaded || !riskData) return

    // Clear existing markers
    const existingMarkers = document.querySelectorAll('.risk-marker')
    existingMarkers.forEach(marker => marker.remove())

    // Add new markers for each prediction
    riskData.predictions?.forEach((pred: any) => {
      if (!layers[pred.hazard as keyof typeof layers]) return

      const riskLevel = pred.p_risk < 0.3 ? 'low' : 
                       pred.p_risk < 0.6 ? 'moderate' : 
                       pred.p_risk < 0.8 ? 'high' : 'extreme'

      const color = riskLevel === 'low' ? '#10b981' :
                   riskLevel === 'moderate' ? '#f59e0b' :
                   riskLevel === 'high' ? '#ef4444' : '#8b5cf6'

      // Create marker element
      const markerEl = document.createElement('div')
      markerEl.className = 'risk-marker'
      markerEl.style.cssText = `
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: ${color};
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        cursor: pointer;
      `

      // Use the center coordinates for the marker (since we're showing risk for the current location)
      // center is [lat, lng], but MapLibre expects [lng, lat]
      const [lat, lng] = center
      if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
        console.error('Invalid coordinates for marker:', center)
        return
      }
      const markerCoords: [number, number] = [lng, lat] // [lng, lat]

      // Add click handler
      markerEl.addEventListener('click', () => {
        new maplibregl.Popup()
          .setLngLat(markerCoords)
          .setHTML(`
            <div class="p-2">
              <h3 class="font-semibold capitalize">${pred.hazard} Risk</h3>
              <p class="text-sm">Probability: ${(pred.p_risk * 100).toFixed(0)}%</p>
              <p class="text-sm">Confidence: ${pred.q10 && pred.q90 ? 
                `${(pred.q10 * 100).toFixed(0)}-${(pred.q90 * 100).toFixed(0)}%` : 'N/A'}</p>
              <p class="text-xs text-gray-500">Model: ${pred.model}</p>
            </div>
          `)
          .addTo(map.current!)
      })

      // Add marker to map
      new maplibregl.Marker(markerEl)
        .setLngLat(markerCoords)
        .addTo(map.current)
    })
  }, [riskData, layers, center, isMapLoaded])

  return (
    <div className="w-full h-full relative">
      <div ref={mapContainer} className="w-full h-full" />
      
      {/* Map controls */}
      <div className="absolute top-4 left-4 space-y-2">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-2">
          <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Time Horizon: {timeHorizon}h
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Layer legend */}
      <div className="absolute bottom-4 left-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3">
        <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Risk Levels
        </div>
        <div className="space-y-1 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-gray-600 dark:text-gray-400">Low (0-30%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span className="text-gray-600 dark:text-gray-400">Moderate (30-60%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-gray-600 dark:text-gray-400">High (60-80%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span className="text-gray-600 dark:text-gray-400">Extreme (80-100%)</span>
          </div>
        </div>
      </div>

      {/* Attribution */}
      <div className="absolute bottom-4 right-4 text-xs text-gray-500 dark:text-gray-400">
        © OpenStreetMap contributors
      </div>
    </div>
  )
}
