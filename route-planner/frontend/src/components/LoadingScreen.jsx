import { motion } from 'framer-motion'

const STEPS = [
    '分析出行意图...',
    '搜索周边景点...',
    '查询用户评价...',
    '计算最优路线...',
    '生成个性化方案...',
    ]

    export default function LoadingScreen() {
    return (
    <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
        position: 'absolute', inset: 0, zIndex: 80,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'rgba(10,10,10,0.7)', backdropFilter: 'blur(4px)',
        flexDirection: 'column', gap: 24
        }}
    >
        {/* 动画圆圈 */}
        <div style={{ position: 'relative', width: 80, height: 80 }}>
        {[0, 1, 2].map(i => (
            <motion.div
            key={i}
            animate={{ scale: [1, 1.5, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ duration: 1.8, delay: i * 0.6, repeat: Infinity }}
            style={{
                position: 'absolute', inset: 0, borderRadius: '50%',
                border: '2px solid var(--orange)',
            }}
            />
        ))}
        <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            fontSize: 28
        }}>
            🗺
        </div>
        </div>

        {/* 步骤文字 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
        {STEPS.map((step, i) => (
            <motion.div
            key={i}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: [0, 1, 0.3], x: 0 }}
            transition={{
                delay: i * 0.8,
                duration: 0.8,
                opacity: { times: [0, 0.3, 1], duration: 3 }
            }}
            style={{
                color: 'var(--text-dim)', fontSize: 13,
                fontFamily: 'var(--font-mono)',
                display: 'flex', alignItems: 'center', gap: 8
            }}
            >
            <motion.span
                animate={{ opacity: [0, 1] }}
                transition={{ delay: i * 0.8 + 0.2 }}
                style={{ color: 'var(--orange)' }}
            >
                ›
            </motion.span>
            {step}
            </motion.div>
        ))}
        </div>
    </motion.div>
    )
}