#!/usr/bin/env python3
"""Step 3 analysis helper for SD-style comma-separated tag prompts.

Handles the mechanical parts of SD tag analysis:
  - Type classification (quality tags, subjects, lighting, etc.)
  - Dictionary-based Chinese translation for common SD tags
  - Specialized word extraction (art terms, artist names, technical vocabulary)

This script does rule-based classification and dictionary lookups for SD tags.
It does NOT replace Claude's intelligence for natural-language prompts.
All dictionary data is domain-specific (SD/art/photography terminology).

Usage:
  python ai_analyze_sd.py < /tmp/prompt_parsed.json > /tmp/prompt_analysis.json
"""

import json
import sys
import re

# ── Type classification rules ───────────────────────────────────────

def classify_sd_tag(text):
    """Classify an SD tag into a statement type_id."""
    t = text.lower().strip()

    # 1 = 固定开头: LoRA tags, artist style references
    if t.startswith('<lora:') or t.startswith('by ') or t.startswith('artist:'):
        return 1
    if re.match(r'^\(?by\s', t):
        return 1
    # Style/technique keywords at the start
    if t in ('concept art', 'illustration art', 'game concept design',
             'fairy tale', 'surrealism', 'fantasy art', 'digital art',
             'digital painting', 'oil painting', 'watercolor', 'sketch'):
        return 1

    # 2 = 光照氛围: lighting
    lighting_terms = [
        'lighting', 'illumination', 'sunlight', 'daylight', 'overcast',
        'golden hour', 'blue hour', 'rim light', 'volumetric', 'glowing',
        'dynamic light', 'available light', 'moody', 'dramatic',
        'global illumination', 'screen space', 'ray traced', 'glow',
        'bokeh', 'lens flare', 'god rays', 'crepuscular', 'backlight',
        'side-light', 'top-light', 'bottom-light', 'cinematic lighting',
        'studio lighting', 'soft light', 'hard light', 'ambient light',
        'indirect light', 'direct light', 'flash', 'strobe',
    ]
    if any(kw in t for kw in lighting_terms):
        return 2

    # 3 = 镜头构图: camera, angle, framing
    camera_terms = [
        'angle', 'shot', 'view', 'close-up', 'closeup', 'full body',
        'portrait', 'looking at', 'from below', 'from above', 'dynamic pose',
        'action shot', 'depth of field', 'dof', 'f/', 'long exposure',
        'wide angle', 'telephoto', 'macro', 'fisheye', 'panoramic',
        'aerial', 'drone', 'overhead', 'pov', 'first-person',
        'side-view', 'front view', 'back view', 'profile',
        'composition', 'framing', 'rule of thirds', 'symmetrical',
        'foreground', 'midground', 'background depth',
    ]
    if any(kw in t for kw in camera_terms):
        return 3

    # 5 = 材质细节: material, texture
    material_terms = [
        'metal', 'glass', 'fabric', 'leather', 'cotton', 'silk', 'wool',
        'shiny', 'dirty', 'texture', 'skin', 'fur', 'feather', 'scale',
        'armor', 'cloth', 'cloak', 'wearing', 'dressed', 'boots',
        'clothes', 'outfit', 'costume', 'uniform', 'coat', 'jacket',
        'robe', 'dress', 'suit', 'helmet', 'gloves', 'belt', 'jewelry',
        'gold', 'silver', 'bronze', 'chrome', 'rust', 'wood', 'stone',
        'marble', 'crystal', 'ice', 'water', 'fire', 'smoke', 'mist',
        'fog', 'dust', 'sand', 'mud', 'blood', 'sweat', 'tears',
        'reflection', 'refraction', 'transparent', 'translucent', 'opaque',
        'rough', 'smooth', 'polished', 'matte', 'glossy', 'wet', 'dry',
    ]
    if any(kw in t for kw in material_terms):
        return 5

    # 7 = 色彩色调: color
    color_terms = [
        'color', 'tone', 'hue', 'saturation', 'vibrant', 'muted',
        'monochrome', 'grayscale', 'sepia', 'black and white', 'b&w',
        'red', 'blue', 'green', 'yellow', 'orange', 'pink', 'purple',
        'cyan', 'magenta', 'teal', 'violet', 'crimson', 'scarlet',
        'azure', 'emerald', 'golden', 'silver', 'bronze', 'copper',
        'pastel', 'neon', 'fluorescent', 'iridescent', 'prismatic',
        'contrasting', 'complementary', 'analogous', 'warm', 'cool',
        'phthalocyanine', 'ultramarine', 'vermilion', 'ochre',
    ]
    if any(kw in t for kw in color_terms):
        return 7

    # 8 = 环境背景: environment, setting
    env_terms = [
        'background', 'sky', 'garden', 'forest', 'castle', 'room',
        'street', 'garage', 'workshop', 'landscape', 'ocean', 'mountain',
        'water', 'shelves', 'lockers', 'tools', 'machine', 'building',
        'city', 'village', 'dungeon', 'cave', 'desert', 'snow', 'rain',
        'beach', 'river', 'lake', 'field', 'meadow', 'swamp', 'jungle',
        'space', 'planet', 'galaxy', 'nebula', 'underwater', 'ruins',
        'temple', 'church', 'cathedral', 'palace', 'throne', 'bridge',
        'tower', 'wall', 'gate', 'door', 'window', 'roof', 'floor',
        'ceiling', 'hallway', 'corridor', 'staircase', 'balcony',
        'indoor', 'outdoor', 'studio', 'lab', 'warehouse', 'factory',
        'kitchen', 'bedroom', 'bathroom', 'living room', 'office',
    ]
    if any(kw in t for kw in env_terms):
        return 8

    # 6 = 画质风格: quality, resolution, style
    quality_terms = [
        'masterpiece', 'best quality', 'highres', 'hi res', '8k', '4k',
        'ultra detailed', 'extreme detail', 'sharp focus', 'award winning',
        'raw photo', 'photorealistic', 'realistic', 'photo-realistic',
        'octane render', 'unreal engine', 'absurdres', 'high detail',
        'intricate', 'professional photo', 'hd', 'full-hd', 'ultra-hd',
        'super-resolution', 'megapixel', 'rendering', 'cinematic',
        'illustration', 'art', 'style', 'design', 'concept',
        'de-noise', 'shaders', 'post processing', 'post-production',
        'tone mapping', 'vfx', 'txaa', 'rtx',
        'score_', 'source_', 'detailed', 'detail',
        'trailblazing', 'magnum', 'precise',
    ]
    if any(kw in t for kw in quality_terms):
        return 6

    # 4 = 场景主体: default for everything else (subjects, characters, objects)
    subject_terms = [
        'girl', 'boy', 'man', 'woman', 'child', 'baby', 'person', 'people',
        'dog', 'cat', 'animal', 'creature', 'monster', 'dragon', 'horse',
        'bird', 'fish', 'rabbit', 'fox', 'wolf', 'bear', 'lion', 'tiger',
        'portrait', 'face', 'eyes', 'hair', 'body', 'hands', 'arms', 'legs',
        'standing', 'sitting', 'walking', 'running', 'flying', 'posing',
        'holding', 'looking', 'smiling', 'angry', 'screaming', 'crying',
        'humanoid', 'android', 'robot', 'alien', 'zombie', 'skeleton',
        'warrior', 'knight', 'mage', 'wizard', 'witch', 'elf', 'dwarf',
        'princess', 'queen', 'king', 'prince', 'angel', 'demon', 'fairy',
        'anthro', 'furry', 'pony', 'pet', 'insect', 'snake', 'spider',
        'hedgehog', 'toad', 'frog', 'hamster', 'mouse', 'rat', 'squirrel',
        'deer', 'owl', 'eagle', 'hawk', 'raven', 'crow', 'butterfly',
        'flower', 'tree', 'plant', 'fruit', 'food', 'drink',
        'sword', 'gun', 'weapon', 'shield', 'staff', 'wand', 'book',
        'car', 'vehicle', 'ship', 'plane', 'bike', 'motorcycle',
    ]
    if any(kw in t for kw in subject_terms):
        return 4

    # Fallback: if it looks like a subject description
    if len(t) > 15 and not t.startswith('<'):
        return 4

    return None


