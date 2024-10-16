'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Slider } from "@/components/ui/slider"
import { Input } from "@/components/ui/input"
import { Coffee, Search } from 'lucide-react'
import { getDashboardData, getUserPreference, updateUserPreference } from '@/lib/api'
import { Button } from "@/components/ui/button"
import { startIndexingAllRepos } from '@/lib/api'
import { DashboardData } from '@/types/dashboard'

const frequencyOptions = ['Daily', 'Weekly', 'Fortnightly', 'Monthly', 'Quarterly']

export function Index() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [userPreference, setUserPreference] = useState('')
  const [sliderValue, setSliderValue] = useState(50)
  const [isIndexing, setIsIndexing] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getDashboardData()
        setDashboardData(data)
        const pref = await getUserPreference()
        setUserPreference(pref.tea_frequency)
        setSliderValue(frequencyOptions.indexOf(pref.tea_frequency) * 25)
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }
    fetchData()
  }, [])

  const handleSliderChange = async (value: number[]) => {
    const newValue = value[0]
    setSliderValue(newValue)
    const newFrequency = frequencyOptions[Math.round(newValue / 25)]
    setUserPreference(newFrequency)
    await updateUserPreference(newFrequency)
  }

  const handleIndexAllRepos = async () => {
    setIsIndexing(true)
    await startIndexingAllRepos()
    setIsIndexing(false)
    // Optionally refresh dashboard data after indexing
    const fetchData = async () => {
      const data = await getDashboardData()
      setDashboardData(data)
      const pref = await getUserPreference()
      setUserPreference(pref.tea_frequency)
      setSliderValue(frequencyOptions.indexOf(pref.tea_frequency) * 25)
    }
    fetchData()
  }

  if (!dashboardData) return <div>Loading...</div>

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Coffee className="h-8 w-8 text-blue-500" />
            <span className="text-xl font-bold">JustTheTea</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <Input className="pl-8" placeholder="Search..." />
            </div>
            <Avatar>
              <AvatarImage src="/placeholder.svg?height=32&width=32" alt="User" />
              <AvatarFallback>U</AvatarFallback>
            </Avatar>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-4">
          <Button onClick={handleIndexAllRepos} disabled={isIndexing}>
            {isIndexing ? 'Indexing...' : 'Index All Repositories'}
          </Button>
        </div>

        {isIndexing && <div className="mb-4">Indexing in progress...</div>}

        <Card className="mb-8 bg-purple-50">
          <CardHeader>
            <CardTitle className="text-sm font-normal text-gray-500">
              Time Range: {new Date(dashboardData.date_range.start).toLocaleDateString()} - {new Date(dashboardData.date_range.end).toLocaleDateString()}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <h2 className="text-xl font-semibold mb-4">How often do you want your tea?</h2>
            <div className="relative mb-6">
              <Slider
                value={[sliderValue]}
                onValueChange={handleSliderChange}
                max={100}
                step={25}
                className="z-10"
              />
              <div className="absolute top-1/2 left-0 right-0 flex justify-between -mt-2 pointer-events-none">
                {[0, 25, 50, 75, 100].map((value) => (
                  <div
                    key={value}
                    className={`w-4 h-4 rounded-full ${
                      sliderValue >= value ? 'bg-blue-500' : 'bg-gray-300'
                    }`}
                  />
                ))}
              </div>
            </div>
            <div className="flex justify-between text-sm text-gray-500">
              {frequencyOptions.map((option, index) => (
                <span key={index} className={sliderValue >= index * 25 ? 'font-semibold' : ''}>
                  {option}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="myteam" className="mb-8">
          <TabsList>
            <TabsTrigger value="myteam">My team</TabsTrigger>
            <TabsTrigger value="myself">Myself</TabsTrigger>
          </TabsList>
          <TabsContent value="myteam">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <MetricCard value={dashboardData.team_metrics.prs_merged.toString()} label="PR merged" />
              <MetricCard value={dashboardData.team_metrics.merge_conflicts_resolved.toString()} label="Merge conflict resolved" />
              <MetricCard value={dashboardData.team_metrics.lines_of_code.toString()} label="Lines of code" />
              <MetricCard value={dashboardData.team_metrics.average_review_time.toString()} label="hours average review time" />
            </div>
          </TabsContent>
          <TabsContent value="myself">
            {/* Add content for "Myself" tab here */}
          </TabsContent>
        </Tabs>

        <Card>
          <CardHeader>
            <CardTitle>Highlights of the sprint</CardTitle>
            <p className="text-sm text-gray-500">
              {new Date(dashboardData.date_range.start).toLocaleDateString()} - {new Date(dashboardData.date_range.end).toLocaleDateString()}
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.highlights.map((highlight, index) => (
                <HighlightItem key={index} icon={highlight.icon} content={highlight.content} />
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

function MetricCard({ value, label }: { value: string; label: string }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-3xl font-bold mb-1">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </CardContent>
    </Card>
  )
}

function HighlightItem({ icon, content }: { icon: string; content: string }) {
  return (
    <div className="flex space-x-4">
      <div className="text-2xl">{icon}</div>
      <p className="text-sm">{content}</p>
    </div>
  )
}
