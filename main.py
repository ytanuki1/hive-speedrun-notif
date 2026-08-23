import os
import io
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

# --- 設定 ---
GAME_ID = "7dge5wp2"  # The Hive のゲームID
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LAST_RUN_FILE = "last_run_id.txt"

LOGO_URL = "https://playhive.com/_next/static/media/Hive.9ce7fa58.png"

# 部門（カテゴリ/レベル名）ごとの背景画像URL
# 取得した種目名（例: "Gravity - 5 Maps"）などの部分一致で背景を出し分ける辞書
# ※ Imgurの直リンク (i.imgur.com/...) も使用可能です
BACKGROUND_URLS = {
    "5 Maps": "https://i.imgur.com/XXXXXXX.png",
    "Abstract": "https://cdn.playhive.com/maps/grav_abstract.jpg",
    "Apartments": "https://cdn.playhive.com/maps/grav_apartments.jpg",
    "Beanstalk": "https://i.imgur.com/ZZZZZZZ.png",
    "Beehive": "https://i.imgur.com/ZZZZZZZ.png",
    "Concrete": "https://i.imgur.com/ZZZZZZZ.png",
    "Cyberpunk": "https://i.imgur.com/ZZZZZZZ.png",
    "Data": "https://i.imgur.com/ZZZZZZZ.png",
    "Depths": "https://i.imgur.com/ZZZZZZZ.png"
    "Glitched": "https://i.imgur.com/ZZZZZZZ.png"
}

# --- ユーティリティ関数（画像生成用） ---
def _load_font(size: int):
    try:
        # Mojanglesフォントがある場合は読み込む（同じディレクトリに配置してください）
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
        # Imgur等のbot弾き対策として、一般的なブラウザのリクエストを偽装
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
    # 部門名から対応する背景を探す
    bg_url = BACKGROUND_URLS["default"]
    for key, url in BACKGROUND_URLS.items():
        if key.lower() in division_name.lower():
            bg_url = url
            break
    
    img = _fetch_image(bg_url)
    if not img:
        img = Image.new("RGB", size, (18, 24, 36))
    else:
        img = ImageOps.fit(img, size, method=Image.LANCZOS, centering=(0.5, 0.4))
    
    # 背景をぼかして暗くする処理
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
    
    # フォント準備
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
        
    # 前回確認したIDを読み込む
    last_run_id = ""
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r") as f:
            last_run_id = f.read().strip()
            
    # Speedrun.com API呼び出し (embed=category,level,playersで付随情報も一括取得)
    api_url = f"https://www.speedrun.com/api/v1/runs?game={GAME_ID}&status=verified&orderby=verify-date&direction=desc&max=10&embed=category,level,players"
    res = requests.get(api_url).json()
    
    runs = res.get("data", [])
    if not runs:
        return
        
    new_runs = []
    for run in runs:
        if run["id"] == last_run_id:
            break
        new_runs.append(run)
        
    if not new_runs:
        print("新着記録はありません。")
        return
        
    # 古いものから順に処理
    new_runs.reverse()
    
    for run in new_runs:
        # 種目名の構築 (例: Level名 - Category名)
        level_data = run.get("level", {}).get("data", {})
        category_data = run.get("category", {}).get("data", {})
        level_name = level_data.get("name", "")
        category_name = category_data.get("name", "")
        
        division_name = f"{level_name} - {category_name}".strip(" -")
        if not division_name:
            division_name = "Gravity"
            
        # プレイヤー名とアイコンの取得
        player_name = "Unknown"
        avatar_url = None
        players = run.get("players", {}).get("data", [])
        if players:
            player = players[0]
            player_name = player.get("names", {}).get("international", player.get("name", "Unknown"))
            avatar_url = player.get("assets", {}).get("image", {}).get("uri")
            
        # タイムのフォーマット
        time_seconds = run["times"]["primary_t"]
        minutes = int(time_seconds // 60)
        seconds = time_seconds % 60
        time_str = f"{minutes}:{seconds:06.3f}" if minutes > 0 else f"{seconds:.3f}"
        
        # 画像生成
        img = generate_notification_image(division_name, player_name, time_str, avatar_url)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Discordへ送信
        payload = {"content": f"**{division_name}** で **{player_name}** が記録を更新しました！\nTime: **{time_str}**"}
        files = {"file": ("result.png", img_byte_arr, "image/png")}
        
        requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
        print(f"通知を送信しました: {player_name} - {time_str}")
        
    # 最後に処理したIDを保存
    with open(LAST_RUN_FILE, "w") as f:
        f.write(new_runs[-1]["id"])

if __name__ == "__main__":
    main()