# ── SD Tag translation dictionary ────────────────────────────────────
# Common Stable Diffusion prompt tags with Chinese translations.
# This is domain-specific terminology, not general translation.

SD_TAG_TRANSLATIONS = {
    # Quality/style
    'masterpiece': '大师级作品',
    'best quality': '最佳画质',
    'highres': '高分辨率',
    'hi res': '高分辨率',
    '8k hd': '8K高清',
    '4k': '4K高清',
    '8k': '8K高清',
    'hd': '高清',
    'full-hd': '全高清',
    'ultra-hd': '超高清',
    'ultra detailed': '极致细节',
    'extreme detail': '极致细节',
    'high detail': '高细节',
    'high details': '高细节',
    'absurdres': '超高分辨率',
    'intricate': '精细复杂',
    'intricate details': '精细细节',
    'detailed background': '细节背景',
    'sharp focus': '锐利对焦',
    'super-resolution': '超分辨率',
    'megapixel': '百万像素',

    # Photography
    'raw photo': 'RAW原片',
    'photorealistic': '写实照片级',
    'realistic': '写实风格',
    'photo-realistic': '照片级写实',
    'professional photo': '专业摄影',
    'award winning': '获奖作品',
    'cinematic': '电影级',
    'cinematic lighting': '电影级布光',

    # Rendering
    'octane render': 'Octane渲染',
    'octane rendering': 'Octane渲染',
    'unreal engine': '虚幻引擎',
    'global illumination': '全局光照',

    # Lighting
    'dynamic lighting': '动态光照',
    'volumetric lighting': '体积光照',
    'available light': '自然光',
    'rim lighting': '轮廓光',
    'rim lights': '轮廓光',
    'moody lighting': '氛围光',
    'beautiful lighting': '精美布光',

    # Camera/angle
    'depth of field': '景深',
    'dof': '景深',
    'long exposure': '长曝光',
    'action shot': '动作镜头',
    'full body': '全身',
    'close-up': '特写',
    'closeup': '特写',
    'looking at viewer': '直视观众',
    'from below': '仰视角度',
    'from above': '俯视角度',
    'dynamic pose': '动态姿势',
    'side-view': '侧面视角',

    # Art styles
    'concept art': '概念艺术',
    'illustration art': '插画艺术',
    'game concept design': '游戏概念设计',
    'fairy tale': '童话风格',
    'surrealism': '超现实主义',
    'fantasy': '奇幻风格',
    'fantasy art': '奇幻艺术',
    'digital art': '数字艺术',
    'digital painting': '数字绘画',
    'anime': '动漫风格',
    'cartoon': '卡通风格',
    'comic': '漫画风格',
    'pixel art': '像素艺术',
    'oil painting': '油画',
    'watercolor': '水彩',
    'sketch': '素描',
    'chibi': 'Q版',

    # Common subjects
    '1girl': '一个女孩',
    '1boy': '一个男孩',
    'solo': '单人',
    'female': '女性',
    'male': '男性',
    'dog': '狗',
    'cat': '猫',
    'animal': '动物',
    'bird': '鸟',
    'fish': '鱼',
    'dragon': '龙',
    'horse': '马',
    'rabbit': '兔子',
    'fox': '狐狸',
    'wolf': '狼',
    'bear': '熊',

    # Actions/poses
    'standing': '站立',
    'sitting': '坐着',
    'walking': '行走',
    'running': '奔跑',
    'flying': '飞行',
    'fighting': '战斗',
    'posing': '摆姿',
    'holding': '手持',
    'looking': '注视',
    'smiling': '微笑',
    'angry': '愤怒',
    'screaming': '尖叫',
    'crying': '哭泣',

    # Body/features
    'face': '脸部',
    'eyes': '眼睛',
    'hair': '头发',
    'hands': '手',
    'arms': '手臂',
    'legs': '腿',
    'body': '身体',
    'portrait': '肖像',
    'blue eyes': '蓝眼睛',
    'red eyes': '红眼睛',
    'green eyes': '绿眼睛',
    'brown eyes': '棕眼睛',
    'short hair': '短发',
    'long hair': '长发',
    'black hair': '黑发',
    'blonde hair': '金发',
    'white hair': '白发',

    # Environment
    'landscape': '风景',
    'background': '背景',
    'sky': '天空',
    'garden': '花园',
    'forest': '森林',
    'castle': '城堡',
    'city': '城市',
    'ocean': '海洋',
    'mountain': '山',
    'river': '河流',
    'lake': '湖泊',
    'desert': '沙漠',
    'snow': '雪景',
    'rain': '雨天',
    'beach': '海滩',
    'sunset': '日落',
    'sunrise': '日出',
    'night': '夜晚',
    'space': '太空',
    'underwater': '水下',
    'ruins': '废墟',

    # Colors
    'red': '红色',
    'blue': '蓝色',
    'green': '绿色',
    'yellow': '黄色',
    'orange': '橙色',
    'pink': '粉色',
    'purple': '紫色',
    'white': '白色',
    'black': '黑色',
    'gray': '灰色',
    'gold': '金色',
    'silver': '银色',
}

