#!/usr/bin/env python3
"""Step 3: AI analysis with Chinese translations for all segments.

Reads parsed prompts from stdin or file, outputs analysis JSON.
AI (Claude) provides:
- text_zh: faithful Chinese translation for each segment
- text_zh_full: natural Chinese paragraph for the full prompt
- type_id: semantic category
- words: difficult English words with positions
"""

import json, sys, re

INPUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/prompt_parsed.json'
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/prompt_analysis.json'

parsed = json.load(open(INPUT))

# ============================================================
# COMPREHENSIVE CHINESE TRANSLATIONS (by Claude AI)
# ============================================================
ZH = {}

# --- Opening (1) ---
ZH['Generate epic Unreal Engine 5 fantasy landscape'] = '生成史诗级虚幻引擎5奇幻场景'

# --- Photography (6) ---
ZH['cinematic environmental photography'] = '电影级环境摄影'
ZH['cinematic wide-angle photography'] = '电影级广角摄影'
ZH['cinematic wide photography'] = '电影级广角摄影'
ZH['cinematic low-angle photography'] = '电影级低角度摄影'
ZH['cinematic aerial photography'] = '电影级航拍摄影'
ZH['cinematic telephoto photography'] = '电影级长焦摄影'
ZH['cinematic close environmental photography'] = '电影级近景环境摄影'

# --- Lighting (97) ---
ZH['stormy overcast daylight'] = '暴风雨阴天光线'
ZH['golden morning light breaking through canopy'] = '金色晨光穿透树冠'
ZH['harsh midday desert sun'] = '正午烈日沙漠光线'
ZH['pale overcast dawn light'] = '苍白阴天黎明光线'
ZH['cold blue twilight'] = '寒冷蓝色暮光'
ZH['warm late afternoon sun'] = '温暖午后斜阳'
ZH['bright noon sun'] = '明亮正午阳光'
ZH['soft diffused spring daylight'] = '柔和漫射春日光线'
ZH['grey misty dawn'] = '灰色薄雾黎明'
ZH['dark stormy twilight'] = '暗沉暴风雨暮光'
ZH['dark night with vivid aurora'] = '极光绚丽的黑夜'
ZH['deep dusk with volcanic glow'] = '火山红光的深邃黄昏'
ZH['frozen arctic daylight'] = '冰冻极地日光'
ZH['crisp cold daylight'] = '清冷日光'
ZH['warm direct sunlight'] = '温暖直射阳光'
ZH['soft diffused light through clouds'] = '云层间柔和漫射光'
ZH['clear starry night'] = '晴朗星空之夜'
ZH['bright golden morning'] = '明亮金色清晨'
ZH['warm golden afternoon light'] = '温暖金色午后光线'
ZH['heavy fog and diffused light'] = '浓雾与漫射光'
ZH['dark purple twilight'] = '深紫色暮光'
ZH['soft ethereal twilight'] = '柔和空灵暮光'
ZH['misty dawn light'] = '薄雾黎明光线'
ZH['rain and lightning flashes'] = '雨夜闪电'
ZH['firelight and ember glow'] = '火光与余烬'
ZH['candlelight and shadow'] = '烛光与暗影'
ZH['cold blue daylight'] = '寒冷蓝色日光'
ZH['bright moonlight'] = '明亮月光'
ZH['soft warm sunset'] = '柔和温暖日落'
ZH['blue hour twilight'] = '蓝调暮光时分'
ZH['cool overcast daylight'] = '清冷阴天光线'
ZH['warm sunrise light'] = '温暖日出光线'
ZH['dusty desert twilight'] = '沙尘沙漠暮光'
ZH['crisp cold clear mountain light'] = '清冷高山光线'
ZH['bright clear summer daylight'] = '明亮夏日光线'
ZH['bright clear coastal light'] = '明亮海岸光线'
ZH['filtered green canopy light'] = '穿透绿荫的光线'
ZH['soft diffused morning light'] = '柔和漫射晨光'
ZH['soft misty dawn light'] = '柔和薄雾黎明光'
ZH['soft golden dawn light'] = '柔和金色黎明光'
ZH['soft pink dawn light'] = '柔和粉色黎明光'
ZH['soft pink frosty dawn'] = '柔和粉色霜冻黎明'
ZH['soft pastel dawn light'] = '柔和粉彩黎明光'
ZH['soft diffused daylight'] = '柔和漫射日光'
ZH['soft bioluminescent glow'] = '柔和生物荧光'
ZH['soft tropical filtered light'] = '热带柔和过滤光'
ZH['warm golden hour'] = '温暖黄金时刻'
ZH['warm hazy afternoon'] = '温暖朦胧午后'
ZH['warm hazy sunset'] = '温暖朦胧日落'
ZH['warm backlit sunset'] = '温暖逆光日落'
ZH['warm fiery sunset'] = '温暖炽热日落'
ZH['warm low daylight'] = '温暖低位日光'
ZH['warm radiant sunrise'] = '温暖灿烂日出'
ZH['warm dusk light against cold snow'] = '温暖暮光映照冷雪'
ZH['warm golden afternoon light'] = '温暖金色午后光'
ZH['warm late light'] = '温暖晚光'
ZH['warm directional canyon light'] = '温暖定向峡谷光'
ZH['cool diffused daylight'] = '清冷漫射日光'
ZH['cool moonlit night'] = '清冷月光夜'
ZH['cool cavern ambient glow'] = '洞穴清冷环境光'
ZH['cool crystalline ambient glow'] = '水晶清冷环境光'
ZH['cool filtered cave light'] = '洞穴清冷过滤光'
ZH['cool glowing blue ambient light'] = '清冷蓝色环境荧光'
ZH['clear bright high-altitude light'] = '高海拔明亮光线'
ZH['clear cool daylight'] = '清朗凉爽日光'
ZH['cold faint blue light'] = '寒冷微弱蓝光'
ZH['cold flat arctic daylight'] = '寒冷平坦极地日光'
ZH['cold pale arctic light'] = '寒冷苍白极地光'
ZH['stormy grey daylight'] = '暴风雨灰色日光'
ZH['moody overcast daylight'] = '阴郁阴天光线'
ZH['moody overcast light'] = '阴郁阴沉光线'
ZH['overcast cold daylight'] = '阴天寒冷日光'
ZH['overcast cool daylight'] = '阴天凉爽日光'
ZH['grey stormy daylight'] = '灰色暴风雨日光'
ZH['pale cold overcast light'] = '苍白寒冷阴天光'
ZH['pale grey eerie daylight'] = '苍白灰色诡异日光'
ZH['pale steamy morning light'] = '苍白蒸汽晨光'
ZH['flat cold overcast light'] = '平坦寒冷阴天光'
ZH['soft overcast post-rain light'] = '雨后柔和阴天光'
ZH['harsh bright daylight'] = '强烈明亮日光'
ZH['dim blue blizzard light'] = '昏暗蓝色暴风雪光'
ZH['dim grey ash-filtered light'] = '灰烬过滤昏暗光线'
ZH['dim melancholic dusk'] = '昏暗忧郁黄昏'
ZH['dim pre-storm light'] = '暴风雨前昏暗光线'
ZH['dim rainy storm light'] = '昏暗暴雨光线'
ZH['dim smoky dusk'] = '昏暗烟尘黄昏'
ZH['dim torch and ambient light'] = '昏暗火炬环境光'
ZH['dramatic dark twilight'] = '戏剧性黑暗暮光'
ZH['dramatic light above storm clouds'] = '暴风云上的戏剧性光线'
ZH['dramatic storm light with lightning'] = '闪电交加的戏剧性光线'
ZH['dramatic storm-edge light'] = '暴风边缘的戏剧性光线'
ZH['dramatic stormy twilight'] = '戏剧性暴风雨暮光'
ZH['dramatic surreal twilight'] = '戏剧性超现实暮光'
ZH['faint blue ambient light'] = '微弱蓝色环境光'
ZH['golden backlit morning light'] = '金色逆光晨光'
ZH['golden hour above a sea of clouds'] = '云海之上的黄金时刻'
ZH['golden hour above the clouds'] = '云层之上的黄金时刻'
ZH['glowing orange dusk'] = '夕阳橙光黄昏'
ZH['dusty golden dusk'] = '沙尘金色黄昏'
ZH['eerie grey-green dusk'] = '诡异灰绿色黄昏'
ZH['fiery night with eruption glow'] = '火山喷发炽热之夜'
ZH['deep blue moonlit night'] = '深蓝月光夜'
ZH['dark blue snowy night'] = '深蓝雪夜'
ZH['deep blue night with bioluminescence'] = '深蓝生物荧光夜'
ZH['dark rainy night with warm lamplight'] = '温暖街灯的暗雨夜'
ZH['deep orange sunset'] = '深橙色日落'
ZH['stormy sunset light'] = '暴风雨日落光线'
ZH['deep red glow from below'] = '来自下方的深红光芒'
ZH['deep red volcanic dusk'] = '深红火山黄昏'
ZH['hazy hot afternoon light'] = '朦胧炎热午后光线'
ZH['hazy overcast morning'] = '朦胧阴天早晨'
ZH['vivid night aurora light'] = '绚丽极光之夜'
ZH['dappled green forest light'] = '斑驳绿林光影'
ZH['ominous dusty light'] = '不祥沙尘光线'
ZH['bright post-rain daylight'] = '雨后明亮日光'
ZH['bright shaft of daylight'] = '明亮光柱'

