import { motion } from 'framer-motion'

const STEPS = [
    '分析出行意图',
    '搜索城市 POI',
    '读取用户评价',
    '避开回头路',
    '生成路线手账',
]

export default function LoadingScreen() {
    return (
        <motion.div
            className="loading-screen"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            <div className="loading-card">
                <div className="loading-map">
                    <motion.span
                        className="loading-bus"
                        animate={{ x: [0, 98, 42, 132], y: [34, 10, 72, 42] }}
                        transition={{ duration: 2.6, repeat: Infinity, ease: 'easeInOut' }}
                    />
                    <svg viewBox="0 0 180 110">
                        <path d="M14 72 C 46 16, 76 22, 94 58 S 138 92, 166 34" fill="none" stroke="#2aa89b" strokeWidth="4" strokeDasharray="8 8" strokeLinecap="round" />
                    </svg>
                </div>
                <div className="loading-steps">
                    {STEPS.map((step, i) => (
                        <motion.span
                            key={step}
                            animate={{ opacity: [0.35, 1, 0.35] }}
                            transition={{ delay: i * 0.28, duration: 1.4, repeat: Infinity }}
                        >
                            {step}
                        </motion.span>
                    ))}
                </div>
            </div>
        </motion.div>
    )
}
