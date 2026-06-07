import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY

const STYLE_COLORS = {
    '平衡推荐': '#2aa89b',
    '省钱少排队': '#78b95b',
    '经典打卡': '#f0a43a',
    '省时版': '#2aa89b',
    '省钱版': '#78b95b',
    '网红版': '#f0a43a',
}

const FOREIGN_CITIES = ['珀斯', '墨尔本', '悉尼', '新加坡', '东京', '首尔']

function detectCity(userInput = '') {
    const lower = userInput.toLowerCase()
    const cityMap = {
        '珀斯': ['珀斯', 'perth'], '墨尔本': ['墨尔本', 'melbourne'],
        '悉尼': ['悉尼', 'sydney'], '新加坡': ['新加坡', 'singapore'],
        '东京': ['东京', 'tokyo'], '首尔': ['首尔', 'seoul'],
    }
    for (const [city, aliases] of Object.entries(cityMap)) {
        if (aliases.some(a => lower.includes(a))) return city
    }
    return null
}

function ForeignBackground({ visible, city }) {
    const cityEmoji = { '东京': '🗼', '首尔': '🏯', '新加坡': '🦁', '悉尼': '🦘', '墨尔本': '☕', '珀斯': '🌊' }
    return (
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(160deg, #e8f5f2 0%, #f0f9f7 40%, #e6f4f0 100%)', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: '15%', left: '8%', width: 280, height: 280, borderRadius: '50%', background: 'rgba(42,168,155,0.06)', border: '1px solid rgba(42,168,155,0.1)' }} />
            <div style={{ position: 'absolute', bottom: '20%', left: '5%', width: 220, height: 220, borderRadius: '50%', background: 'rgba(120,185,91,0.05)', border: '1px solid rgba(120,185,91,0.08)' }} />
            <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.06 }} viewBox="0 0 600 800">
                <path d="M50 600 Q150 400 300 300 Q450 200 580 100" fill="none" stroke="#2aa89b" strokeWidth="1.5" strokeDasharray="8 6" />
            </svg>
            {visible && <div style={{ position: 'absolute', top: '30%', left: '15%', fontSize: 72, opacity: 0.15, userSelect: 'none' }}>{cityEmoji[city] || '✈️'}</div>}
            {visible && <div style={{ position: 'absolute', bottom: 32, left: '50%', transform: 'translateX(-50%)', color: '#2aa89b', opacity: 0.5, fontSize: 12, fontFamily: 'serif', whiteSpace: 'nowrap' }}>点击景点卡片中的 Google Maps 链接进行导航</div>}
        </div>
    )
}

