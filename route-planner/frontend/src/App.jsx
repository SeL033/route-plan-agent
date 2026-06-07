import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import SearchPanel from './components/SearchPanel'
import RoutePanel from './components/RoutePanel'
import MapView from './components/MapView'

const FOREIGN_CITIES = ['珀斯', '墨尔本', '悉尼', '新加坡', '东京', '首尔']
function detectIsForeign(text = '') {
    const lower = text.toLowerCase()
    const map = { '珀斯': ['珀斯','perth'], '墨尔本': ['墨尔本','melbourne'], '悉尼': ['悉尼','sydney'], '新加坡': ['新加坡','singapore'], '东京': ['东京','tokyo'], '首尔': ['首尔','seoul'] }
    return Object.values(map).some(aliases => aliases.some(a => lower.includes(a)))
}
import LoadingScreen from './components/LoadingScreen'
import OpeningAnimation from './components/OpeningAnimation'

export default function App() {
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [activeRoute, setActiveRoute] = useState(0)
    const [error, setError] = useState(null)
    const [userId, setUserId] = useState('demo_user')

    const handleSearch = async (userInput, startLocation, nextUserId = 'demo_user') => {
        setLoading(true)
        setError(null)
        setResult(null)
        setUserId(nextUserId)

        try {
        const payload = { user_input: userInput, start_location: startLocation || null, user_id: nextUserId }
        const initialRes = await fetch('/api/plan/initial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        const initialData = await initialRes.json()
        if (initialData.status === 'error') {
            setError(initialData.error_msg)
        } else {
            setResult(initialData)
            setActiveRoute(0)
            setLoading(false)
        }

        fetch(`${import.meta.env.VITE_API_BASE}/api/plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'error') {
                    setError(data.error_msg)
                } else {
                    setResult(data)
                    setActiveRoute(0)
                    setError(null)
                    console.log('route stops:', data?.routes?.[0]?.stops?.map(s => ({name: s.name, location: s.location})))
                }
            })
            .catch(() => setError('大模型精修暂时没有完成，已保留初步方案'))
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
        <div className={`app-shell ${result ? 'has-result' : ''}`}>
        <OpeningAnimation />
        <MapView route={result?.routes?.[activeRoute]} visible={!!result} userInput={result?.user_input || ''} />

        <AnimatePresence>
            {!result && (
                <motion.div
                initial={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="landing-wash"
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
                background: 'rgba(255,245,238,0.9)', border: '1px solid rgba(214,100,73,0.25)',
                color: '#b8503d', padding: '12px 24px', borderRadius: 8,
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
                userId={userId}
                isForeign={detectIsForeign(result?.user_input || '')}
            />
            )}
        </AnimatePresence>
        </div>
    )
}