# ── Specialized word extraction ──────────────────────────────────────

# Art/photography terms worth highlighting
ART_TERMS = {
    'bokeh', 'depth of field', 'volumetric', 'ambient occlusion',
    'global illumination', 'specular', 'diffuse', 'refraction',
    'caustics', 'subsurface scattering', 'displacement', 'normal map',
    'hdri', 'ibl', 'pbr', 'sss', 'hdr',
    'octane', 'vray', 'arnold', 'redshift', 'cycles', 'eevee',
    'unreal engine', 'unity', 'blender', 'zbrush', 'substance',
    'megascan', 'quixel', 'photoshop', 'lightroom',
    'f/2.8', 'f/1.4', 'f/1.8', 'f/4', 'f/5.6', 'f/8', 'f/16',
    '35mm', '50mm', '85mm', '135mm', '200mm', '24mm', '14mm',
    'iso', 'shutter speed', 'aperture', 'exposure',
    'wide angle', 'telephoto', 'macro lens', 'tilt-shift',
    'rule of thirds', 'golden ratio', 'leading lines',
    'dutch angle', 'low angle', 'high angle', 'bird\'s eye',
    'worm\'s eye', 'over the shoulder', 'establishing shot',
    'anamorphic', 'widescreen', '16:9', '2.35:1',
}

