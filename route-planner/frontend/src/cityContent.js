export const CITY_ALIASES = {
    '上海': ['上海', 'shanghai'],
    '北京': ['北京', 'beijing', 'peking'],
    '成都': ['成都', 'chengdu'],
    '珀斯': ['珀斯', 'perth'],
    '墨尔本': ['墨尔本', 'melbourne'],
    '悉尼': ['悉尼', 'sydney'],
    '广州': ['广州', 'guangzhou', 'canton'],
    '深圳': ['深圳', 'shenzhen'],
    '杭州': ['杭州', 'hangzhou'],
    '南京': ['南京', 'nanjing'],
    '西安': ['西安', 'xian', "xi'an"],
    '重庆': ['重庆', 'chongqing'],
    '新加坡': ['新加坡', 'singapore'],
    '东京': ['东京', 'tokyo'],
    '首尔': ['首尔', 'seoul'],
}

export const CITY_FOODS = {
    '上海': ['生煎', '小笼包', '本帮菜', '南翔馒头'],
    '北京': ['烤鸭', '铜锅涮肉', '爆肚', '胡同小吃'],
    '成都': ['火锅', '担担面', '夫妻肺片', '甜水面'],
    '珀斯': ['海港早午餐', '精酿啤酒', '澳式咖啡'],
    '墨尔本': ['澳式咖啡', '早午餐', '市场海鲜', '意面'],
    '悉尼': ['海鲜', '澳式早午餐', '港湾餐厅'],
    '广州': ['早茶', '烧腊', '肠粉', '糖水'],
    '深圳': ['粤式早茶', '沙井生蚝', '海鲜烧烤'],
    '杭州': ['西湖醋鱼', '小笼包', '龙井虾仁', '杭帮菜'],
    '南京': ['鸭血粉丝汤', '盐水鸭', '秦淮小吃', '汤包'],
    '西安': ['肉夹馍', '羊肉泡馍', '凉皮', '灌汤包'],
    '重庆': ['火锅', '小面', '酸辣粉', '江湖菜'],
    '新加坡': ['叻沙', '海南鸡饭', '辣椒螃蟹', '肉骨茶'],
    '东京': ['拉面', '寿司', '天妇罗', '抹茶甜点'],
    '首尔': ['烤肉', '参鸡汤', '炸鸡啤酒', '绿豆煎饼'],
}

export function detectCity(text = '') {
    const lower = text.toLowerCase()
    for (const [city, aliases] of Object.entries(CITY_ALIASES)) {
        if (aliases.some(alias => lower.includes(alias))) return city
    }
    return '上海'
}

export function travelImage(name, city = '') {
    return seededPhoto(`${city}-${name}-travel-landmark`, 640, 420)
}

export function foodImage(food, city = '') {
    return seededPhoto(`${city}-${food}-food-restaurant`, 480, 320)
}

export function fallbackImage(label = 'route') {
    const safe = String(label).replace(/[<>&"]/g, '')
    const hue = hashCode(safe) % 360
    const accent = `hsl(${hue}, 48%, 48%)`
    const deep = `hsl(${(hue + 42) % 360}, 42%, 34%)`
    return `data:image/svg+xml;utf8,${encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 420">
            <defs>
                <linearGradient id="sky" x1="0" x2="1" y1="0" y2="1">
                    <stop offset="0" stop-color="#bfe8ee"/>
                    <stop offset="0.55" stop-color="#dff1dd"/>
                    <stop offset="1" stop-color="#fff1c9"/>
                </linearGradient>
            </defs>
            <rect width="640" height="420" fill="url(#sky)"/>
            <circle cx="528" cy="82" r="38" fill="#f4c95d" opacity="0.88"/>
            <path d="M0 305 C90 250 145 278 220 238 C290 201 348 236 420 196 C500 151 570 192 640 150 L640 420 L0 420Z" fill="${accent}"/>
            <path d="M0 350 C110 315 180 338 270 300 C360 262 458 310 640 246 L640 420 L0 420Z" fill="${deep}" opacity="0.82"/>
            <path d="M100 262 C180 246 258 244 336 260 C416 277 494 276 570 252" fill="none" stroke="#fffaf0" stroke-width="16" stroke-linecap="round" opacity="0.72"/>
            <text x="42" y="78" font-family="Arial, sans-serif" font-size="34" font-weight="700" fill="#274047">${safe}</text>
        </svg>
    `)}`
}

function seededPhoto(seed, width, height) {
    return `https://picsum.photos/seed/${encodeURIComponent(seed)}/${width}/${height}`
}

function hashCode(text) {
    let hash = 0
    for (let i = 0; i < text.length; i += 1) {
        hash = ((hash << 5) - hash + text.charCodeAt(i)) | 0
    }
    return Math.abs(hash)
}