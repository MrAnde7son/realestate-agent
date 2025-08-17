'use client'
import React, { useEffect, useRef } from 'react'

export default function Map({ center=[34.7818,32.0853], zoom=12 }:{ center?: [number,number], zoom?: number }){
  const ref = useRef<HTMLDivElement>(null)
  useEffect(()=>{
    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN as string | undefined
    if(!token){ 
      if(ref.current) {
        ref.current.innerHTML='<div style="display:flex;align-items:center;justify-content:center;color:#a6aab5;height:280px;border:1px dashed var(--border);border-radius:10px">Mapbox placeholder (set NEXT_PUBLIC_MAPBOX_TOKEN)</div>'
      }
      return 
    }

    let map: any
    (async () => {
      const mapboxgl = (await import('mapbox-gl')).default
      mapboxgl.accessToken = token
      map = new mapboxgl.Map({
        container: ref.current!,
        style: 'mapbox://styles/mapbox/streets-v12',
        center,
        zoom,
      })
    })()

    return () => { if (map) map.remove() }
  },[center,zoom])
  return <div ref={ref} className="h-[280px] rounded-lg" />
}