def extract_difficult_words(segment_text, full_text):
    """Extract specialized/highlightable words from an SD tag segment."""
    words = []
    seen = set()

    t = segment_text.strip()

    # Check art/photography terms
    for term in ART_TERMS:
        if term.lower() in t.lower():
            idx = full_text.lower().find(term.lower())
            if idx >= 0 and term.lower() not in seen:
                seen.add(term.lower())
                words.append({
                    'word_en': term,
                    'word_zh': SD_TAG_TRANSLATIONS.get(term, ''),
                    'position_start': idx,
                    'position_end': idx + len(term),
                })

    # Extract artist names (by Xxx Yyy pattern)
    artist_patterns = re.finditer(r'by\s+((?:\(*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\)*)+)', t)
    for m in artist_patterns:
        name = m.group(1).strip('()')
        if len(name) > 5 and name.lower() not in seen:
            seen.add(name.lower())
            idx = full_text.find(name)
            if idx >= 0:
                words.append({
                    'word_en': name,
                    'word_zh': f'艺术家 {name}',
                    'position_start': idx,
                    'position_end': idx + len(name),
                })

    # Extract LoRA references
    for m in re.finditer(r'<lora:([^:>]+)', t):
        lora_name = m.group(1)
        if lora_name.lower() not in seen:
            seen.add(lora_name.lower())
            idx = full_text.find(f'<lora:{lora_name}')
            if idx >= 0:
                words.append({
                    'word_en': f'<lora:{lora_name}>',
                    'word_zh': f'LoRA模型: {lora_name}',
                    'position_start': idx,
                    'position_end': idx + len(f'<lora:{lora_name}>'),
                })

    # Extract uncommon animal names
    uncommon_animals = {
        'spadefoot toad': '锄足蟾',
        'axolotl': '蝾螈',
        'capybara': '水豚',
        'platypus': '鸭嘴兽',
        'pangolin': '穿山甲',
        'narwhal': '独角鲸',
        'okapi': '霍加狓',
        'quokka': '短尾矮袋鼠',
        'tardigrade': '水熊虫',
        'mantis shrimp': '螳螂虾',
    }
    for animal, zh in uncommon_animals.items():
        if animal in t.lower() and animal not in seen:
            seen.add(animal)
            idx = full_text.lower().find(animal)
            if idx >= 0:
                words.append({
                    'word_en': animal,
                    'word_zh': zh,
                    'position_start': idx,
                    'position_end': idx + len(animal),
                })

    return words


