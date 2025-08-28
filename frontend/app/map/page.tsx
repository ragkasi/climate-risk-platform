'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import dynamic from 'next/dynamic'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'


import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  MapPin, 
  Clock, 
  AlertTriangle, 
  TrendingUp, 
  Info,
  Play,
  Pause,
  RotateCcw,
  Layers,
  Settings,
  Search,
  Filter
} from 'lucide-react'
import { useAuth } from '@/app/providers'

// Dynamically import map component to avoid SSR issues
const MapCanvas = dynamic(
  () => import('@/components/MapCanvas'),
  { 
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-gray-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading map...</p>
        </div>
      </div>
    )
  }
)

export default function MapPage() {
  const searchParams = useSearchParams()
  const { isAuthenticated } = useAuth()
  
  // Map state
  const [center, setCenter] = useState<[number, number]>([37.7749, -122.4194]) // San Francisco
  const [zoom, setZoom] = useState(10)
  const [searchQuery, setSearchQuery] = useState('')
  
  // Risk data state
  const [riskData, setRiskData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  
  // Layer visibility
  const [layers, setLayers] = useState({
    flood: true,
    heat: true,
    smoke: true,
    pm25: true,
    uncertainty: false
  })
  
  // Time controls
  const [timeHorizon, setTimeHorizon] = useState([24]) // hours
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  
  const fetchRiskData = useCallback(async (lat: number, lon: number) => {
    setLoading(true)
    try {
      // Mock risk data - in production, call the API
      const mockRiskData = {
        grid_id: '37_-122',
        horizon: timeHorizon[0],
        predictions: [
          {
            hazard: 'flood',
            p_risk: 0.35,
            q10: 0.15,
            q50: 0.35,
            q90: 0.65,
            model: 'demo-model-v1',
            updated_at: new Date().toISOString()
          },
          {
            hazard: 'heat',
            p_risk: 0.42,
            q10: 0.20,
            q50: 0.42,
            q90: 0.75,
            model: 'demo-model-v1',
            updated_at: new Date().toISOString()
          },
          {
            hazard: 'smoke',
            p_risk: 0.18,
            q10: 0.05,
            q50: 0.18,
            q90: 0.45,
            model: 'demo-model-v1',
            updated_at: new Date().toISOString()
          },
          {
            hazard: 'pm25',
            p_risk: 0.28,
            q10: 0.10,
            q50: 0.28,
            q90: 0.55,
            model: 'demo-model-v1',
            updated_at: new Date().toISOString()
          }
        ],
        top_drivers: [
          { feature: 'precipitation_24h', contribution: 0.35 },
          { feature: 'soil_moisture', contribution: 0.28 },
          { feature: 'elevation', contribution: 0.22 },
          { feature: 'distance_to_water', contribution: 0.15 }
        ],
        brief: 'Moderate risk conditions present. Main hazard: heat with 42% probability. Stay informed.',
        sources: ['NOAA', 'USGS', 'EPA AirNow', 'NASA FIRMS']
      }
      
      setRiskData(mockRiskData)
    } catch (error) {
      console.error('Risk data fetch error:', error)
    } finally {
      setLoading(false)
    }
  }, [timeHorizon])
  
  const handleGeocode = useCallback(async (query: string) => {
    setLoading(true)
    try {
      // Mock geocoding - in production, call the API
      const mockResults = {
        'san francisco': { lat: 37.7749, lon: -122.4194 },
        'new york': { lat: 40.7128, lon: -74.0060 },
        'chicago': { lat: 41.8781, lon: -87.6298 },
        'miami': { lat: 25.7617, lon: -80.1918 },
        'seattle': { lat: 47.6062, lon: -122.3321 },
      }
      
      const result = mockResults[query.toLowerCase() as keyof typeof mockResults]
      if (result) {
        const newCenter: [number, number] = [result.lat, result.lon]
        setCenter(newCenter)
        setZoom(12)
        await fetchRiskData(result.lat, result.lon)
      }
    } catch (error) {
      console.error('Geocoding error:', error)
    } finally {
      setLoading(false)
    }
  }, [fetchRiskData])
  
  const handleSearch = useCallback(() => {
    if (searchQuery.trim()) {
      handleGeocode(searchQuery)
    }
  }, [searchQuery, handleGeocode])
  
  const toggleLayer = useCallback((layer: keyof typeof layers) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }))
  }, [])
  
  // Individual toggle functions to prevent infinite loops
  const toggleFlood = useCallback(() => setLayers(prev => ({ ...prev, flood: !prev.flood })), [])
  const toggleHeat = useCallback(() => setLayers(prev => ({ ...prev, heat: !prev.heat })), [])
  const toggleSmoke = useCallback(() => setLayers(prev => ({ ...prev, smoke: !prev.smoke })), [])
  const togglePm25 = useCallback(() => setLayers(prev => ({ ...prev, pm25: !prev.pm25 })), [])
  const toggleUncertainty = useCallback(() => setLayers(prev => ({ ...prev, uncertainty: !prev.uncertainty })), [])
  
  // Memoize slider handler to prevent infinite loops
  const handleTimeHorizonChange = useCallback((value: number[]) => {
    setTimeHorizon(value)
  }, [])
  
  // Initialize from URL params - separate effect to avoid dependency issues
  useEffect(() => {
    const search = searchParams.get('search')
    if (search) {
      setSearchQuery(search)
      // Direct geocoding without using the memoized function
      const mockResults = {
        'san francisco': { lat: 37.7749, lon: -122.4194 },
        'new york': { lat: 40.7128, lon: -74.0060 },
        'chicago': { lat: 41.8781, lon: -87.6298 },
        'miami': { lat: 25.7617, lon: -80.1918 },
        'seattle': { lat: 47.6062, lon: -122.3321 },
      }
      
      const result = mockResults[search.toLowerCase() as keyof typeof mockResults]
      if (result) {
        const newCenter: [number, number] = [result.lat, result.lon]
        setCenter(newCenter)
        setZoom(12)
        // Call fetchRiskData directly
        fetchRiskData(result.lat, result.lon)
      }
    }
  }, [searchParams, fetchRiskData])
  
  const getRiskLevel = (pRisk: number) => {
    if (pRisk < 0.3) return 'low'
    if (pRisk < 0.6) return 'moderate'
    if (pRisk < 0.8) return 'high'
    return 'extreme'
  }
  
  const getRiskColor = (pRisk: number) => {
    if (pRisk < 0.3) return 'text-green-600'
    if (pRisk < 0.6) return 'text-yellow-600'
    if (pRisk < 0.8) return 'text-red-600'
    return 'text-purple-600'
  }
  
  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Modern Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 shadow-sm">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 shadow-lg">
                  <MapPin className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Climate Risk Map</h1>
                  <p className="text-sm text-gray-500">Real-time hazard assessment</p>
                </div>
              </div>
              
              <div className="hidden md:flex items-center space-x-3 px-4 py-2 bg-gray-50 rounded-lg">
                <MapPin className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">
                  {center[0].toFixed(4)}, {center[1].toFixed(4)}
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search location..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-10 pr-4 py-2 w-64 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm"
                />
              </div>
              
              <Button 
                onClick={handleSearch} 
                disabled={loading}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-2 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  'Search'
                )}
              </Button>
              
              {isAuthenticated && (
                <Button 
                  variant="outline" 
                  className="border-gray-200 hover:bg-gray-50 px-4 py-2 rounded-xl"
                >
                  Save Location
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>
      
      <div className="flex-1 flex">
        {/* Map */}
        <div className="flex-1 relative">
          <MapCanvas
            center={center}
            zoom={zoom}
            layers={layers}
            timeHorizon={timeHorizon[0]}
            riskData={riskData}
            onCenterChange={setCenter}
            onZoomChange={setZoom}
          />
          
                  {/* Modern Map Controls */}
        <div className="absolute top-6 right-6 space-y-4">
          {/* Layers Control */}
          <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-gray-200/50 p-4 w-72">
            <div className="flex items-center space-x-2 mb-4">
              <Layers className="h-5 w-5 text-blue-600" />
              <h3 className="font-semibold text-gray-900">Risk Layers</h3>
            </div>
            <div className="space-y-3">
              {[
                { key: 'flood', label: 'Flood Risk', color: 'bg-blue-500', icon: '🌊' },
                { key: 'heat', label: 'Heat Risk', color: 'bg-orange-500', icon: '🌡️' },
                { key: 'smoke', label: 'Smoke Risk', color: 'bg-gray-500', icon: '💨' },
                { key: 'pm25', label: 'Air Quality', color: 'bg-purple-500', icon: '🌫️' },
                { key: 'uncertainty', label: 'Uncertainty', color: 'bg-yellow-500', icon: '❓' }
              ].map((layer) => (
                <div key={layer.key} className="flex items-center justify-between p-3 bg-gray-50/80 rounded-xl hover:bg-gray-100/80 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${layer.color}`}></div>
                    <span className="text-sm font-medium text-gray-700">{layer.label}</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={layers[layer.key as keyof typeof layers]}
                    onChange={layer.key === 'flood' ? toggleFlood : 
                             layer.key === 'heat' ? toggleHeat :
                             layer.key === 'smoke' ? toggleSmoke :
                             layer.key === 'pm25' ? togglePm25 : toggleUncertainty}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              ))}
            </div>
          </div>
          
          {/* Time Horizon Control */}
          <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-gray-200/50 p-4 w-72">
            <div className="flex items-center space-x-2 mb-4">
              <Clock className="h-5 w-5 text-blue-600" />
              <h3 className="font-semibold text-gray-900">Time Horizon</h3>
            </div>
            <div className="space-y-4">
              <div className="relative">
                <input
                  type="range"
                  min="1"
                  max="72"
                  step="1"
                  value={timeHorizon[0]}
                  onChange={(e) => handleTimeHorizonChange([parseInt(e.target.value)])}
                  className="w-full h-3 bg-gradient-to-r from-blue-200 to-indigo-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="absolute -top-8 left-0 right-0 flex justify-between text-xs text-gray-500">
                  <span>1h</span>
                  <span className="font-semibold text-blue-600">{timeHorizon[0]}h</span>
                  <span>72h</span>
                </div>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <Button size="sm" variant="outline" className="rounded-lg">
                  <Play className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="outline" className="rounded-lg">
                  <Pause className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="outline" className="rounded-lg">
                  <RotateCcw className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
        </div>
        
        {/* Modern Sidebar */}
        <div className="w-96 bg-white/95 backdrop-blur-md border-l border-gray-200/50 shadow-xl overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600">
                <AlertTriangle className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-lg font-bold text-gray-900">Risk Assessment</h2>
            </div>
            
            <Tabs defaultValue="risk" className="h-full">
              <TabsList className="grid w-full grid-cols-2 bg-gray-100 rounded-xl p-1">
                <TabsTrigger 
                  value="risk" 
                  className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm"
                >
                  Risk Data
                </TabsTrigger>
                <TabsTrigger 
                  value="details" 
                  className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm"
                >
                  Details
                </TabsTrigger>
              </TabsList>
            
            <TabsContent value="risk" className="mt-6 space-y-6">
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600 font-medium">Loading risk data...</p>
                </div>
              ) : riskData ? (
                <>
                  {/* Risk Summary Card */}
                  <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-lg border border-gray-200/50 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold text-gray-900">Risk Summary</h3>
                      <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                        {riskData.horizon}h horizon
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-6">Grid ID: {riskData.grid_id}</p>
                    
                    <div className="space-y-4">
                      {riskData.predictions.map((pred: any) => (
                        <div key={pred.hazard} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                              <div className={`w-4 h-4 rounded-full ${
                                getRiskLevel(pred.p_risk) === 'low' ? 'bg-green-500' :
                                getRiskLevel(pred.p_risk) === 'moderate' ? 'bg-yellow-500' :
                                getRiskLevel(pred.p_risk) === 'high' ? 'bg-red-500' : 'bg-purple-500'
                              }`} />
                              <div>
                                <div className="font-semibold text-gray-900 capitalize">{pred.hazard}</div>
                                <div className="text-xs text-gray-500">
                                  {pred.model} • {new Date(pred.updated_at).toLocaleTimeString()}
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-2xl font-bold ${getRiskColor(pred.p_risk)}`}>
                                {(pred.p_risk * 100).toFixed(0)}%
                              </div>
                              <div className="text-xs text-gray-500">
                                {pred.q10 && pred.q90 ? `${(pred.q10 * 100).toFixed(0)}-${(pred.q90 * 100).toFixed(0)}%` : ''}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Risk Brief Card */}
                  {riskData.brief && (
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl shadow-lg border border-blue-200/50 p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
                          <Info className="h-5 w-5 text-white" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-900">Risk Brief</h3>
                      </div>
                      <p className="text-gray-700 leading-relaxed">
                        {riskData.brief}
                      </p>
                    </div>
                  )}
                  
                  {/* Risk Drivers Card */}
                  <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-lg border border-gray-200/50 p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Top Risk Drivers</h3>
                    <div className="space-y-3">
                      {riskData.top_drivers.map((driver: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-white rounded-xl shadow-sm">
                          <span className="text-sm font-medium text-gray-700 capitalize">
                            {driver.feature.replace(/_/g, ' ')}
                          </span>
                          <Badge className="bg-blue-100 text-blue-700 font-semibold">
                            {(driver.contribution * 100).toFixed(0)}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-100 mx-auto mb-4">
                    <MapPin className="h-8 w-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No Risk Data</h3>
                  <p className="text-gray-600">
                    Click on the map or search for a location to see risk assessments.
                  </p>
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="details" className="mt-6 space-y-6">
              {/* Data Sources Card */}
              <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-lg border border-gray-200/50 p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Data Sources</h3>
                <div className="space-y-3">
                  {riskData?.sources?.map((source: string, index: number) => (
                    <div key={index} className="flex items-center space-x-3 p-3 bg-white rounded-xl shadow-sm">
                      <div className="w-3 h-3 bg-blue-500 rounded-full" />
                      <span className="text-sm font-medium text-gray-700">{source}</span>
                    </div>
                  )) || (
                    <p className="text-sm text-gray-500 text-center py-4">No data sources available</p>
                  )}
                </div>
              </div>
              
              {/* Model Information Card */}
              <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-lg border border-gray-200/50 p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Model Information</h3>
                <div className="space-y-4">
                  {[
                    { label: 'Grid Resolution', value: '1km' },
                    { label: 'Update Frequency', value: '15 minutes' },
                    { label: 'Prediction Horizon', value: 'Up to 72 hours' },
                    { label: 'Confidence Interval', value: '90%' }
                  ].map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-white rounded-xl shadow-sm">
                      <span className="text-sm font-medium text-gray-700">{item.label}</span>
                      <span className="text-sm font-semibold text-gray-900">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  )
}
