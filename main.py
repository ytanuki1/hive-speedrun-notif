import os
import io
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

# --- 設定 ---
GAME_ID = "hive"  # ご指定に合わせて変更
TARGET_CATEGORY = "Gravity"  # 取得対象とするカテゴリ名

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LAST_RUN_FILE = "last_run_id.txt"

LOGO_URL = "https://playhive.com/_next/static/media/Hive.9ce7fa58.png"

# 部門（カテゴリ/レベル名）ごとの背景画像URL
BACKGROUND_URLS = {
    "5 Maps": "https://i.imgur.com/1gY2pA4.png",
    "5 Maps (No Custom Server)": "https://i.imgur.com/xfFhLxa.png",
    "Abstract": "https://cdn.playhive.com/maps/grav_abstract.jpg",
    "Apartments": "https://cdn.playhive.com/maps/grav_apartments.jpg",
    "Beanstalk": "https://cdn.playhive.com/maps/grav_beanstalk.jpg",
    "Beehive": "https://cdn.playhive.com/maps/grav_beehive.jpg",
    "Concrete": "https://cdn.playhive.com/maps/grav_concrete.jpg",
    "Cyberpunk": "https://cdn.playhive.com/maps/grav_cyberpunk.jpg",
    "Data": "https://cdn.playhive.com/maps/grav_beehive.jpg",
    "Depths": "https://cdn.playhive.com/maps/grav_depth.jpg",
    "Glitched": "https://cdn.playhive.com/maps/grav_glitched.jpg",
    "Groovy": "https://cdn.playhive.com/maps/grav_groovy.jpg",
    "Jungle": "https://cdn.playhive.com/maps/grav_jungle.jpg",
    "Lava": "https://cdn.playhive.com/maps/grav_lava.jpg",
    "Pixels": "https://cdn.playhive.com/maps/grav_pixels.jpg",
    "Shapes": "https://cdn.playhive.com/maps/grav_shapes.jpg",
    "Shelves": "https://cdn.playhive.com/maps/grav_shelves.jpg",
    "Shrine": "https://cdn.playhive.com/maps/grav_shrine.jpg",
    "Stairs": "https://cdn.playhive.com/maps/grav_stairs.jpg",
    "Toxic": "https://cdn.playhive.com/maps/grav_toxic.jpg",
    "Waterways": "https://cdn.playhive.com/maps/grav_waterways.jpg",
    "Clockwork": "https://cdn.playhive.com/maps/grav_clockwork.jpg",
    "Construction": "https://cdn.playhive.com/maps/grav_construction.jpg",
    "Daisies": "https://cdn.playhive.com/maps/grav_daisies.jpg",
    "Deepscape": "https://cdn.playhive.com/maps/grav_deepscape.jpg", 
    "Dimensions": "https://cdn.playhive.com/maps/grav_dimensions.jpg",
    "Dungeon": "https://cdn.playhive.com/maps/grav_dungeon.jpg",
    "Labyrinth": "https://cdn.playhive.com/maps/grav_labyrinth.jpg",
    "Lilypads": "https://cdn.playhive.com/maps/grav_lilypads.jpg",
    "New Orleans": "https://cdn.playhive.com/maps/grav_neworleans.jpg",
    "Post Office": "https://cdn.playhive.com/maps/grav_postoffice.jpg",
    "Road Trip": "https://cdn.playhive.com/maps/grav_roadtrip.jpg", 
    "Stained Glass": "https://cdn.playhive.com/maps/grav_stainedglass.jpg",
    "Tomes": "https://cdn.playhive.com/maps/grav_tomes.jpg",
    "Burrow": "https://cdn.playhive.com/maps/grav_burrow.jpg",
    "Circuit Board": "https://cdn.playhive.com/maps/grav_circuitboard.jpg",
    "Geometric": "https://cdn.playhive.com/maps/grav_geometric.jpg",
    "Shanty Town": "https://cdn.playhive.com/maps/grav_shantytown.jpg",
    "Space": "https://cdn.playhive.com/maps/grav_space.jpg",
    "Triangles": "https://cdn.playhive.com/maps/grav_triangles.jpg",
    "Twisted": "https://cdn.playhive.com/maps/grav_twisted.jpg",
    "Under The Sea": "https://cdn.playhive.com/maps/grav_underthesea.jpg",
    "default": "https://i.imgur.com/1gY2pA4.png"
}