# --- Scene descriptions (307) ---
ZH['ancient colossal temple ruins built into towering cliffs'] = '建于高耸悬崖上的古老巨型神庙废墟'
ZH['massive waterfalls crashing into deep valleys'] = '巨大瀑布奔泻入深邃山谷'
ZH['dark pine forests'] = '黑暗松林'
ZH['mist-covered mountains'] = '薄雾笼罩的山脉'
ZH['reflective wet stone roads'] = '反光的湿润石板路'
ZH['half-sunken stone pyramid swallowed by dense jungle'] = '被茂密丛林吞没的半沉石质金字塔'
ZH['vines and roots cracking carved walls'] = '藤蔓与树根在雕刻墙壁上蔓延开裂'
ZH['shafts of god rays through humid mist'] = '丁达尔光束穿过潮湿雾气'
ZH['colossal half-buried statue temple emerging from rolling dunes'] = '从起伏沙丘中浮现的巨型半埋神像神殿'
ZH['cracked sandstone columns'] = '开裂的砂岩柱'
ZH['drifting sand and heat haze'] = '飘动的沙尘与热浪'
ZH['ancient coastal ruins revealed at low tide'] = '退潮时显露的古老海岸遗迹'
ZH['barnacle-covered broken arches'] = '藤壶覆盖的断裂拱门'
ZH['shallow reflective tidal pools'] = '浅水反光的潮汐池'
ZH['frozen ancient altar on a windswept mountain summit'] = '屹立于迎风雪山之巅的冰冻古老祭坛'
ZH['ice-crusted carved pillars'] = '冰封的雕刻石柱'
ZH['blowing snow and frost mist'] = '飞雪与霜雾'
ZH['mist-wrapped mountaintop monastery library'] = '云雾缭绕的山顶修道院图书馆'
ZH['towering gothic cathedral on a misty mountain peak'] = '雾中山顶上的高耸哥特式大教堂'
ZH['cluster of towering desert rock spires under a brilliant milky way'] = '璀璨银河下耸立的沙漠石笋群'
ZH['abandoned mine descending into a glowing lava abyss'] = '废弃矿洞向下延伸至炽热熔岩深渊'
ZH['frozen valley beneath swirling green and violet northern lights'] = '绿色与紫色极光旋舞下的冰封山谷'
ZH['single sharp tower peak piercing above a churning sea of storm clouds'] = '孤峰突破翻涌暴风云海的尖锐塔峰'
ZH['massive multi-tiered cascading waterfalls down a jungle cliff'] = '丛林悬崖上多层级的巨大瀑布群'
ZH['subterranean forest of glowing mushrooms and floating spores'] = '发光蘑菇与漂浮孢子的地下森林'
ZH['ancient manor estate at the end of rolling golden wheat fields'] = '起伏金色麦田尽头的古老庄园'
ZH['massive snow-covered glacier carving a deep crevasse valley'] = '覆盖深雪的巨型冰川凿出的深邃裂缝山谷'
ZH['ancient amphitheater inside a vast underground cavern'] = '巨大地下洞穴中的古老圆形剧场'
ZH['black obsidian temple surrounded by slow rivers of lava'] = '被缓慢熔岩河环绕的黑色黑曜石神殿'
ZH['grand castle on an island surrounded by a calm reflective lake'] = '环湖孤岛上反射如镜的宏伟城堡'
ZH['terracotta walled city beside a desert oasis with palms'] = '沙漠绿洲旁棕榈环绕的陶土城墙之城'
ZH['sacred site of floating glowing monoliths circling a central altar'] = '悬浮发光的巨石环绕中央祭坛的圣地'
ZH['colossal ice-encrusted castle rising from an endless snow field'] = '无垠雪原上升起的覆冰巨型城堡'
ZH['field of derelict windmills on a cracked wasteland plain'] = '开裂荒原上废弃风车群'
ZH['enormous glowing lava fissure splitting cracked dark terrain'] = '巨大炽热熔岩裂隙撕裂黑暗大地'
ZH['perfectly calm mirror-like lagoon reflecting sky and distant islands'] = '天空与远岛倒映的完美平静镜面潟湖'
ZH['beach with glowing bioluminescent waves rolling onto dark sand'] = '发光生物荧光波浪涌向暗色沙滩的海滩'
ZH['geothermal basin of colorful sulfur hot springs and steaming pools'] = '彩色硫磺温泉与蒸汽池的地热盆地'
ZH['erupting volcano lighting up a vast black lava plain'] = '喷发火山照亮广阔的黑色熔岩平原'
ZH['lone watchtower on a rugged storm-battered coast'] = '暴风雨肆虐的崎岖海岸上孤立的瞭望塔'
ZH['illuminated mountain castle glowing warm against a snowy night'] = '雪夜中温暖发光的山顶城堡'
ZH['massive stepped stone fortress carved along a sheer cliff edge'] = '沿陡峭悬崖雕凿的巨大阶梯式石头堡垒'
ZH['ancient arched stone bridge spanning a bottomless misty chasm'] = '跨越无底雾渊的古老石拱桥'
ZH['hidden treehouse village built among colossal forest trees'] = '建于巨型森林树木间的隐秘树屋村落'
ZH['frozen lake dotted with frost-covered bare trees'] = '散落着覆霜枯树的冰封湖泊'
ZH['small snow-covered village among pine forest below white mountains'] = '雪山脚下松林间的覆雪小村庄'
ZH['sky city built across a colossal natural stone arch above clouds'] = '建于云端巨型天然石拱之上的天空之城'
ZH['endless rolling giant sand dunes glowing red at sunset'] = '日落时红光闪耀的无尽起伏巨型沙丘'
ZH['massive jungle sinkhole with a beam of light into a green cavern below'] = '光束射入下方绿色洞穴的巨大丛林天坑'
ZH['ancient elven altar entwined in colossal tree roots'] = '缠绕于巨型树根中的古老精灵祭坛'
ZH['labyrinth of narrow wind-carved red rock canyons'] = '风蚀红色岩壁峡谷迷宫'
ZH['single colossal monolith standing on a barren windswept plateau'] = '荒芜迎风高原上矗立的巨型独石'
ZH['dark fortress on an island in the middle of a glowing lava lake'] = '炽热熔岩湖中央岛屿上的黑暗堡垒'
ZH['lone wooden cabin on a vast snow plain in a howling blizzard'] = '暴风雪呼啸的广阔雪原上的孤独木屋'
ZH['highland village with rising chimney smoke at the foot of snow mountains'] = '雪山脚下炊烟袅袅的高原村落'
ZH['inside a giant sea cave with surging glowing turquoise water'] = '巨大海蚀洞内翻涌的发光碧绿海水'
ZH['beach with...'] = '...'
ZH['deep blue fjord channel between towering sheer cliffs'] = '高耸峭壁间的深蓝峡湾水道'
ZH['ancient canal city wrapped in morning mist'] = '晨雾笼罩的古老运河之城'
ZH['ancient cliff-carved city cut into a deep red canyon'] = '深红色峡谷中开凿的古老崖壁城市'
ZH['single colossal...'] = '...'
ZH['hidden grotto behind a hanging vine waterfall'] = '悬垂藤蔓瀑布后的隐秘石窟'
ZH['colossal ancient creature skeleton in a dry cracked riverbed'] = '干涸开裂河床中的巨型远古生物骨架'
ZH['ruined hilltop fortress with crumbling walls and broken towers'] = '残垣断壁与破碎塔楼的废墟山顶要塞'
ZH['moss-covered gorge with a clear rushing stream'] = '苔藓覆盖的峡谷中清澈奔流的溪水'
ZH['towering black sea stacks battered by enormous crashing waves'] = '被巨浪冲击的高耸黑色海蚀柱'
ZH['cluster of towering red sandstone natural arches'] = '高耸的红色砂岩天然拱门群'
ZH['vast cracked salt flat with a lone ruined structure'] = '广阔开裂盐滩上孤立的废墟建筑'
ZH['ancient towering redwood forest in deep autumn'] = '深秋中的古老高耸红杉林'
ZH['abandoned monastery cloister overgrown with ivy'] = '常春藤蔓生的废弃修道院回廊'
ZH['shallow tidal flats scattered with old shipwreck hulls'] = '浅潮滩上散落的古老沉船残骸'
ZH['vast field of hexagonal basalt columns by a stormy sea'] = '暴风雨海边广阔的六角形玄武岩柱群'
ZH['flooded ancient city plaza under heavy rain'] = '大雨中淹没的古老城市广场'
ZH['interior of a vast glacial ice cave'] = '广阔冰川洞穴的内部'
ZH['network of rope bridges connecting floating mountain fragments'] = '连接悬浮山体碎片的绳桥网络'
ZH['skyscraper-like'] = '摩天楼般'
ZH['dense field of towering karst limestone pinnacles'] = '高耸的喀斯特石灰岩尖峰密林'
ZH['black volcanic sand desert under a pale moon'] = '苍白月光下的黑色火山沙沙漠'
ZH['surreal rainforest with colossal glowing mushrooms'] = '巨型发光蘑菇的超现实雨林'
ZH['vast alpine meadow blooming with wildflowers'] = '野花盛开的广阔高山草甸'
ZH['enormous limestone cavern with an underground river'] = '拥有地下河的巨大石灰岩洞穴'
ZH['silent snow-laden coniferous forest'] = '寂静的覆雪针叶林'
ZH['forest buried under thick grey volcanic ash'] = '被厚厚灰色火山灰掩埋的森林'
ZH['towering frozen waterfall hanging from a snow-dusted cliff'] = '冰雪覆盖悬崖上悬挂的高耸冰冻瀑布'
ZH['withered dead forest of bare twisted trees in thick fog'] = '浓雾中扭曲枯树的凋零死寂森林'
ZH['massive glacier calving face meeting dark ocean'] = '巨型冰川崩解面与黑暗海洋的交汇'
ZH['chain of floating islands with waterfalls pouring into the sky'] = '瀑布倾泻入天际的浮空岛屿链'
ZH['sky-high canyon with waterfalls falling into clouds and arcing rainbows'] = '瀑布落入云端拱起彩虹的天际峡谷'
ZH['vast underground hall filled with giant glowing crystals'] = '布满巨大发光水晶的广阔地下殿堂'
ZH['abandoned stone desert village as a towering sandstorm wall approaches'] = '高耸沙暴墙逼近的废弃石头沙漠村庄'
ZH['enchanted forest glade lit by swarms of fireflies and glowing mushrooms'] = '萤火虫群与发光蘑菇照亮的魔法森林空地'
ZH['jagged razorback mountain ridge under heavy storm clouds'] = '厚重暴风云下锯齿状的陡峭山脊'
ZH['mountain shrine path under blooming cherry blossom trees'] = '樱花盛开的山间神社小径'
ZH['narrow cobblestone old-town street glistening in the rain'] = '雨中闪耀的狭窄鹅卵石老城街道'
ZH['immense stairway rising through clouds to a golden temple in the sky'] = '穿越云层通往天际金色神殿的宏伟阶梯'
ZH['vast wetland of tall reeds in low morning mist'] = '低矮晨雾中广阔的高芦苇湿地'
ZH['sky harbor with moored airships silhouetted against a glowing sky'] = '停泊飞艇在发光天空中的剪影天空港湾'
ZH['shattered landscape torn by a glowing rift in space'] = '被太空发光裂缝撕裂的破碎大地'
ZH['ruins of a colossal withered world-tree dominating a barren plain'] = '占据荒芜平原的巨型枯萎世界树残骸'
ZH['scorched battlefield with smoldering embers and broken siege ruins'] = '余烬闷烧与破碎攻城废墟的焦灼战场'
ZH['narrow wooden plank path clinging to a lone towering peak'] = '紧贴孤立高峰的狭窄木板栈道'
ZH['vast thin water layer over a salt flat perfectly mirroring the milky way'] = '盐滩上完美倒映银河的薄水层'
ZH['winding mountain switchback road seen from above in thin fog'] = '薄雾中俯瞰蜿蜒山路的之字形弯道'
ZH['layered terraced valley wrapped in low morning mist'] = '低矮晨雾缠绕的层叠梯田山谷'
ZH['white birch forest pierced by low sun through ground fog'] = '低日照穿透地面雾的白桦林'
ZH['sinister black tower half-sunk in a foggy swamp'] = '半沉于雾沼的邪恶黑塔'
ZH['colorful fishing village stacked up a steep coastal cliff'] = '陡峭海岸悬崖上层叠的彩色渔村'
ZH['turquoise crater lake fed by tall ribbon waterfalls'] = '高处丝带瀑布注入的碧绿火山口湖'
ZH['vast ancient underground city hall with colossal carved stone doors'] = '拥有巨型雕刻石门的广阔地下古城大厅'
ZH['ruined ancient lighthouse on a fractured sea cliff'] = '断裂海崖上的废墟古老灯塔'
ZH['ruined floating platform at the edge of a massive storm wall'] = '巨大暴风墙边缘的废墟悬浮平台'
ZH['single sharp tower peak piercing above a churning sea of storm clouds'] = '孤峰突破翻涌暴风云海的塔峰'
ZH['rows of leaning ancient stone idols sunk in a dark swamp'] = '沉入黑暗沼泽的成排倾斜古老石像'
ZH['ancient arched stone bridge spanning a bottomless misty chasm'] = '跨越无底雾渊的古老石拱桥'
ZH['winding ramparts'] = '蜿蜒的城墙'
ZH['carved stone seating'] = '雕刻的石座'
ZH['glowing turquoise pool'] = '发光的碧绿水潭'
ZH['dark muddy ground'] = '黑暗的泥泞地面'
ZH['steep volcanic rim walls'] = '陡峭的火山口壁'
ZH['mineral crusts'] = '矿物结壳'
ZH['distant smoking cones'] = '远处冒烟的锥形山'
ZH['layered balconies and stairways'] = '层叠的阳台与阶梯'
ZH['sunlight on the summit'] = '山顶的阳光'
ZH['stacked wooden and stone pavilions'] = '层叠的木石亭台'
ZH['rope bridges and lanterns'] = '绳桥与灯笼'
ZH['boats in a small harbor'] = '小船停泊的小港'
ZH['stone bridges and gondolas'] = '石桥与贡多拉'
ZH['dark pine forests'] = '黑暗的松林'
ZH['overgrown courtyards'] = '杂草丛生的庭院'
ZH['flying buttresses and spires'] = '飞扶壁与尖塔'
ZH['stone houses and prayer flags'] = '石屋与经幡'
ZH['suspended bridges and towers'] = '悬索桥与塔楼'
ZH['frozen spires and battlements'] = '冰冻的尖塔与城垛'
ZH['arched stone walkways'] = '拱形石步道'
ZH['stone lanterns and torii gate'] = '石灯笼与鸟居'
ZH['mud-brick towers'] = '泥砖塔楼'
ZH['drifted snow banks'] = '漂移的雪堆'
ZH['half-buried buildings'] = '半埋的建筑'
ZH['fallen pillars'] = '倒塌的石柱'
ZH['glowing windows and chimney smoke'] = '发光的窗户与烟囱炊烟'
ZH['warm window lights'] = '温暖的窗光'
ZH['glowing lanterns and shop windows'] = '发光的灯笼与店铺橱窗'
ZH['banners in the wind'] = '风中飘扬的旗帜'
ZH['wooden docks on a cliff'] = '悬崖上的木栈码头'
ZH['broken spiral stairs'] = '断裂的螺旋楼梯'
ZH['blowing snow and faint window glow'] = '吹雪与微弱的窗光'
ZH['dark pine forests'] = '黑暗松林'
ZH['flake snow and window light'] = '雪花与窗光'

