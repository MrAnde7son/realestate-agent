'use client'
import React, { useEffect, useRef, useState } from 'react'
import { Loader2, MapPin } from 'lucide-react'

export default function Map({ center=[34.7818,32.0853], zoom=12 }:{ center?: [number,number], zoom?: number }){
  const ref = useRef<HTMLDivElement>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(()=>{
    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN as string | undefined
    if(!token){ 
      setLoading(false)
      if(ref.current) {
        ref.current.innerHTML='<div style="display:flex;align-items:center;justify-content:center;color:#a6aab5;height:280px;border:1px dashed var(--border);border-radius:10px">Mapbox placeholder (set NEXT_PUBLIC_MAPBOX_TOKEN)</div>'
      }
      return 
    }

    let map: any
    (async () => {
      try {
        const mapboxgl = (await import('mapbox-gl')).default
        mapboxgl.accessToken = token
        map = new mapboxgl.Map({
          container: ref.current!,
          style: 'mapbox://styles/mapbox/streets-v12',
          center,
          zoom,
        })
        
        map.on('load', () => {
          setLoading(false)
        })
      } catch (error) {
        console.error('Error loading map:', error)
        setLoading(false)
      }
    })()

    return () => { 
      if (map) map.remove() 
      setLoading(true)
    }
  },[center,zoom])
  
  return (
    <div className="relative h-[280px] rounded-lg">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted rounded-lg z-10">
          <div className="flex flex-col items-center space-y-2">
            <Loader2 className="h-6 w-6 animate-spin text-brand-teal" />
            <span className="text-sm text-muted-foreground">טוען מפה...</span>
          </div>
        </div>
      )}
      <div ref={ref} className="h-full rounded-lg" />
    </div>
  )
}
