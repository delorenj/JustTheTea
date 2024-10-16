'use client'

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle } from 'lucide-react'

type DigestEntry = {
  id: number
  title: string
  content: string
  date: string
}

const API_URL = 'https://ab62-158-106-221-180.ngrok-free.app'

export function Index() {
  const [digest, setDigest] = useState<DigestEntry | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await fetch(`${API_URL}/digest`, {
          mode: 'cors', // This tells the browser to include CORS headers
          headers: {
            'Content-Type': 'application/json',
            // Add any other necessary headers here
          },
        })
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        setDigest(data)
      } catch (e) {
        console.error("Error fetching data:", e)
        setError("Failed to fetch data. Please try again later.")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-4xl font-bold mb-8">JustTheTea ☕</h1>
        <Card className="mb-8">
          <CardHeader>
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-4xl font-bold mb-8">JustTheTea ☕</h1>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button className="mt-4" onClick={() => window.location.reload()}>
          Try Again
        </Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4">
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
    </div>
  )
}