# Scene descriptions continued — more complex ones
ZH['floating broken terrain shards'] = '漂浮的破碎地形碎片'
ZH['swirling energy and dust'] = '旋转的能量与尘埃'
ZH['alien crystal wasteland under colorful auroras'] = '彩色极光下的外星水晶荒原'
ZH['distant floating land'] = '远处悬浮的大地'
ZH['glowing crystal spires from cracked ground'] = '从开裂地面生长的发光水晶尖塔'
ZH['dense field of towering karst limestone pinnacles'] = '高耸喀斯特石灰岩尖峰群'
ZH['crumbling stone falling into the void'] = '落入虚空的碎石'
ZH['glowing lava rivers and ember clouds'] = '发光的熔岩河与余烬云'
ZH['heat shimmer'] = '热气蒸腾'
ZH['distant floating peaks'] = '远处悬浮的山峰'
ZH['deeper spires fading into severe haze'] = '更深处的尖塔渐隐入浓雾'
ZH['endless field of razor-sharp shattered glass shards'] = '无边无际的锋利玻璃碎片原野'
ZH['alien coral formations'] = '外星珊瑚构造'
ZH['blue ice columns'] = '蓝色冰柱'
ZH['towering ice walls'] = '高耸的冰墙'
ZH['cracked ice surface'] = '开裂的冰面'
ZH['drifted snow banks'] = '漂移雪堆'
ZH['ice-coated rock formations'] = '冰封的岩层'
ZH['frozen floor'] = '冰冻的地面'
ZH['frosted spires'] = '覆霜的尖塔'
ZH['low blowing snow'] = '低空吹雪'
ZH['sea of clouds below'] = '下方的云海'
ZH['distant jagged summits'] = '远处锯齿状的山峰'
ZH['steep forested slopes'] = '陡峭的森林坡地'
ZH['snow-covered peaks'] = '白雪覆盖的山峰'
ZH['sharp shadow ridgelines'] = '锐利的阴影山脊线'
ZH['low cloud ceiling'] = '低矮的云层顶盖'
ZH['distant blue mountains'] = '远处的蓝色山脉'
ZH['distant snow mountains'] = '远处的雪山'
ZH['distant ridges fading into haze'] = '远处山脊渐隐入雾'
ZH['mist pooling between spires'] = '雾气汇聚于尖塔之间'
ZH['dark gathering clouds'] = '暗沉的积云'
ZH['lightning glow below'] = '下方闪电的微光'
ZH['lightning in dark clouds'] = '乌云中的闪电'
ZH['deep cloud chasms below'] = '下方深邃的云渊'
ZH['dramatic orange-on-dark contrast'] = '戏剧性的橙色与黑暗对比'
ZH['distant light shaft'] = '远处的光柱'
ZH['faint glow at the top'] = '顶部微弱的光芒'
ZH['faint horizon glow'] = '地平线微弱的辉光'
ZH['faint distant glow'] = '远处微弱的辉光'
ZH['soft cloud layers'] = '柔软的云层'
ZH['low drifting clouds'] = '低空飘浮的云'
ZH['drifting cloud wisps'] = '飘浮的云丝'
ZH['drifting clouds'] = '飘浮的云'
ZH['drifting clouds and birds'] = '飘浮的云与飞鸟'
ZH['drifting clouds below the peaks'] = '山峰下飘浮的云'
ZH['starry sky above'] = '上方的星空'
ZH['faint star field'] = '微弱的星空'
ZH['snow peaks behind'] = '背后的雪峰'
ZH['dark pine forests'] = '深色松林'
ZH['distant tree line'] = '远处的树线'
ZH['distant mountains'] = '远处的山脉'
ZH['dark twisted trees'] = '黑暗扭曲的树木'
ZH['charred bare trees'] = '烧焦的光秃树木'
ZH['faint fog between trunks'] = '树干间微弱的雾气'
ZH['hanging moss and fog'] = '悬挂的苔藓与雾气'
ZH['mist and dripping greenery'] = '雾气与滴水的绿植'
ZH['mist and sun shafts'] = '雾气与光柱'
ZH['soft god rays and mist'] = '柔和的丁达尔光与雾气'
ZH['soft god rays through leaves'] = '穿过树叶的柔和光柱'
ZH['falling leaves and god rays'] = '飘落的树叶与光柱'
ZH['glowing god rays'] = '发光的丁达尔光束'
ZH['fern-covered floor'] = '蕨类覆盖的地面'
ZH['soft snowfall'] = '柔和的落雪'
ZH['falling snow'] = '飘落的雪'
ZH['heavy snow on branches'] = '枝头厚厚的积雪'
ZH['frozen floor'] = '冰冻的地面'
ZH['scattered golden leaves'] = '散落的金色树叶'
ZH['drifting petals'] = '飘落的花瓣'
ZH['lush undergrowth'] = '茂密的林下植被'
ZH['lush cliff edges'] = '茂密的悬崖边缘'
ZH['lush green ledges'] = '茂密的绿色岩架'
ZH['moss and wildflowers in cracks'] = '裂缝中的苔藓与野花'
ZH['long tree shadows'] = '长长的树影'
ZH['long tree-lined path'] = '长长的林荫道'
ZH['wind-bent grass'] = '被风吹弯的草地'
ZH['dry grass bending in wind'] = '风中摇曳的干草'
ZH['dripping leaves and vines'] = '滴水的树叶与藤蔓'
ZH['hanging vines and waterfalls'] = '悬挂的藤蔓与瀑布'
ZH['dripping ceiling'] = '滴水的洞顶'
ZH['hanging stalactites'] = '悬挂的钟乳石'
ZH['towering stalactites and stalagmites'] = '高耸的钟乳石与石笋'
ZH['rocky ceiling'] = '岩石洞顶'
ZH['glowing moss and fireflies'] = '发光的苔藓与萤火虫'
ZH['glowing cracks and ember sparks'] = '发光的裂缝与火星'
ZH['faint glowing cracks'] = '微弱的发光裂缝'
ZH['faint glowing sap'] = '微弱的发光树液'
ZH['ember sparks'] = '余烬火星'
ZH['drifting light particles'] = '漂浮的光粒子'
ZH['dust in light beams'] = '光柱中的尘埃'
ZH['dust in golden light'] = '金色光线中的尘埃'
ZH['dust motes in golden light'] = '金色光线中的尘埃微粒'
ZH['soft dust in light'] = '光线中的柔和尘埃'
ZH['faint mist'] = '微弱的薄雾'
ZH['low mist'] = '低矮的薄雾'
ZH['low ground mist'] = '低矮的地面雾气'
ZH['faint morning mist'] = '微弱的晨雾'
ZH['drifting mist'] = '飘浮的雾气'
ZH['drifting fine mist'] = '飘浮的细雾'
ZH['drifting fog'] = '飘浮的浓雾'
ZH['drifting fog in the void'] = '虚空中飘浮的浓雾'
ZH['drifting frost mist'] = '飘浮的霜雾'
ZH['drifting dust'] = '飘浮的尘埃'
ZH['drifting smoke and ash'] = '飘浮的烟与灰'
ZH['drifting ash particles'] = '飘浮的灰烬微粒'
ZH['swirling dust'] = '旋转的尘埃'
ZH['rising heat and smoke'] = '升腾的热气与烟雾'
ZH['rising smoke'] = '升腾的烟雾'
ZH['smoke plumes'] = '烟柱'
ZH['rising thick steam'] = '升腾的浓密蒸汽'
ZH['rising heat haze'] = '升腾的热浪'
ZH['smoke and heat distortion'] = '烟雾与热气扭曲'
ZH['heat haze and sparks'] = '热浪与火星'
ZH['soft humid haze'] = '柔和的潮湿雾霭'
ZH['dense spray and rainbows'] = '浓密的水雾与彩虹'
ZH['steam rising from vents'] = '从裂口升腾的蒸汽'
ZH['low sea fog'] = '低矮的海雾'
ZH['drifting sea mist'] = '飘浮的海雾'
ZH['faint sea mist'] = '微弱的海雾'
ZH['drifting spray'] = '飘浮的水雾'
ZH['drifting spray mist'] = '飘浮的水雾'
ZH['flying sea spray and foam'] = '飞扬的海浪水雾与泡沫'
ZH['crashing waves'] = '冲击的海浪'
ZH['crashing waves and sea spray'] = '冲击的海浪与水雾'
ZH['crashing waves below'] = '下方冲击的海浪'
ZH['driving rain and wind'] = '狂风暴雨'
ZH['rain ripples and reflections'] = '雨滴涟漪与倒影'
ZH['faint reflections'] = '微弱的倒影'
ZH['reflections in wet stone'] = '湿润石面上的倒影'
ZH['reflective dark pools'] = '反光的暗色水潭'
ZH['reflective surfaces'] = '反光的表面'
ZH['golden reflections in wet sand'] = '湿润沙地上的金色倒影'
ZH['still black water reflections'] = '静默黑水中的倒影'
ZH['mirror-still channels'] = '镜面般平静的水道'
ZH['calm reflective water'] = '平静的反光水面'
ZH['winding river below'] = '下方蜿蜒的河流'
ZH['thin waterfalls down rock walls'] = '岩壁上细细的瀑布'
ZH['total stillness'] = '完全的静谧'
ZH['crisp clear air'] = '清冽的空气'
ZH['drifted snow banks'] = '漂移的雪堆'
ZH['frozen floor'] = '冰冻的地面'
ZH['translucent rippling blue walls'] = '半透明的蓝色波纹墙壁'
ZH['light filtering through ice'] = '光线透过冰层'
ZH['light beams from the entrance'] = '洞口射入的光束'
ZH['light beams hitting the walls'] = '投射在墙壁上的光束'
ZH['faint silhouettes deeper in mist'] = '雾中深处微弱的身影轮廓'
ZH['long shadows'] = '长长的影子'
ZH['long shadows across desert floor'] = '沙漠地面上长长的影子'
ZH['scattered ribs and skull'] = '散落的肋骨与头骨'
ZH['fallen petrified branches'] = '倒下的石化树枝'
ZH['blowing dry tumbleweed'] = '吹动的干枯风滚草'
ZH['drifting sand off the crests'] = '沙丘顶端吹落的沙粒'
ZH['shimmering heat haze'] = '闪烁的热浪'
ZH['dust and heat haze'] = '尘埃与热浪'
ZH['broken wooden scaffolds and rail tracks'] = '破损的木脚手架与铁轨'
ZH['drifting gulls'] = '翱翔的海鸥'
ZH['faint red vents'] = '微弱的红色火山口'
ZH['drifting brash ice'] = '漂移的碎冰'
ZH['faint moonlight on sand'] = '沙漠上微弱的月光'
ZH['warm rim light on stone'] = '石头上温暖的光晕'
ZH['glowing stone and grass materials'] = '发光的石头与草地材质'
ZH['half-submerged statues and arches'] = '半淹没的雕像与拱门'
ZH['dark water and stone materials'] = '深色水体与石材'
ZH['sunbeams through windows'] = '透过窗户的阳光束'
ZH['soft volumetric light shafts'] = '柔和的体积光柱'
ZH['bioluminescent pools'] = '生物荧光水潭'
ZH['drifting blue icebergs in a still polar bay'] = '宁静极地海湾中漂移的蓝色冰山'
ZH['towering blue ice cliffs'] = '高耸的蓝色冰崖'
ZH['dark soil and rock'] = '深色泥土与岩石'
ZH['steep forested slopes'] = '陡峭森林坡地'
ZH['silent cavern over a frozen underground lake'] = '冰冻地下湖上的寂静洞穴'
ZH['dead trees and still water'] = '枯树与静止的水'
ZH['dark pine forests'] = '深色松林'
ZH['steep volcanic rim walls'] = '陡峭火山口壁'
ZH['dark muddy ground'] = '深色泥泞地面'
ZH['deep red volcanic dusk'] = '深红火山黄昏'
ZH['dark glassy stone materials'] = '深色玻璃石材质'
ZH['faint red vents'] = '微弱红色喷气口'
ZH['glowing cracks and ember sparks'] = '发光裂缝与余烬火星'