export default function MapView({ route, visible, userInput }) {
    const mapRef = useRef(null)
    const mapInstanceRef = useRef(null)
    const markersRef = useRef([])
    const polylinesRef = useRef([])
    const pendingRouteRef = useRef(null)

    const city = detectCity(userInput)
    const isForeign = FOREIGN_CITIES.includes(city)

    const updateMap = (route, map) => {
        // 调试日志
        console.log('[MapView] updateMap called, stops:', route?.stops?.length)
        console.log('[MapView] stops locations:', route?.stops?.map(s => ({ name: s.name, location: s.location })))

        markersRef.current.forEach(m => map.remove(m))
        polylinesRef.current.forEach(p => map.remove(p))
        markersRef.current = []
        polylinesRef.current = []

        const color = STYLE_COLORS[route.style] || '#2aa89b'
        const positions = []

        route.stops.forEach((stop, i) => {
            const lat = stop.location?.lat ?? stop.location?.latitude
            const lng = stop.location?.lng ?? stop.location?.longitude
            console.log(`[MapView] stop ${i} ${stop.name}: lat=${lat} lng=${lng}`)
            if (!lng || !lat || lat === 0 || lng === 0) {
                console.warn(`[MapView] SKIP ${stop.name} - invalid coords`)
                return
            }
            positions.push([lng, lat])

            const marker = new window.AMap.Marker({
                position: [lng, lat],
                content: `<div style="background:${color};color:white;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,0.3);border:2px solid rgba(255,255,255,0.4);font-family:monospace;cursor:pointer;">${i + 1}</div>`,
                offset: new window.AMap.Pixel(-14, -14),
            })

            const infoWindow = new window.AMap.InfoWindow({
                content: `<div style="background:#fff;color:#333;padding:10px 14px;border-radius:8px;font-family:serif;min-width:140px;box-shadow:0 2px 12px rgba(0,0,0,0.15);">
                    <strong style="font-size:14px;">${stop.name}</strong><br/>
                    <span style="color:#888;font-size:11px;">${stop.arrive_time} · ${stop.duration}分钟</span><br/>
                    <span style="color:${color};font-size:11px;">${stop.cost === 0 ? '免费' : '¥' + stop.cost}</span>
                </div>`,
                isCustom: true,
                offset: new window.AMap.Pixel(0, -32)
            })

            marker.on('click', () => infoWindow.open(map, marker.getPosition()))
            map.add(marker)
            markersRef.current.push(marker)
        })

        console.log(`[MapView] added ${markersRef.current.length} markers, ${positions.length} positions`)

        if (positions.length > 1) {
            const polyline = new window.AMap.Polyline({
                path: positions,
                strokeColor: color,
                strokeWeight: 3,
                strokeOpacity: 0.85,
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

    const initMap = () => {
        console.log('[MapView] initMap called, mapRef:', !!mapRef.current, 'already init:', !!mapInstanceRef.current)
        if (!mapRef.current || mapInstanceRef.current) return
        mapInstanceRef.current = new window.AMap.Map(mapRef.current, {
            zoom: 12,
            center: [116.3972, 39.9042],
        })
        console.log('[MapView] map created')
        if (pendingRouteRef.current) {
            console.log('[MapView] rendering pending route')
            updateMap(pendingRouteRef.current, mapInstanceRef.current)
            pendingRouteRef.current = null
        }
    }

    useEffect(() => {
        console.log('[MapView] mount, AMap exists:', !!window.AMap)
        if (window.AMap) {
            initMap()
            return
        }
        // 防止重复插入script
        if (document.getElementById('amap-script')) {
            // 脚本已在加载中，等待
            const timer = setInterval(() => {
                if (window.AMap) {
                    clearInterval(timer)
                    console.log('[MapView] AMap ready from poll')
                    initMap()
                }
            }, 100)
            return () => clearInterval(timer)
        }
        const script = document.createElement('script')
        script.id = 'amap-script'
        script.src = `https://webapi.amap.com/maps?v=1.4.15&key=${AMAP_KEY}`
        script.onload = () => {
            console.log('[MapView] AMap script loaded')
            initMap()
        }
        document.head.appendChild(script)
    }, [])

    useEffect(() => {
        console.log('[MapView] route changed, isForeign:', isForeign, 'route:', !!route, 'mapInstance:', !!mapInstanceRef.current)
        if (!route || isForeign) return
        if (!mapInstanceRef.current) {
            console.log('[MapView] map not ready, saving pending route')
            pendingRouteRef.current = route
        } else {
            updateMap(route, mapInstanceRef.current)
        }
    }, [route, isForeign])

    return (
        <motion.div
            animate={{ opacity: visible ? 1 : 0.18 }}
            transition={{ duration: 0.6 }}
            style={{ position: 'absolute', inset: 0, zIndex: 0 }}
        >
            {isForeign && <ForeignBackground visible={visible} city={city} />}
            <div
                ref={mapRef}
                style={{ width: '100%', height: '100%', position: 'absolute', inset: 0, display: isForeign ? 'none' : 'block' }}
            />
            {!isForeign && (
                <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', background: visible ? 'linear-gradient(to right, rgba(248,245,240,0) 55%, rgba(248,245,240,0.35) 100%)' : 'rgba(248,245,240,0.55)' }} />
            )}
        </motion.div>
    )
}