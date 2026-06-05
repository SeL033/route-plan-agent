import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY

const STYLE_COLORS = {
    '省时版': '#3498DB',
    '省钱版': '#2ECC71',
    '网红版': '#FF6B00',
    }

    export default function MapView({ route, visible }) {
    const mapRef = useRef(null)
    const mapInstanceRef = useRef(null)
    const markersRef = useRef([])
    const polylinesRef = useRef([])
    const pendingRouteRef = useRef(null)

    const initMap = () => {
        if (!mapRef.current || mapInstanceRef.current) return
        mapInstanceRef.current = new window.AMap.Map(mapRef.current, {
        zoom: 12,
        center: [116.3972, 39.9042],
        })
        // 地图初始化完成后，如果有pending的路线，立即渲染
        if (pendingRouteRef.current) {
        updateMap(pendingRouteRef.current)
        pendingRouteRef.current = null
        }
    }

    useEffect(() => {
        if (window.AMap) {
        initMap()
        } else {
        const script = document.createElement('script')
        script.src = `https://webapi.amap.com/maps?v=1.4.15&key=${AMAP_KEY}`
        script.onload = initMap
        document.head.appendChild(script)
        }
    }, [])

    useEffect(() => {
        if (!route) return
        if (!mapInstanceRef.current) {
        // 地图还没初始化，存起来等地图好了再渲染
        pendingRouteRef.current = route
        } else {
        updateMap(route)
        }
    }, [route])

    const updateMap = (route) => {
        const map = mapInstanceRef.current
        if (!map) return

        markersRef.current.forEach(m => map.remove(m))
        polylinesRef.current.forEach(p => map.remove(p))
        markersRef.current = []
        polylinesRef.current = []

        const color = STYLE_COLORS[route.style] || '#FF6B00'
        const positions = []

        route.stops.forEach((stop, i) => {
        const lng = stop.location?.lng
        const lat = stop.location?.lat
        if (!lng || !lat) return

        positions.push([lng, lat])

        const marker = new window.AMap.Marker({
            position: [lng, lat],
            content: `<div style="
            background:${color};color:white;
            width:28px;height:28px;border-radius:50%;
            display:flex;align-items:center;justify-content:center;
            font-weight:700;font-size:12px;
            box-shadow:0 2px 8px rgba(0,0,0,0.4);
            border:2px solid rgba(255,255,255,0.3);
            font-family:monospace;
            ">${i + 1}</div>`,
            offset: new window.AMap.Pixel(-14, -14),
        })

        const infoWindow = new window.AMap.InfoWindow({
            content: `<div style="
            background:#141414;color:#F0EDE8;
            padding:10px 14px;border-radius:8px;
            border:1px solid rgba(255,255,255,0.1);
            font-family:serif;min-width:140px;
            ">
            <div style="font-weight:600;font-size:14px;margin-bottom:4px;">${stop.name}</div>
            <div style="font-size:11px;color:rgba(240,237,232,0.5);">${stop.arrive_time} · ${stop.duration}分钟</div>
            <div style="font-size:11px;color:${color};margin-top:4px;">${stop.cost === 0 ? '免费' : '¥' + stop.cost}</div>
            </div>`,
            isCustom: true,
            offset: new window.AMap.Pixel(0, -32)
        })

        marker.on('click', () => infoWindow.open(map, marker.getPosition()))
        map.add(marker)
        markersRef.current.push(marker)
        })

        if (positions.length > 1) {
        const polyline = new window.AMap.Polyline({
            path: positions,
            strokeColor: color,
            strokeWeight: 3,
            strokeOpacity: 0.8,
            strokeStyle: 'dashed',
            lineJoin: 'round',
        })
        map.add(polyline)
        polylinesRef.current.push(polyline)
        }

        if (markersRef.current.length > 0) {
        map.setFitView(markersRef.current, false, [80, 80, 80, 450])
        }
    }

    return (
        <motion.div
        animate={{ opacity: visible ? 1 : 0.15 }}
        transition={{ duration: 0.6 }}
        style={{ position: 'absolute', inset: 0, zIndex: 0 }}
        >
        <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
        <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            background: visible
            ? 'linear-gradient(to right, rgba(10,10,10,0) 50%, rgba(10,10,10,0.5) 100%)'
            : 'rgba(10,10,10,0.7)'
        }} />
    </motion.div>
    )
}