# --- Materials (80+) ---
ZH['realistic rock and foliage materials'] = '写实岩石与植被材质'
ZH['weathered mossy stone materials'] = '风化苔藓石质材质'
ZH['eroded weathered stone materials'] = '侵蚀风化石质材质'
ZH['glacial stone and ice materials'] = '冰川石与冰晶材质'
ZH['kelp and wet stone materials'] = '海藻与湿润石质材质'
ZH['mossy weathered stone materials'] = '苔藓风化石材'
ZH['dark weathered stone materials'] = '深色风化石材'
ZH['weathered stone materials'] = '风化石材'
ZH['wet rock and foliage materials'] = '湿润岩石与植被材质'
ZH['ice-crusted carved pillars'] = '冰封雕刻石柱'
ZH['aged timber and stone materials'] = '陈年木材与石材'
ZH['weathered stone and mud materials'] = '风化石材与泥土'
ZH['weathered rock and timber materials'] = '风化岩石与木材'
ZH['weathered stone and fabric materials'] = '风化石材与织物'
ZH['weathered stone and rusted iron materials'] = '风化石材与锈铁'
ZH['weathered granite and dirt materials'] = '风化花岗岩与泥土'
ZH['weathered stone and water materials'] = '风化石材与水体'
ZH['rock and snow materials'] = '岩石与雪材质'
ZH['ice snow and rock materials'] = '冰雪与岩石材质'
ZH['frost rock and ice materials'] = '霜冻岩石与冰材质'
ZH['ice rock and snow materials'] = '冰岩与雪材质'
ZH['ice stone and snow materials'] = '冰石与雪材质'
ZH['ice water and snow materials'] = '冰水与雪材质'
ZH['pure ice and frost materials'] = '纯冰与霜材质'
ZH['snow ice and rock materials'] = '雪冰与岩石材质'
ZH['glacial ice and snow materials'] = '冰川冰与雪材质'
ZH['snow bark and ice materials'] = '雪树皮与冰材质'
ZH['ice frost and bark materials'] = '冰霜与树皮材质'
ZH['timber snow and ice materials'] = '木材雪与冰材质'
ZH['rock timber and ember materials'] = '岩石木材与余烬材质'
ZH['dark ash and rock materials'] = '深色灰烬与岩石材质'
ZH['ash charcoal and ember materials'] = '灰烬木炭与余烬材质'
ZH['burnt earth and charred wood materials'] = '焦土与烧焦木材材质'
ZH['basalt and molten materials'] = '玄武岩与熔岩材质'
ZH['basalt and molten rock materials'] = '玄武岩与熔岩材质'
ZH['obsidian and molten materials'] = '黑曜石与熔岩材质'
ZH['cracked clay and stone materials'] = '开裂黏土与石材质'
ZH['dead bark and mud materials'] = '枯树皮与泥材质'
ZH['dead bark stone and ember materials'] = '枯树皮石与余烬材质'
ZH['bone clay and dust materials'] = '骨骼黏土与尘埃材质'
ZH['smooth sandstone materials'] = '光滑砂岩材质'
ZH['sandstone and dry vine materials'] = '砂岩与干藤材质'
ZH['eroded sandstone materials'] = '侵蚀砂岩材质'
ZH['smooth bark and mist materials'] = '光滑树皮与雾气材质'
ZH['rock vine and water materials'] = '岩石藤蔓与水体材质'
ZH['rock foliage and water materials'] = '岩石植被与水体材质'
ZH['rock grass and water materials'] = '岩石草地与水体材质'
ZH['wet rock vine and water materials'] = '湿润岩石藤蔓与水体材质'
ZH['fungus rock and moss materials'] = '真菌岩石与苔藓材质'
ZH['fungus bark and moss materials'] = '真菌树皮与苔藓材质'
ZH['bark and stone and moss materials'] = '树皮石与苔藓材质'
ZH['bark moss and fungi materials'] = '树皮苔藓与真菌材质'
ZH['bark moss and soil materials'] = '树皮苔藓与土壤材质'
ZH['limestone and moss materials'] = '石灰岩与苔藓材质'
ZH['damp rock and crystal materials'] = '潮湿岩石与水晶材质'
ZH['crystal rock and glow materials'] = '水晶岩石与发光材质'
ZH['crystal stone and water materials'] = '水晶石材与水体材质'
ZH['water salt and sky materials'] = '水体盐与天空材质'
ZH['water sand and glow materials'] = '水体沙与发光材质'
ZH['water reed and mud materials'] = '水体芦苇与泥材质'
ZH['sulfur mineral and water materials'] = '硫磺矿物与水体材质'
ZH['volcanic rock and water materials'] = '火山岩与水体材质'
ZH['wet limestone and water materials'] = '湿润石灰岩与水体材质'
ZH['wet basalt and water materials'] = '湿润玄武岩与水体材质'
ZH['dark basalt and water materials'] = '深色玄武岩与水体材质'
ZH['dark wet basalt and water materials'] = '深色湿润玄武岩与水体材质'
ZH['dark wet rock materials'] = '深色湿岩材质'
ZH['dark stone and water materials'] = '深色石材与水体材质'
ZH['dark stone and moss materials'] = '深色石材与苔藓材质'
ZH['stone water and timber materials'] = '石材水体与木材'
ZH['stone ivy and moss materials'] = '石材常春藤与苔藓材质'
ZH['mossy stone and ivy materials'] = '苔藓石材与常春藤材质'
ZH['wet stone and water materials'] = '湿石与水体材质'
ZH['slick stone moss and water materials'] = '光滑石头苔藓与水体材质'
ZH['smooth water sand and stone materials'] = '光滑水体沙与石材'
ZH['clay palm and water materials'] = '黏土棕榈与水体材质'
ZH['plaster stone and water materials'] = '灰泥石材与水体材质'
ZH['timber bark and rope materials'] = '木材树皮与绳索材质'
ZH['rope timber and rock materials'] = '绳索木材与岩石材质'
ZH['timber metal and fabric materials'] = '木材金属与织物材质'
ZH['stone timber and crop materials'] = '石材木材与作物材质'
ZH['stone timber and snow materials'] = '石材木材与雪材质'
ZH['cobble timber and glass materials'] = '鹅卵石木材与玻璃材质'
ZH['wood snow and stone materials'] = '木材雪与石材'
ZH['wood stone and blossom materials'] = '木材石材与花材质'
ZH['soil grass and water materials'] = '土壤草地与水体材质'
ZH['grass flower and rock materials'] = '草花与岩石材质'
ZH['stone metal and cloud materials'] = '石材金属与云材质'
ZH['marble gold and cloud materials'] = '大理石金与云材质'
ZH['stone snow and light materials'] = '石材雪与光材质'
ZH['rock and glowing energy materials'] = '岩石与发光能量材质'
ZH['rusted metal and dry earth materials'] = '锈蚀金属与干土材质'
ZH['rusted wood and water materials'] = '锈蚀木材与水体材质'
ZH['asphalt rock and pine materials'] = '沥青岩石与松木材质'
ZH['dry salt and stone materials'] = '干盐与石材质'
ZH['fine sand materials'] = '细沙材质'

