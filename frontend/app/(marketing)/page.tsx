'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { MapPin, Shield, AlertTriangle, TrendingUp, Users, Globe, ArrowRight, CheckCircle, BarChart3, Zap } from 'lucide-react'
import { useAuth } from '@/app/providers'

export default function LandingPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const { isAuthenticated } = useAuth()

  const handleSearch = () => {
    if (searchQuery.trim()) {
      window.location.href = `/map?search=${encodeURIComponent(searchQuery)}`
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-700">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <div>
                <span className="text-xl font-semibold text-gray-900">Climate Risk Lens</span>
                <p className="text-xs text-gray-500">Risk Assessment Platform</p>
              </div>
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <Link href="/map" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                Map
              </Link>
              <Link href="/sites" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                Sites
              </Link>
              <Link href="/alerts" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                Alerts
              </Link>
              {isAuthenticated ? (
                <Link href="/dashboard" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                  Dashboard
                </Link>
              ) : (
                <Button variant="outline" size="sm" className="text-sm">
                  Sign In
                </Button>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] -z-10" />
        <div className="container mx-auto px-6 py-24">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-8">
              <Badge variant="secondary" className="mb-4 px-4 py-2 text-sm font-medium">
                <Zap className="mr-2 h-4 w-4" />
                Real-time Climate Risk Assessment
              </Badge>
              <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl lg:text-7xl">
                Forecast Local
                <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent"> Climate Hazards</span>
              </h1>
              <p className="mt-6 text-xl leading-8 text-gray-600 max-w-3xl mx-auto">
                Advanced machine learning models provide accurate, localized risk predictions for flooding, 
                extreme heat, wildfire smoke, and air quality with actionable insights for your community.
              </p>
            </div>
            
            {/* Search Bar */}
            <div className="mx-auto max-w-2xl mb-12">
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <MapPin className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                  <Input
                    type="text"
                    placeholder="Enter address or city name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="h-14 pl-12 pr-4 text-lg border-2 border-gray-200 focus:border-blue-500 focus:ring-0"
                  />
                </div>
                <Button 
                  onClick={handleSearch} 
                  size="lg" 
                  className="h-14 px-8 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                >
                  <ArrowRight className="mr-2 h-5 w-5" />
                  Search
                </Button>
              </div>
            </div>

            {/* Demo Cities */}
            <div className="flex flex-wrap justify-center gap-3">
              <span className="text-sm text-gray-500">Try:</span>
              {['San Francisco', 'New York', 'Chicago', 'Miami', 'Seattle'].map((city) => (
                <Button
                  key={city}
                  variant="outline"
                  size="sm"
                  onClick={() => setSearchQuery(city)}
                  className="h-9 px-4 text-sm border-gray-200 hover:border-blue-300 hover:text-blue-600"
                >
                  {city}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <Badge variant="outline" className="mb-4 px-4 py-2 text-sm font-medium">
              <BarChart3 className="mr-2 h-4 w-4" />
              Advanced Analytics
            </Badge>
            <h2 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl mb-6">
              Comprehensive Risk Assessment
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our platform combines multiple data sources and advanced ML models to provide accurate,
              localized risk predictions with actionable insights.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="group hover:shadow-xl transition-all duration-300 border-0 shadow-lg">
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-3 mb-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50 group-hover:bg-red-100 transition-colors">
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  </div>
                  <CardTitle className="text-xl font-semibold">Flood Risk</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-gray-600 mb-4">
                  Predict flooding risk based on precipitation, soil moisture, elevation, and upstream conditions with 72-hour forecasting.
                </CardDescription>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="text-xs">Precipitation</Badge>
                  <Badge variant="secondary" className="text-xs">Soil Moisture</Badge>
                  <Badge variant="secondary" className="text-xs">Elevation</Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="group hover:shadow-xl transition-all duration-300 border-0 shadow-lg">
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-3 mb-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-50 group-hover:bg-orange-100 transition-colors">
                    <TrendingUp className="h-6 w-6 text-orange-600" />
                  </div>
                  <CardTitle className="text-xl font-semibold">Heat Risk</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-gray-600 mb-4">
                  Assess extreme heat risk considering urban heat island effects, humidity, and land cover patterns.
                </CardDescription>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="text-xs">Temperature</Badge>
                  <Badge variant="secondary" className="text-xs">Humidity</Badge>
                  <Badge variant="secondary" className="text-xs">Land Cover</Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="group hover:shadow-xl transition-all duration-300 border-0 shadow-lg">
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-3 mb-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 group-hover:bg-purple-100 transition-colors">
                    <Globe className="h-6 w-6 text-purple-600" />
                  </div>
                  <CardTitle className="text-xl font-semibold">Air Quality</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-gray-600 mb-4">
                  Monitor smoke and PM2.5 levels with wind field analysis and real-time fire detection integration.
                </CardDescription>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="text-xs">PM2.5</Badge>
                  <Badge variant="secondary" className="text-xs">Wind Fields</Badge>
                  <Badge variant="secondary" className="text-xs">Fire Detection</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-24 bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl mb-4">
              Platform Capabilities
            </h2>
            <p className="text-lg text-gray-600">
              Advanced technology delivering precise risk assessments at scale
            </p>
          </div>
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center group">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 group-hover:bg-blue-200 transition-colors mb-4">
                <span className="text-2xl font-bold text-blue-600">72h</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Prediction Horizon</h3>
              <p className="text-sm text-gray-600">Advanced forecasting with 72-hour lead time</p>
            </div>
            <div className="text-center group">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-green-100 group-hover:bg-green-200 transition-colors mb-4">
                <span className="text-2xl font-bold text-green-600">1km</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Grid Resolution</h3>
              <p className="text-sm text-gray-600">High-resolution 1km grid for precise localization</p>
            </div>
            <div className="text-center group">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-100 group-hover:bg-purple-200 transition-colors mb-4">
                <span className="text-2xl font-bold text-purple-600">4</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Hazard Types</h3>
              <p className="text-sm text-gray-600">Comprehensive coverage of major climate risks</p>
            </div>
            <div className="text-center group">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-100 group-hover:bg-orange-200 transition-colors mb-4">
                <span className="text-2xl font-bold text-orange-600">24/7</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Real-time Updates</h3>
              <p className="text-sm text-gray-600">Continuous monitoring and instant alerts</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-white">
        <div className="container mx-auto px-6">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-8">
              <h2 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl mb-6">
                Ready to Get Started?
              </h2>
              <p className="text-xl text-gray-600">
                Explore the map to see risk assessments for your area, or upload your assets
                for personalized monitoring and alerts.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" asChild className="h-14 px-8 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
                <Link href="/map" className="flex items-center">
                  <MapPin className="mr-2 h-5 w-5" />
                  Explore Map
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild className="h-14 px-8 border-2">
                <Link href="/sites" className="flex items-center">
                  <Users className="mr-2 h-5 w-5" />
                  Upload Assets
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-gray-50 py-12">
        <div className="container mx-auto px-6">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-700">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-semibold text-gray-900">Climate Risk Lens</span>
            </div>
            <p className="text-gray-600 mb-2">
              &copy; 2024 Climate Risk Lens. All rights reserved.
            </p>
            <p className="text-sm text-gray-500">
              Built with Next.js, FastAPI, and advanced ML models for accurate risk assessment.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
