import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const SUGGESTIONS = [
    '我想去北京玩一天，不想排队，预算100',
    '情侣上海一日游，喜欢咖啡和海边',
    '朋友悉尼一天，想打卡地标和美食',
    '广州两日游，想吃早茶和逛老城区',
    '成都一天，老人腿脚不便',
]

const PROFILES = [
    { id: 'demo_user', label: '默认偏好' },
    { id: 'user_family', label: '亲子清淡' },
    { id: 'user_spicy', label: '川渝重口' },
]

export default function SearchPanel({ onSearch, loading, hasResult, onReset }) {
    const [input, setInput] = useState('')
    const [startLocation, setStartLocation] = useState('')
    const [userId, setUserId] = useState('demo_user')
    const [focused, setFocused] = useState(false)

    const handleSubmit = () => {
        if (input.trim() && !loading) onSearch(input.trim(), startLocation.trim(), userId)
    }

    const handleKey = (e) => {
        if (e.key === 'Enter') handleSubmit()
    }

    const handleReset = () => {
        setInput('')
        setStartLocation('')
        onReset()
    }

    return (
        <div className={`search-panel ${hasResult ? 'compact' : ''}`}>
            <AnimatePresence>
                {!hasResult && (
                    <motion.div
                        className="brand-block"
                        initial={{ opacity: 0, y: -18 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -18 }}
                    >
                        <div className="brand-mark">逛逛</div>
                        <h1>一句话，规划你的城市之旅</h1>
                        <p>输入目的地、预算和偏好，生成顺路、不重复、能直接执行的城市路线。</p>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className={`search-card ${focused ? 'is-focused' : ''}`}>
                <div className="search-row">
                    <span className="field-icon">⌕</span>
                    <input
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKey}
                        onFocus={() => setFocused(true)}
                        onBlur={() => setTimeout(() => setFocused(false), 150)}
                        placeholder="想去哪里？比如：珀斯一天，不想排队，预算100"
                    />
                    {hasResult ? (
                        <button className="icon-button" onClick={handleReset} aria-label="重新规划">×</button>
                    ) : (
                        <button className="primary-button" onClick={handleSubmit} disabled={loading || !input.trim()}>
                            {loading ? '规划中' : '出发'}
                        </button>
                    )}
                </div>

                <div className="start-row">
                    <span className="field-icon">⌖</span>
                    <input
                        value={startLocation}
                        onChange={e => setStartLocation(e.target.value)}
                        onKeyDown={handleKey}
                        placeholder="出发地，可选：酒店、车站、商圈"
                    />
                </div>

                <div className="profile-row">
                    {PROFILES.map(profile => (
                        <button
                            key={profile.id}
                            type="button"
                            className={profile.id === userId ? 'active' : ''}
                            onClick={() => setUserId(profile.id)}
                        >
                            {profile.label}
                        </button>
                    ))}
                </div>

                <AnimatePresence>
                    {(focused || hasResult || !input) && (
                        <motion.div
                            className="suggestions"
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                        >
                            <div className="suggest-title">{hasResult ? '换个城市试试' : '灵感路线'}</div>
                            <div className="suggest-grid">
                                {SUGGESTIONS.map((suggestion) => (
                                    <button
                                        key={suggestion}
                                        onMouseDown={() => {
                                            setInput(suggestion)
                                            setFocused(false)
                                            if (hasResult) onSearch(suggestion, startLocation.trim(), userId)
                                        }}
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}