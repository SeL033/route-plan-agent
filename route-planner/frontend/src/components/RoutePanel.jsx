import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CITY_FOODS, detectCity } from '../cityContent'

const STYLE_CONFIG = {
    '平衡推荐': { color: '#2aa89b', icon: '◎' },
    '省钱少排队': { color: '#78b95b', icon: '¥' },
    '经典打卡': { color: '#f0a43a', icon: '★' },
    '省时版': { color: '#2aa89b', icon: '◎' },
    '省钱版': { color: '#78b95b', icon: '¥' },
    '网红版': { color: '#f0a43a', icon: '★' },
}

export default function RoutePanel({ result, activeRoute, onSelectRoute, userId }) {
    const routes = result?.routes || []
    const current = routes[activeRoute]
    const city = detectCity(result?.user_input)
    const foods = CITY_FOODS[city] || CITY_FOODS['上海']
    const days = groupStopsByDay(current?.stops || [])
    const [feedback, setFeedback] = useState(null)

    const submitFeedback = async (liked) => {
        if (!current) return
        setFeedback('正在更新偏好...')
        try {
            const res = await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    route_style: current.style,
                    liked,
                    stops: current.stops,
                    comment: liked ? '用户喜欢这条路线' : '用户觉得这条路线不适合',
                })
            })
            const data = await res.json()
            setFeedback(data.history_summary || data.message || '偏好已更新')
        } catch {
            setFeedback('反馈暂时没有提交成功')
        }
    }

    return (
        <motion.aside
            className="route-panel"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 40 }}
            transition={{ type: 'spring', stiffness: 280, damping: 32 }}
        >
            <div className="route-tabs">
                {routes.map((route, i) => {
                    const cfg = STYLE_CONFIG[route.style] || STYLE_CONFIG['经典打卡']
                    const active = i === activeRoute
                    return (
                        <button
                            key={route.style}
                            className={active ? 'active' : ''}
                            style={{ '--accent': cfg.color }}
                            onClick={() => onSelectRoute(i)}
                        >
                            <span>{cfg.icon}</span>
                            {route.style}
                        </button>
                    )
                })}
            </div>

            <AnimatePresence mode="wait">
                {current && (
                    <motion.div
                        key={activeRoute}
                        className="route-scroll"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                    >
                        <section className="route-summary">
                            {result.status === 'partial' && <div className="draft-banner">初步方案已生成，大模型正在后台精修</div>}
                            <p>{current.description}</p>
                            <div className="stats">
                                <Stat label="费用" value={`¥${current.total_cost}`} />
                                <Stat label="时长" value={`${Math.round(current.total_duration_minutes / 60)}小时`} />
                                <Stat label="出发" value={current.start_time} />
                                <Stat label="结束" value={current.end_time} />
                            </div>
                            <div className="feedback-row">
                                <button onClick={() => submitFeedback(true)}>更喜欢这条</button>
                                <button onClick={() => submitFeedback(false)}>不太适合我</button>
                                {feedback && <span>{feedback}</span>}
                            </div>
                        </section>

                        <section className="stop-list">
                            {days.map(({ day, stops }) => (
                                <div className="day-group" key={day}>
                                    {days.length > 1 && <div className="day-divider">Day {day}</div>}
                                    {stops.map((stop, i) => (
                                        <motion.article
                                            className={`stop-card ${stop.poi_type === 'food' ? 'food-stop' : ''}`}
                                            key={`${stop.poi_id}-${i}`}
                                            initial={{ opacity: 0, y: 16 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.05 }}
                                        >

                                            <div className="stop-content">
                                                <div className="stop-head">
                                                    <span className="stop-index">{i + 1}</span>
                                                    <div>
                                                        <h3>{stop.name}</h3>
                                                        <time>{stop.arrive_time} - {stop.leave_time}</time>
                                                    </div>
                                                </div>
                                                <p>{stop.reason}</p>
                                                <div className="tags">
                                                    {stop.poi_type === 'food' && <span>顺路美食</span>}
                                                    <span>{stop.cost === 0 ? '免费' : `¥${stop.cost}`}</span>
                                                    <span>{stop.duration}分钟</span>
                                                    <a href={mapLink(stop, city)} target="_blank" rel="noreferrer">{isForeignCity(city) ? 'Google Maps' : '高德地图'}</a>
                                                </div>
                                                {stop.evidence?.length > 0 && (
                                                    <details className="evidence-box">
                                                        <summary>推荐证据链</summary>
                                                        <ol>
                                                            {stop.evidence.map((item, idx) => <li key={idx}>{item}</li>)}
                                                        </ol>
                                                    </details>
                                                )}
                                                {stop.last_50m_guidance && (
                                                    <div className="micro-guide">
                                                        <strong>最后50米</strong>
                                                        <span>{stop.last_50m_guidance}</span>
                                                    </div>
                                                )}
                                                {stop.dining_advice && (
                                                    <div className="dining-advice">
                                                        <strong>堂食/外带建议</strong>
                                                        <span>{stop.dining_advice}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </motion.article>
                                    ))}
                                </div>
                            ))}
                        </section>

                        <NearbyFood current={current} city={city} foods={foods} />
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.aside>
    )
}

function Stat({ label, value }) {
    return (
        <div>
            <span>{label}</span>
            <strong>{value}</strong>
        </div>
    )
}

function groupStopsByDay(stops) {
    const grouped = new Map()
    stops.forEach(stop => {
        const day = stop.day || 1
        if (!grouped.has(day)) grouped.set(day, [])
        grouped.get(day).push(stop)
    })
    return Array.from(grouped.entries()).map(([day, dayStops]) => ({ day, stops: dayStops }))
}

function isForeignCity(city) {
    return ['珀斯', '墨尔本', '悉尼', '新加坡', '东京', '首尔'].includes(city)
}

function mapLink(stop, city) {
    const lat = stop.location?.lat
    const lng = stop.location?.lng
    const query = encodeURIComponent(`${stop.name} ${city}`)
    if (isForeignCity(city)) {
        return `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`
    }
    return `https://uri.amap.com/marker?position=${lng},${lat}&name=${query}`
}


function NearbyFood({ current, city, foods }) {
    return (
        <section className="food-section">
            <div className="section-title">
                <span>顺路美食</span>
                <small>{city} · 点击搜附近</small>
            </div>
            <div style={{ padding: '0 14px 14px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                {current?.stops?.filter(s => s.poi_type !== 'food').map((stop, i) => (
                    <div key={i}>
                        <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6 }}>
                            📍 {stop.name} 附近
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                            {foods.map((food) => {
                                const url = `https://uri.amap.com/search?keyword=${encodeURIComponent(stop.name + '附近' + food)}&city=${encodeURIComponent(city)}`
                                return (
                                    <a key={food} href={url} target="_blank" rel="noreferrer"
                                        style={{
                                            padding: '5px 12px', borderRadius: 999,
                                            background: 'rgba(42,168,155,0.1)',
                                            border: '1px solid rgba(42,168,155,0.2)',
                                            color: '#2aa89b', fontSize: 12, fontWeight: 600,
                                            textDecoration: 'none',
                                        }}
                                        onMouseEnter={e => { e.currentTarget.style.background = '#2aa89b'; e.currentTarget.style.color = 'white' }}
                                        onMouseLeave={e => { e.currentTarget.style.background = 'rgba(42,168,155,0.1)'; e.currentTarget.style.color = '#2aa89b' }}
                                    >
                                        {food} ↗
                                    </a>
                                )
                            })}
                        </div>
                    </div>
                ))}
            </div>
        </section>
    )
}