# ── Main ─────────────────────────────────────────────────────────────

def translate_tag(text):
    """Translate an SD tag to Chinese using dictionary lookup."""
    t = text.strip()
    if t in SD_TAG_TRANSLATIONS:
        return SD_TAG_TRANSLATIONS[t]

    # Handle LoRA tags: "<lora:name:weight>" → "LoRA风格: name"
    m = re.match(r'^<lora:([^:>]+)(?::([^>]+))?>$', t)
    if m:
        return f'LoRA模型: {m.group(1)}'

    # Handle artist references: "by Artist Name" → "艺术家 Artist Name 风格"
    m = re.match(r'^\(?by\s+(.+?)\)?$', t)
    if m:
        name = m.group(1).strip('()')
        return f'艺术家 {name} 风格'

    # Handle weighted tags: "(tag:weight)" → tag translation with weight note
    m = re.match(r'^\((.+?):(\d+\.?\d*)\)$', t)
    if m:
        inner = translate_tag(m.group(1))
        return f'{inner}（权重{m.group(2)}）'

    # Handle negated/emphasis brackets
    cleaned = re.sub(r'^[\[\(]+|[\]\)]+$', '', t)
    if cleaned != t:
        inner = translate_tag(cleaned)
        if inner != cleaned:
            return inner

    # For tags with underscores, translate parts
    if '_' in t and len(t) < 30:
        parts = t.split('_')
        translated = [SD_TAG_TRANSLATIONS.get(p.lower(), p) for p in parts]
        result = ' '.join(translated)
        if result != t.replace('_', ' '):
            return result

    # Return original for unknown tags
    return t


def analyze_prompts(parsed_prompts):
    """Convert parsed prompts to analyzed prompts with translations/types/words."""
    results = []
    for p in parsed_prompts:
        en_full = p['text_en_full']
        statements = []

        for s in p['statements']:
            text_en = s['text_en']
            text_zh = translate_tag(text_en)
            type_id = classify_sd_tag(text_en)
            words = extract_difficult_words(text_en, en_full)

            statements.append({
                'text_en': text_en,
                'text_zh': text_zh,
                'sort_order': s['sort_order'],
                'type_id': type_id,
                'words': words,
            })

        # Compose Chinese full text from segment translations
        zh_parts = [s['text_zh'] for s in statements if s['text_zh']]
        text_zh_full = '，'.join(zh_parts) if zh_parts else ''

        results.append({
            'title': p['title'],
            'text_en_full': en_full,
            'text_zh_full': text_zh_full,
            'category': p.get('category', ''),
            'source_file': p.get('source_file', ''),
            'statements': statements,
        })

    return results


def main():
    data = json.load(sys.stdin)
    prompts = data if isinstance(data, list) else data.get('prompts', data.get('new_prompts', []))

    if not prompts:
        print("Error: no prompts in input", file=sys.stderr)
        sys.exit(1)

    results = analyze_prompts(prompts)

    total_stmts = sum(len(p['statements']) for p in results)
    total_words = sum(len(s['words']) for p in results for s in p['statements'])
    print(f"Analyzed {len(results)} prompts: {total_stmts} statements, {total_words} words", file=sys.stderr)

    json.dump({'new_prompts': results}, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