# --- ユーティリティ関数（画像生成用） ---
def _load_font(size: int):
    try:
        return ImageFont.truetype("mojangles.ttf", size)
    except IOError:
        return ImageFont.load_default()

def _rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)

def _draw_text_with_shadow(draw, pos, text, font, fill, shadow=(63, 63, 63, 255), anchor="mm", offset=2):
    x, y = pos
    draw.text((x + offset, y + offset), text, font=font, fill=shadow, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

def _fetch_image(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://imgur.com/"
        }
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        print(f"画像取得エラー ({url}): {e}")
        return None

def _fetch_background(division_name, size):
    bg_url = BACKGROUND_URLS["default"]
    sorted_keys = sorted(BACKGROUND_URLS.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        if key == "default":
            continue
        if key.lower() in division_name.lower():
            bg_url = BACKGROUND_URLS[key]
            break
            
    img = _fetch_image(bg_url)
    if not img:
        img = Image.new("RGB", size, (18, 24, 36))
    else:
        img = ImageOps.fit(img, size, method=Image.LANCZOS, centering=(0.5, 0.4))
    
    img = img.filter(ImageFilter.GaussianBlur(2))
    dark_overlay = Image.new("RGBA", size, (0, 0, 0, 90))
    result = Image.alpha_composite(img.convert("RGBA"), dark_overlay).convert("RGB")
    return result

# --- メイン画像生成関数 ---
def generate_notification_image(division_name, player_name, time_str, avatar_url):
    width, height = 1010, 568
    bg = _fetch_background(division_name, (width, height)).convert("RGBA")
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    center_x = width // 2
    cell_bg = (15, 15, 15, 128)
    
    font_title = _load_font(30)
    font_player = _load_font(36)
    font_time = _load_font(72)
    
    # 1. 種目名（上部）
    title_y = 40
    title_w = int(draw.textlength(division_name, font=font_title)) + 60
    title_box = (center_x - title_w//2, title_y, center_x + title_w//2, title_y + 45)
    _rounded_rect(draw, title_box, radius=8, fill=cell_bg)
    _draw_text_with_shadow(draw, (center_x, title_y + 22), division_name, font_title, (255, 255, 255, 255))
    
    # 2. アイコン（中央上）
    icon_y = 110
    icon_size = 90
    icon_box = (center_x - icon_size//2 - 10, icon_y - 10, center_x + icon_size//2 + 10, icon_y + icon_size + 10)
    _rounded_rect(draw, icon_box, radius=8, fill=cell_bg)
    
    avatar_img = _fetch_image(avatar_url) if avatar_url else None
    if avatar_img:
        avatar_img = avatar_img.resize((icon_size, icon_size), Image.LANCZOS)
        overlay.alpha_composite(avatar_img, (center_x - icon_size//2, icon_y))
    
    # 3. ユーザー名（中央下）
    player_y = 230
    player_w = int(draw.textlength(player_name, font=font_player)) + 60
    player_box = (center_x - player_w//2, player_y, center_x + player_w//2, player_y + 50)
    _rounded_rect(draw, player_box, radius=8, fill=cell_bg)
    _draw_text_with_shadow(draw, (center_x, player_y + 25), player_name, font_player, (85, 255, 85, 255))
    
    # 4. タイム（下部）
    time_y = 300
    time_w = int(draw.textlength(time_str, font=font_time)) + 80
    time_box = (center_x - time_w//2, time_y, center_x + time_w//2, time_y + 90)
    _rounded_rect(draw, time_box, radius=12, fill=cell_bg)
    _draw_text_with_shadow(draw, (center_x, time_y + 45), time_str, font_time, (85, 255, 255, 255), offset=4)
    
    # 5. 最下部ロゴ
    logo_target_height = 50
    logo_y = 480
    logo = _fetch_image(LOGO_URL)
    if logo:
        ratio = logo_target_height / logo.height
        new_w = max(1, round(logo.width * ratio))
        logo = logo.resize((new_w, logo_target_height), Image.LANCZOS)
        overlay.alpha_composite(logo, (center_x - new_w//2, logo_y))
    
    return Image.alpha_composite(bg, overlay).convert("RGB")

# --- メイン処理 ---
def main():
    if not DISCORD_WEBHOOK_URL:
        print("Webhook URLが設定されていません。")
        return
        
    last_run_id = ""
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r") as f:
            last_run_id = f.read().strip()
            
    api_url = f"https://www.speedrun.com/api/v1/runs?game={GAME_ID}&status=verified&orderby=verify-date&direction=desc&max=20&embed=category,level,players"
    res = requests.get(api_url).json()
    
    runs = res.get("data", [])
    if not runs:
        print("データが取得できませんでした。")
        return
        
    new_runs = []
    for run in runs:
        if run["id"] == last_run_id:
            break
        
        # カテゴリ名の判定（Gravityに絞り込む）
        cat_rel = run.get("category")
        category_name = ""
        if isinstance(cat_rel, dict):
            cat_data = cat_rel.get("data", {})
            if isinstance(cat_data, dict):
                category_name = cat_data.get("name", "")
            elif isinstance(cat_data, list) and len(cat_data) > 0:
                category_name = cat_data[0].get("name", "")
        elif isinstance(cat_rel, list) and len(cat_rel) > 0:
            if isinstance(cat_rel[0], dict):
                category_name = cat_rel[0].get("name", "")
                
        # 指定したカテゴリ名（Gravity）でなければスキップ
        if TARGET_CATEGORY.lower() not in category_name.lower():
            continue
            
        new_runs.append(run)
        
    if not new_runs:
        print("新着記録はありません。")
        return
        
    new_runs.reverse()
    
    for run in new_runs:
        # レベル名の安全な取得
        level_name = ""
        level_rel = run.get("level")
        if isinstance(level_rel, dict):
            level_data = level_rel.get("data", {})
            if isinstance(level_data, dict):
                level_name = level_data.get("name", "")
            elif isinstance(level_data, list) and len(level_data) > 0:
                level_name = level_data[0].get("name", "")
        elif isinstance(level_rel, list) and len(level_rel) > 0:
            if isinstance(level_rel[0], dict):
                level_name = level_rel[0].get("name", "")

        category_name = ""
        cat_rel = run.get("category")
        if isinstance(cat_rel, dict):
            cat_data = cat_rel.get("data", {})
            if isinstance(cat_data, dict):
                category_name = cat_data.get("name", "")
            elif isinstance(cat_data, list) and len(cat_data) > 0:
                category_name = cat_data[0].get("name", "")
        elif isinstance(cat_rel, list) and len(cat_rel) > 0:
            if isinstance(cat_rel[0], dict):
                category_name = cat_rel[0].get("name", "")
        
        print(f"取得データ確認 -> Level: '{level_name}' / Category: '{category_name}'")

        division_name = f"{level_name} - {category_name}".strip(" -")
        if not division_name:
            division_name = "Gravity"
            
        player_name = "Unknown"
        avatar_url = None
        players = run.get("players", {}).get("data", [])
        if players:
            player = players[0]
            player_name = player.get("names", {}).get("international", player.get("name", "Unknown"))
            avatar_url = player.get("assets", {}).get("image", {}).get("uri")
            
        time_seconds = run["times"]["primary_t"]
        minutes = int(time_seconds // 60)
        seconds = time_seconds % 60
        time_str = f"{minutes}:{seconds:06.3f}" if minutes > 0 else f"{seconds:.3f}"
        
        img = generate_notification_image(division_name, player_name, time_str, avatar_url)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        payload = {"content": f"**{division_name}** で **{player_name}** が記録を更新しました！\nTime: **{time_str}**"}
        files = {"file": ("result.png", img_byte_arr, "image/png")}
        
        requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
        print(f"通知を送信しました: {player_name} - {time_str}")
        
    with open(LAST_RUN_FILE, "w") as f:
        f.write(new_runs[-1]["id"])

if __name__ == "__main__":
    main()
