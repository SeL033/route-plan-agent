import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const SUGGESTIONS = [
    '带娃上海一日游，预算500，不想排队',
    '情侣北京两日游，喜欢历史文化',
    '老人成都一日游，腿脚不便',
    '朋友聚会成都一天，网红打卡',
    ]

    export default function SearchPanel({ onSearch, loading, hasResult, onReset }) {
    const [input, setInput] = useState('')
    const [startLocation, setStartLocation] = useState('')
    const [focused, setFocused] = useState(false)

    const handleSubmit = () => {
        if (input.trim() && !loading) onSearch(input.trim(), startLocation.trim())
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
        <div style={{
        position: 'absolute',
        top: hasResult ? 24 : '50%',
        left: hasResult ? 24 : '50%',
        transform: hasResult ? 'none' : 'translate(-50%, -50%)',
        width: hasResult ? 380 : 'min(600px, 90vw)',
        zIndex: 50,
        transition: 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
        }}>
        {/* Logo */}
        <AnimatePresence>
            {!hasResult && (
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                style={{ textAlign: 'center', marginBottom: 32 }}
            >
                <div style={{
                fontSize: 48, fontWeight: 700, letterSpacing: '-2px',
                fontFamily: 'var(--font-serif)',
                background: 'linear-gradient(135deg, var(--orange), var(--orange-light))',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
                }}>智行</div>
                <div style={{ color: 'var(--text-dim)', fontSize: 14, marginTop: 6, letterSpacing: 4 }}>
                AI 智能路线规划
                </div>
            </motion.div>
            )}
        </AnimatePresence>

        <div style={{
            background: 'rgba(20,20,20,0.9)', backdropFilter: 'blur(20px)',
            borderRadius: 16, overflow: 'hidden',
            boxShadow: focused
            ? '0 0 0 2px var(--orange), 0 20px 60px rgba(255,107,0,0.2)'
            : '0 0 0 1px var(--border), 0 8px 32px rgba(0,0,0,0.4)',
            transition: 'box-shadow 0.2s',
        }}>
            {/* 主输入行 */}
            <div style={{ display: 'flex', alignItems: 'center', padding: '14px 16px' }}>
            <span style={{ fontSize: 18, marginRight: 10, flexShrink: 0 }}>🗺</span>
            <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                onFocus={() => setFocused(true)}
                onBlur={() => setTimeout(() => setFocused(false), 150)}
                placeholder="告诉我你想去哪里玩..."
                style={{
                flex: 1, background: 'none', border: 'none', outline: 'none',
                color: 'var(--text)', fontSize: 15, fontFamily: 'var(--font-serif)', minWidth: 0,
                }}
            />
            {/* 结果页显示×返回，否则显示规划按钮 */}
            {hasResult ? (
                <button
                onClick={handleReset}
                style={{
                    background: 'rgba(255,255,255,0.06)', border: '1px solid var(--border)',
                    borderRadius: 8, width: 32, height: 32,
                    color: 'var(--text-dim)', cursor: 'pointer',
                    fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0, marginLeft: 8, transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,50,50,0.15)'; e.currentTarget.style.color = '#ff6b6b'; e.currentTarget.style.borderColor = 'rgba(255,50,50,0.3)' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = 'var(--text-dim)'; e.currentTarget.style.borderColor = 'var(--border)' }}
                >
                ×
                </button>
            ) : (
                <button
                onClick={handleSubmit}
                disabled={loading || !input.trim()}
                style={{
                    background: input.trim() ? 'var(--orange)' : 'rgba(255,107,0,0.2)',
                    border: 'none', borderRadius: 10, padding: '8px 16px',
                    color: 'white', cursor: input.trim() ? 'pointer' : 'default',
                    fontFamily: 'var(--font-serif)', fontSize: 13, fontWeight: 600,
                    transition: 'background 0.2s', whiteSpace: 'nowrap', flexShrink: 0, marginLeft: 8,
                }}
                >
                {loading ? '规划中...' : '开始规划'}
                </button>
            )}
            </div>

            {/* 出发地输入行 */}
            <div style={{
            borderTop: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', padding: '10px 16px', gap: 8
            }}>
            <span style={{ fontSize: 14, flexShrink: 0 }}>📍</span>
            <input
                value={startLocation}
                onChange={e => setStartLocation(e.target.value)}
                onKeyDown={handleKey}
                placeholder="出发地（可选）：如酒店名、火车站..."
                style={{
                flex: 1, background: 'none', border: 'none', outline: 'none',
                color: 'var(--text-dim)', fontSize: 13, fontFamily: 'var(--font-serif)', minWidth: 0,
                }}
            />
            </div>

            {/* 热搜词 - 初始页focused时显示，结果页始终显示 */}
            <AnimatePresence>
            {(focused || hasResult) && (
                <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                style={{ borderTop: '1px solid var(--border)', overflow: 'hidden' }}
                >
                {!hasResult && (
                    <div style={{
                    padding: '8px 16px 4px',
                    fontSize: 11, color: 'var(--text-muted)', letterSpacing: 2
                    }}>
                    试试这些
                    </div>
                )}
                {hasResult && (
                    <div style={{
                    padding: '8px 16px 4px',
                    fontSize: 11, color: 'var(--text-muted)', letterSpacing: 2
                    }}>
                    换一个试试
                    </div>
                )}
                {SUGGESTIONS.map((s, i) => (
                    <div
                    key={i}
                    onMouseDown={() => {
                        setInput(s)
                        setFocused(false)
                        if (hasResult) onSearch(s, startLocation.trim())
                    }}
                    style={{
                        padding: '9px 16px', cursor: 'pointer',
                        color: 'var(--text-dim)', fontSize: 12, fontFamily: 'var(--font-serif)',
                        borderBottom: i < SUGGESTIONS.length - 1 ? '1px solid var(--border)' : 'none',
                        transition: 'all 0.15s',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,107,0,0.08)'; e.currentTarget.style.color = 'var(--orange)' }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'var(--text-dim)' }}
                    >
                    <span style={{ marginRight: 8, opacity: 0.5 }}>↗</span>{s}
                    </div>
                ))}
                </motion.div>
            )}
            </AnimatePresence>
        </div>
        </div>
    )
}