# --- Composition (60+) ---
ZH['sweeping ridgeline composition'] = '辽阔山脊线构图'
ZH['leading-line composition'] = '引导线构图'
ZH['sweeping open composition'] = '辽阔开放构图'
ZH['sweeping minimal composition'] = '辽阔极简构图'
ZH['sweeping diagonal composition'] = '辽阔对角线构图'
ZH['sweeping serpentine composition'] = '辽阔蜿蜒构图'
ZH['sweeping sky-dominant composition'] = '辽阔天空主导构图'
ZH['layered atmospheric depth'] = '层次化大气深度'
ZH['layered canopy composition'] = '层次化树冠构图'
ZH['layered natural composition'] = '层次化自然构图'
ZH['layered depth composition'] = '层次化深度构图'
ZH['layered horizontal composition'] = '层次化水平构图'
ZH['layered vertical composition'] = '层次化垂直构图'
ZH['layered ridge composition'] = '层次化山脊构图'
ZH['layered aerial composition'] = '层次化航拍构图'
ZH['dramatic atmospheric depth'] = '戏剧性大气深度'
ZH['dramatic central composition'] = '戏剧性中心构图'
ZH['dramatic backlit composition'] = '戏剧性逆光构图'
ZH['dramatic curved composition'] = '戏剧性曲线构图'
ZH['dramatic layered composition'] = '戏剧性层次构图'
ZH['dramatic upward composition'] = '戏剧性向上构图'
ZH['dramatic vertical composition'] = '戏剧性垂直构图'
ZH['dramatic high-contrast composition'] = '戏剧性高对比构图'
ZH['dramatic depth and scale'] = '戏剧性深度与比例'
ZH['dramatic windswept composition'] = '戏剧性迎风构图'
ZH['dramatic radiating composition'] = '戏剧性放射构图'
ZH['dramatic framed composition'] = '戏剧性框架构图'
ZH['dramatic receding composition'] = '戏剧性后退构图'
ZH['grand symmetrical composition'] = '宏伟对称构图'
ZH['grand vertical composition'] = '宏伟垂直构图'
ZH['monumental layered composition'] = '纪念碑式层次构图'
ZH['monumental balanced composition'] = '纪念碑式平衡构图'
ZH['monumental central composition'] = '纪念碑式中心构图'
ZH['monumental diagonal composition'] = '纪念碑式对角线构图'
ZH['vast clean composition'] = '广阔干净构图'
ZH['vast horizontal composition'] = '广阔水平构图'
ZH['vast minimal composition'] = '广阔极简构图'
ZH['tranquil horizontal composition'] = '宁静水平构图'
ZH['vertical dramatic composition'] = '垂直戏剧性构图'
ZH['vertical cathedral composition'] = '垂直大教堂式构图'
ZH['awe-inspiring central composition'] = '令人敬畏的中心构图'
ZH['awe-inspiring vertical composition'] = '令人敬畏的垂直构图'
ZH['rhythmic geometric composition'] = '节奏几何构图'
ZH['rhythmic perspective composition'] = '节奏透视构图'
ZH['rhythmic vertical composition'] = '节奏垂直构图'
ZH['peaceful layered composition'] = '宁静层次构图'
ZH['peaceful leading-line composition'] = '宁静引导线构图'
ZH['intricate layered composition'] = '精致层次构图'
ZH['intimate enclosed composition'] = '亲密封闭式构图'
ZH['intimate magical composition'] = '亲密魔法构图'
ZH['intimate winding composition'] = '亲密蜿蜒构图'
ZH['isolated minimal composition'] = '孤立极简构图'
ZH['isolated vertical composition'] = '孤立垂直构图'
ZH['balanced minimal composition'] = '平衡极简构图'
ZH['minimal powerful composition'] = '极简有力构图'
ZH['minimal quiet composition'] = '极简安静构图'
ZH['dynamic chaotic composition'] = '动态混乱构图'
ZH['dynamic diagonal composition'] = '动态对角线构图'
ZH['powerful diagonal composition'] = '强力对角线构图'
ZH['deep perspective composition'] = '深邃透视构图'
ZH['ominous central composition'] = '不祥中心构图'
ZH['melancholic central composition'] = '忧郁中心构图'
ZH['lyrical winding composition'] = '抒情蜿蜒构图'
ZH['serene receding composition'] = '宁静后退构图'
ZH['stark minimal composition'] = '鲜明极简构图'
ZH['stark otherworldly composition'] = '鲜明异世界构图'
ZH['sparse haunting composition'] = '稀疏萦绕构图'
ZH['tense diagonal composition'] = '紧张对角线构图'
ZH['inviting central composition'] = '引人入胜的中心构图'
ZH['mysterious layered composition'] = '神秘层次构图'
ZH['mystical radial composition'] = '神秘放射构图'
ZH['surreal layered composition'] = '超现实层次构图'
ZH['surreal radiant composition'] = '超现实放射构图'
ZH['somber wide composition'] = '阴沉广角构图'
ZH['still minimal composition'] = '静止极简构图'
ZH['lonely horizontal composition'] = '孤独水平构图'
ZH['desolate layered composition'] = '荒凉层次构图'
ZH['cozy layered composition'] = '舒适层次构图'
ZH['towering vertical composition'] = '高耸垂直构图'
ZH['vertiginous downward composition'] = '眩晕下坠构图'
ZH['vertiginous vertical composition'] = '眩晕垂直构图'
ZH['symmetrical infinite composition'] = '对称无限构图'
ZH['symmetrical reflective composition'] = '对称反射构图'
ZH['vibrant layered composition'] = '活力层次构图'
ZH['calm layered composition'] = '平静层次构图'
ZH['circular framing composition'] = '圆形框架构图'
ZH['enclosed framed composition'] = '封闭框架构图'
ZH['heroic upward composition'] = '英雄式向上构图'

