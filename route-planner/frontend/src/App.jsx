import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import SearchPanel from './components/SearchPanel'
import RoutePanel from './components/RoutePanel'
import MapView from './components/MapView'
import LoadingScreen from './components/LoadingScreen'

export default function App() {
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [activeRoute, setActiveRoute] = useState(0)
    const [error, setError] = useState(null)

    const handleSearch = async (userInput, startLocation) => {
        setLoading(true)
        setError(null)
        setResult(null)

        try {
        const res = await fetch('/api/plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_input: userInput, start_location: startLocation || null })
        })
        const data = await res.json()
        if (data.status === 'error') {
            setError(data.error_msg)
        } else {
            setResult(data)
            setActiveRoute(0)
        }
        } catch (e) {
        setError('网络错误，请检查后端服务是否启动')
        } finally {
        setLoading(false)
        }
    }

    const handleReset = () => {
        setResult(null)
        setError(null)
    }

    return (
        <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden' }}>
        <MapView route={result?.routes?.[activeRoute]} visible={!!result} />

        <AnimatePresence>
            {!result && (
            <motion.div
                initial={{ opacity: 1 }} exit={{ opacity: 0 }}
                style={{
                position: 'absolute', inset: 0,
                background: 'radial-gradient(ellipse at 30% 50%, rgba(255,107,0,0.08) 0%, transparent 60%), radial-gradient(ellipse at 70% 30%, rgba(52,152,219,0.05) 0%, transparent 50%)',
                zIndex: 0
                }}
            />
            )}
        </AnimatePresence>

        <SearchPanel
            onSearch={handleSearch}
            loading={loading}
            hasResult={!!result}
            onReset={handleReset}
        />

        <AnimatePresence>{loading && <LoadingScreen />}</AnimatePresence>

        <AnimatePresence>
            {error && (
            <motion.div
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}
                style={{
                position: 'absolute', bottom: 32, left: '50%', transform: 'translateX(-50%)',
                background: 'rgba(220,50,50,0.15)', border: '1px solid rgba(220,50,50,0.3)',
                color: '#ff6b6b', padding: '12px 24px', borderRadius: 8,
                fontFamily: 'var(--font-mono)', fontSize: 13, zIndex: 100,
                backdropFilter: 'blur(12px)'
                }}
            >
                ⚠ {error}
            </motion.div>
            )}
        </AnimatePresence>

        <AnimatePresence>
            {result && (
            <RoutePanel
                result={result}
                activeRoute={activeRoute}
                onSelectRoute={setActiveRoute}
            />
            )}
        </AnimatePresence>
        </div>
    )
}