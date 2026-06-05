import { motion, AnimatePresence } from 'framer-motion'

const STYLE_CONFIG = {
    '省时版': { color: '#3498DB', icon: '⚡', bg: 'rgba(52,152,219,0.1)', border: 'rgba(52,152,219,0.3)' },
    '省钱版': { color: '#2ECC71', icon: '💰', bg: 'rgba(46,204,113,0.1)', border: 'rgba(46,204,113,0.3)' },
    '网红版': { color: '#FF6B00', icon: '🔥', bg: 'rgba(255,107,0,0.1)', border: 'rgba(255,107,0,0.3)' },
    }

    export default function RoutePanel({ result, activeRoute, onSelectRoute }) {
    const routes = result?.routes || []
    const current = routes[activeRoute]

    return (
        <motion.div
        initial={{ opacity: 0, x: 40 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 40 }}
        transition={{ type: 'spring', stiffness: 300, damping: 35 }}
        style={{
            position: 'absolute', right: 24, top: 24, bottom: 24,
            width: 400, zIndex: 50,
            display: 'flex', flexDirection: 'column', gap: 12,
        }}
        >
        {/* 路线选择tabs */}
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            style={{ display: 'flex', gap: 8 }}
        >
            {routes.map((route, i) => {
            const cfg = STYLE_CONFIG[route.style] || STYLE_CONFIG['网红版']
            const active = i === activeRoute
            return (
                <motion.button
                key={i}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onSelectRoute(i)}
                style={{
                    flex: 1, padding: '10px 8px',
                    background: active ? cfg.bg : 'rgba(14,14,14,0.85)',
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${active ? cfg.border : 'var(--border)'}`,
                    borderRadius: 12, cursor: 'pointer',
                    color: active ? cfg.color : 'var(--text-dim)',
                    fontFamily: 'var(--font-serif)', fontSize: 13,
                    transition: 'all 0.2s', textAlign: 'center'
                }}
                >
                <div style={{ fontSize: 18, marginBottom: 2 }}>{cfg.icon}</div>
                <div style={{ fontWeight: 600 }}>{route.style}</div>
                </motion.button>
            )
            })}
        </motion.div>

        {/* 当前路线详情 */}
        <AnimatePresence mode="wait">
            {current && (
            <motion.div
                key={activeRoute}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}
            >
                {/* 路线概览 */}
                <div style={{
                background: 'rgba(14,14,14,0.92)', backdropFilter: 'blur(20px)',
                borderRadius: 14, padding: '16px', border: '1px solid var(--border)',
                }}>
                <div style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.6, marginBottom: 12 }}>
                    {current.description}
                </div>
                <div style={{ display: 'flex', gap: 16 }}>
                    <Stat label="总费用" value={`¥${current.total_cost}`} />
                    <Stat label="游览时长" value={`${Math.round(current.total_duration_minutes / 60)}小时`} />
                    <Stat label="出发" value={current.start_time} />
                    <Stat label="结束" value={current.end_time} />
                </div>
                </div>

                {/* 停留点列表 */}
                {current.stops.map((stop, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.06 }}
                    style={{
                    background: 'rgba(14,14,14,0.92)', backdropFilter: 'blur(20px)',
                    borderRadius: 14, padding: '14px 16px',
                    border: '1px solid var(--border)',
                    display: 'flex', gap: 12, alignItems: 'flex-start'
                    }}
                >
                    <div style={{
                    width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                    background: `${STYLE_CONFIG[current.style]?.color || '#FF6B00'}22`,
                    border: `1px solid ${STYLE_CONFIG[current.style]?.color || '#FF6B00'}66`,
                    color: STYLE_CONFIG[current.style]?.color || '#FF6B00',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)'
                    }}>
                    {i + 1}
                    </div>
                    <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <div style={{ fontWeight: 600, fontSize: 15 }}>{stop.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {stop.arrive_time} → {stop.leave_time}
                        </div>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.5, marginBottom: 6 }}>
                        {stop.reason}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <Tag value={stop.cost === 0 ? '免费' : `¥${stop.cost}`} />
                        <Tag value={`${stop.duration}分钟`} />
                    </div>
                    </div>
                </motion.div>
                ))}
            </motion.div>
            )}
        </AnimatePresence>
        </motion.div>
    )
    }

    function Stat({ label, value }) {
    return (
        <div style={{ flex: 1, textAlign: 'center' }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>{label}</div>
        <div style={{ fontSize: 14, fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--orange)' }}>{value}</div>
        </div>
    )
    }

    function Tag({ value }) {
    return (
        <span style={{
        fontSize: 11, padding: '2px 8px', borderRadius: 4,
        background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)',
        fontFamily: 'var(--font-mono)'
        }}>
        {value}
        </span>
    )
}