# --- Atmosphere/Style (40+) ---
ZH['grounded fantasy realism'] = '写实奇幻风格'
ZH['moody volumetric lighting'] = '情绪化体积光效'
ZH['lush volumetric haze'] = '浓郁体积雾效'
ZH['crisp atmospheric depth'] = '清晰大气深度'
ZH['cool atmospheric depth'] = '清冷大气深度'
ZH['dusty atmospheric depth'] = '沙尘大气深度'
ZH['tender atmospheric depth'] = '柔和大气深度'
ZH['eerie atmospheric depth'] = '诡异大气深度'
ZH['moody atmospheric depth'] = '情绪化大气深度'
ZH['warm atmospheric depth'] = '温暖大气深度'
ZH['rich atmospheric depth'] = '丰富大气深度'
ZH['deep atmospheric depth'] = '深邃大气深度'
ZH['soft atmospheric depth'] = '柔和大气深度'
ZH['sharp atmospheric depth'] = '锐利大气深度'
ZH['fine atmospheric depth'] = '精细大气深度'
ZH['hyper atmospheric depth'] = '极致大气深度'
ZH['luminous atmospheric depth'] = '明亮大气深度'
ZH['blinding atmospheric depth'] = '炫目大气深度'
ZH['glowing atmospheric depth'] = '发光大气深度'
ZH['sublime atmospheric depth'] = '崇高大气深度'
ZH['immense atmospheric depth'] = '无垠大气深度'
ZH['vast atmospheric depth'] = '广阔大气深度'
ZH['intense atmospheric depth'] = '强烈大气深度'
ZH['airy atmospheric depth'] = '轻盈大气深度'
ZH['clean atmospheric depth'] = '干净大气深度'
ZH['fresh atmospheric depth'] = '清新大气深度'
ZH['delicate atmospheric depth'] = '细腻大气深度'
ZH['dreamy atmospheric depth'] = '梦幻大气深度'
ZH['ethereal atmospheric depth'] = '空灵大气深度'
ZH['magical atmospheric depth'] = '魔法大气深度'
ZH['lush atmospheric depth'] = '浓郁大气深度'
ZH['heavy atmospheric depth'] = '沉重大气深度'
ZH['humid atmospheric depth'] = '潮湿大气深度'
ZH['hazy atmospheric depth'] = '朦胧大气深度'
ZH['misty atmospheric depth'] = '薄雾大气深度'
ZH['muted atmospheric depth'] = '柔和大气深度'
ZH['smoky atmospheric depth'] = '烟雾大气深度'
ZH['harsh atmospheric depth'] = '强烈大气深度'
ZH['turbulent atmospheric depth'] = '湍流大气深度'
ZH['oppressive atmospheric depth'] = '压抑大气深度'
ZH['frigid atmospheric depth'] = '严寒大气深度'
ZH['brooding atmospheric depth'] = '阴郁大气深度'
ZH['somber atmospheric depth'] = '阴沉大气深度'
ZH['melancholic atmospheric depth'] = '忧郁大气深度'
ZH['nostalgic atmospheric depth'] = '怀旧大气深度'
ZH['cozy atmospheric depth'] = '温馨大气深度'
ZH['serene atmospheric depth'] = '宁静大气深度'
ZH['gentle atmospheric depth'] = '柔和大气深度'
ZH['warm hazy depth'] = '温暖朦胧深度'
ZH['warm atmospheric haze'] = '温暖大气雾霭'
ZH['atmospheric mist depth'] = '大气雾霭深度'
ZH['atmospheric rain depth'] = '大气雨雾深度'
ZH['deep atmospheric haze'] = '深邃大气雾霭'
ZH['deep night atmospheric depth'] = '深夜大气深度'
ZH['deep cosmic atmospheric depth'] = '深邃宇宙大气深度'
ZH['fresh humid atmospheric depth'] = '清新潮湿大气深度'
ZH['dramatic storm light with lightning'] = '戏剧性暴风闪电光线'
ZH['low moody lighting'] = '低矮情绪化光线'
ZH['ominous volumetric lighting'] = '不祥体积光效'
ZH['dreamy volumetric depth'] = '梦幻体积深度'
ZH['gentle volumetric haze'] = '柔和体积雾效'
ZH['glowing volumetric haze'] = '发光体积雾效'
ZH['dramatic light above storm clouds'] = '暴风云上戏剧性光线'
ZH['dramatic storm-edge light'] = '暴风边缘戏剧性光线'
ZH['surreal layered composition'] = '超现实层次构图'

