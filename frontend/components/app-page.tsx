'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

// Define types for our data
type DigestEntry = {
  id: number
  title: string
  content: string
  date: string
}

type PersonalizedData = {
  contributions: string[]
  impact: string
}

type TeamData = {
  name: string
  ticketsClosed: number
}

type TopContributor = {
  name: string
  avatar: string
  prs: number
}

const API_URL = 'https://ab62-158-106-221-180.ngrok-free.app'

export function Page() {
  const [digest, setDigest] = useState<DigestEntry | null>(null)
  const [personalData, setPersonalData] = useState<PersonalizedData | null>(null)
  const [topTeam, setTopTeam] = useState<TeamData | null>(null)
  const [topContributor, setTopContributor] = useState<TopContributor | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch digest
        const digestRes = await fetch(`${API_URL}/digest`)
        const digestData = await digestRes.json()
        setDigest(digestData)

        // For demo purposes, we'll mock the other data
        // In a real application, you'd fetch this from your API
        setPersonalData({
          contributions: [
            "Closed 5 critical bugs",
            "Contributed to the new feature launch",
            "Helped onboard 2 new team members"
          ],
          impact: "Your work on the new feature has increased user engagement by 15%!"
        })

        setTopTeam({
          name: "Frontend Wizards",
          ticketsClosed: 47
        })

        setTopContributor({
          name: "Jane Doe",
          avatar: "/placeholder.svg?height=40&width=40",
          prs: 15
        })

        setLoading(false)
      } catch (error) {
        console.error("Error fetching data:", error)
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return <div className="p-8"><Skeleton className="w-full h-[600px]" /></div>
  }

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-4xl font-bold mb-8">JustTheTea ☕</h1>
      
      {digest && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>{digest.title}</CardTitle>
            <CardDescription>{new Date(digest.date).toLocaleDateString()}</CardDescription>
          </CardHeader>
          <CardContent>
            <p>{digest.content}</p>
          </CardContent>
        </Card>
      )}

      {personalData && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Your Impact This Week</CardTitle>
          </CardHeader>
          <CardContent>
            <h3 className="font-semibold mb-2">Your Contributions:</h3>
            <ul className="list-disc pl-5 mb-4">
              {personalData.contributions.map((contribution, index) => (
                <li key={index}>{contribution}</li>
              ))}
            </ul>
            <p className="font-semibold">{personalData.impact}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {topTeam && (
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Team</CardTitle>
            </CardHeader>
            <CardContent>
              <h3 className="text-2xl font-bold mb-2">{topTeam.name}</h3>
              <p>Closed {topTeam.ticketsClosed} tickets this week!</p>
              <Badge className="mt-2">Team of the Week</Badge>
            </CardContent>
          </Card>
        )}

        {topContributor && (
          <Card>
            <CardHeader>
              <CardTitle>Top Contributor</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center space-x-4">
              <Avatar>
                <AvatarImage src={topContributor.avatar} alt={topContributor.name} />
                <AvatarFallback>{topContributor.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="text-xl font-semibold">{topContributor.name}</h3>
                <p>{topContributor.prs} PRs merged this week!</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}