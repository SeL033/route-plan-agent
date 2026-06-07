import { motion } from 'framer-motion'

export default function OpeningAnimation() {
    return (
        <motion.div
            className="opening"
            initial={{ opacity: 1 }}
            animate={{ opacity: 0, pointerEvents: 'none' }}
            transition={{ delay: 2.8, duration: 0.7 }}
        >
            <motion.div
                className="bus-window"
                initial={{ scale: 1.08 }}
                animate={{ scale: 1 }}
                transition={{ duration: 2.4, ease: 'easeOut' }}
            >
                <motion.div
                    className="window-city"
                    initial={{ scale: 1.6, y: 120 }}
                    animate={{ scale: 0.74, y: -52 }}
                    transition={{ duration: 2.7, ease: [0.16, 1, 0.3, 1] }}
                >
                    <span className="sun" />
                    <span className="hill hill-a" />
                    <span className="hill hill-b" />
                    <span className="tower tower-a" />
                    <span className="tower tower-b" />
                    <span className="tower tower-c" />
                    <span className="road-line road-one" />
                    <span className="road-line road-two" />
                </motion.div>
                <motion.div
                    className="window-frame"
                    animate={{ opacity: [1, 1, 0], scale: [1, 1, 1.8] }}
                    transition={{ duration: 2.7, times: [0, 0.65, 1] }}
                />
            </motion.div>
            <motion.div
                className="opening-copy"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: [0, 1, 1, 0], y: [16, 0, 0, -12] }}
                transition={{ duration: 2.7, times: [0, 0.25, 0.78, 1] }}
            >
                从车窗出发，把城市慢慢展开
            </motion.div>
        </motion.div>
    )
}