# --- Scale/Quality (5) ---
ZH['believable scale, 16:9'] = '可信比例，16:9宽高比'
ZH['believable monumental scale, 16:9'] = '可信宏伟比例，16:9宽高比'
ZH['monumental believable scale, 16:9'] = '纪念碑式可信比例，16:9宽高比'
ZH['16:9'] = '16:9宽高比'
ZH['lush layered composition'] = '浓郁层次构图'
ZH['gentle ambient glow'] = '柔和环境微光'
ZH['blowing powder snow'] = '吹起的粉状雪'
ZH['crisp cold blue daylight'] = '清冷蓝色日光'
ZH['sheer cliff walls'] = '陡峭的岩壁'
ZH['soft golden dusk'] = '柔和金色黄昏'
ZH['soft mist'] = '柔和薄雾'
ZH['vast empty horizon'] = '广阔空旷的地平线'
ZH['wet boulders and ferns'] = '湿润的巨石与蕨类'

# ============================================================
# TYPE CLASSIFICATION
# ============================================================
LK = set('daylight morning sun dawn dusk moonlight golden twilight night overcast stormy harsh pale noon fog mist haze lighting light glow shadow crisp cold warm soft diffused blue clear starry moody grey bright dark cloudy rain lightning firelight ember candlelight sunbeam spring summer autumn winter afternoon directional sunbeam post-rain blizzard aurora arctic bioluminescent filtered ambient dusk sunset sunrise'.split())
CK = set('photography wide-angle low-angle drone aerial close-up dolly tracking push-in camera cinematic bokeh wide telephoto'.split())
MK = set('materials texture stone metal glass crystal ice rock sand moss weathered eroded polished rough smooth fabric wood leather fur scales snow frost water mud clay marble granite bark timber basalt obsidian'.split())
SK = set('realism realistic atmospheric volumetric depth scale composition lighting render quality detail film grounded fantasy believable dramatic lush eerie crisp moody warm rich sharp soft fine hyper cinematic leading-line tender sweeping majestic epic'.split())

def classify_text(text):
    words = set(re.findall(r'[a-z]+', text.lower()))
    lh,ch,mh,sh = len(words&LK), len(words&CK), len(words&MK), len(words&SK)
    if ch > max(lh,mh,sh,0): return 3
    if lh > max(ch,mh,sh,0): return 2
    if mh > max(ch,lh,sh,0): return 5
    if sh > max(ch,lh,mh,0): return 6
    return 4  # scene subject

STOP = set('a an the in on at of to for with and or but is are was were be been being have has had do does did will would can could shall should may might must it its this that these those by from as into through no not up out over under across along toward towards past against off down below above near far faint few such than then also just only very so all some any'.split())

# Difficult word dictionary (same as before)
DW = {}
for line in open(__file__):
    m = re.match(r"\s*'(\w+(?:-\w+)?)':", line)
    if m: DW.setdefault(m.group(1), '')

# Keywords that indicate the word is genuinely difficult/specialized
DIFFICULT = {
    'generate':'生成','epic':'史诗的','unreal':'虚幻','engine':'引擎','cinematic':'电影级的',
    'photography':'摄影','environmental':'环境的','wide-angle':'广角','low-angle':'低角',
    'drone':'无人机','aerial':'航拍','parallax':'视差','bokeh':'背景虚化','composition':'构图',
    'volumetric':'体积的','ambient':'环境的','occlusion':'遮挡','render':'渲染','rendering':'渲染',
    'overcast':'阴天','stormy':'暴风雨','harsh':'强烈的','pale':'苍白','golden':'金色',
    'moonlit':'月光照亮的','twilight':'黄昏','haze':'薄雾','mist':'雾气','misty':'多雾',
    'fog':'浓雾','humid':'潮湿的','shimmer':'微光闪烁','reflective':'反射','diffused':'漫射',
    'directional':'定向','ethereal':'空灵','starry':'星空','dappled':'斑驳的',
    'colossal':'巨大的','towering':'高耸','monumental':'纪念碑式','canopy':'树冠',
    'foliage':'植被','vines':'藤蔓','dune':'沙丘','cliff':'悬崖','cliffs':'悬崖',
    'gorge':'峡谷','canyon':'峡谷','cascade':'瀑布','waterfall':'瀑布','waterfalls':'瀑布',
    'glacier':'冰川','fjord':'峡湾','tundra':'冻原','ravine':'沟壑','boulder':'巨石',
    'cavern':'洞穴','grotto':'岩穴','temple':'神庙','ruins':'废墟','pyramid':'金字塔',
    'citadel':'城堡','fortress':'要塞','sanctuary':'圣殿','archipelago':'群岛',
    'landscape':'景观','reef':'礁石','lagoon':'潟湖','oasis':'绿洲','volcano':'火山',
    'crater':'火山口','geyser':'间歇泉','altar':'祭坛','shrine':'神社','monolith':'巨石碑',
    'obelisk':'方尖碑','bastion':'堡垒','rampart':'城墙','aqueduct':'引水渠',
    'weathered':'风化','eroded':'侵蚀','mossy':'苔藓覆盖','barnacle':'藤壶','cracked':'开裂',
    'crystalline':'水晶','translucent':'半透明','iridescent':'彩虹色','luminous':'发光',
    'pristine':'原始','rugged':'崎岖','jagged':'锯齿',
    'realism':'写实主义','realistic':'写实','grounded':'写实','atmospheric':'大气',
    'believable':'可信','moody':'情绪化','dramatic':'戏剧性','eerie':'诡异','lush':'浓郁',
    'crisp':'清晰','tender':'柔和','majestic':'雄伟','sweeping':'辽阔','layered':'层次',
    'ancient':'古老','massive':'巨大','vast':'广阔','dense':'茂密','frozen':'冰冻',
    'floating':'悬浮','sunken':'沉没','buried':'埋葬','enchanted':'魔法','sacred':'神圣',
    'forgotten':'遗忘','ruined':'毁灭','crumbled':'崩塌','shattered':'破碎','twisted':'扭曲',
    'gnarled':'多节','barren':'荒芜','verdant':'翠绿','arid':'干旱','frigid':'严寒',
    'desolate':'荒凉','celestial':'天体','mystical':'神秘','arcane':'奥术',
    'runes':'符文','glyphs':'符文','carvings':'雕刻','statues':'雕像','pillars':'柱子',
    'arches':'拱门','domes':'穹顶','spires':'尖塔','towers':'塔楼','balconies':'阳台',
    'pine':'松树','oak':'橡树','willow':'柳树','birch':'桦树','cedar':'雪松',
    'cypress':'柏树','bamboo':'竹子','lotus':'莲花','ivy':'常春藤','moss':'苔藓',
    'fern':'蕨类','kelp':'海藻','coral':'珊瑚','lichen':'地衣',
    'drifting':'飘浮','crashing':'冲击','swirling':'旋转','billowing':'翻涌',
    'flickering':'闪烁','rippling':'涟漪','undulating':'起伏','bioluminescence':'生物荧光',
    'obsidian':'黑曜岩','basalt':'玄武岩','limestone':'石灰岩','sandstone':'砂岩',
    'granite':'花岗岩','karst':'喀斯特','fjord':'峡湾','terracotta':'陶土',
    'chasm':'深渊','crevasse':'裂缝','fissure':'裂隙','caldera':'火山口',
    'parallax':'视差','depth of field':'景深','bokeh':'散景',
}

# ============================================================
# MAIN PROCESSING
# ============================================================
new_prompts = []
for p in parsed:
    en_full = p['text_en_full']
    zh_parts = []  # collect segment translations for composing zh_full

    for s in p['statements']:
        seg = s['text_en'].strip()
        seg_lower = seg.lower()
        idx = s['sort_order']

        # Type classification: use specific rules for first/last segments
        if idx == 1:
            s['type_id'] = 1
        elif idx == 2:
            s['type_id'] = 2
        elif idx == 3:
            s['type_id'] = 3
        else:
            s['type_id'] = classify_text(seg)

        # Chinese translation
        s['text_zh'] = ZH.get(seg, '')
        if s['text_zh']:
            zh_parts.append(s['text_zh'])

        # Difficult words
        tokens = re.findall(r'\b[a-zA-Z][a-zA-Z-]+\b', seg)
        seen = set()
        words = []
        for tok in tokens:
            tl = tok.lower().strip('-')
            if tl in STOP or len(tl) <= 2 or tl not in DIFFICULT: continue
            pos = -1
            for m in re.finditer(re.escape(tok), en_full, re.IGNORECASE):
                if m.start() not in seen: pos = m.start(); break
            if pos < 0: continue
            seen.add(pos)
            words.append({'word_en':tok,'word_zh':DIFFICULT[tl],'position_start':pos,'position_end':pos+len(tok)})
        words.sort(key=lambda w:w['position_start'])
        s['words'] = words

    # Generate zh_full: natural Chinese paragraph
    if p.get('text_zh_full'):
        zh_full = p['text_zh_full']  # Keep existing if source provided it
    else:
        zh_full = '，'.join(zh_parts) if zh_parts else p['title']

    new_prompts.append({
        'title':p['title'],'text_en_full':en_full,'text_zh_full':zh_full,
        'category':p['category'],'source_file':'100条史诗奇幻场景提示词.xlsx',
        'statements':p['statements'],
    })

with open(OUTPUT,'w',encoding='utf-8') as f:
    json.dump({'new_prompts':new_prompts},f,ensure_ascii=False,indent=2)

ts = sum(len(pp['statements']) for pp in new_prompts)
tw = sum(len(s['words']) for pp in new_prompts for s in pp['statements'])
ez = sum(1 for pp in new_prompts for s in pp['statements'] if not s.get('text_zh'))
print(f'Done: {len(new_prompts)} prompts, {ts} stmts, {tw} words, {ez} missing ZH')

# Show samples
for pp in new_prompts[:2]:
    print(f'\n--- {pp["title"]} ---')
    print(f'  zh_full: {pp["text_zh_full"][:120]}...')
    for s in pp['statements'][:4]:
        tn = {1:'固',2:'光',3:'镜',4:'主',5:'材',6:'风',7:'色',8:'环'}.get(s['type_id'],'?')
        zh = s.get('text_zh','') or '(待翻译)'
        print(f'  [{tn}] {s["text_en"][:50]} → {zh[:30]}')
