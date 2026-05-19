import pygame as pg
import random
import sys
import os

# -----------------------------
# 実行ディレクトリを自動修正
# -----------------------------
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("Fixed directory:", os.getcwd())

# -----------------------------
# 初期設定
# -----------------------------
pg.init()
WIDTH, HEIGHT = 800, 600
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Gradius-like Shooter")
main_clock = pg.time.Clock()

# -----------------------------
# 安全な読み込み関数（画像・音声・BGM）
# -----------------------------
def load_image_safe(path):
    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        surf = pg.Surface((30, 20))
        surf.fill((255, 80, 80))
        return surf

    try:
        img = pg.image.load(path)
        print(f"[OK] Loaded image: {path}")
        return img
    except Exception as e:
        print(f"[ERROR] Cannot load image: {path}")
        print("Reason:", e)
        surf = pg.Surface((30, 20))
        surf.fill((255, 80, 80))
        return surf

def load_sound_safe(path):
    if not os.path.exists(path):
        print(f"[ERROR] Sound file not found: {path}")
        return None
        
    try:
        sound = pg.mixer.Sound(path)
        print(f"[OK] Loaded sound: {path}")
        return sound
    except Exception as e:
        print(f"[ERROR] Cannot load sound: {path}")
        print("Reason:", e)
        return None

# ★ 追加: BGM再生用の安全な関数
def play_bgm_safe(path):
    if not os.path.exists(path):
        print(f"[ERROR] BGM file not found: {path}")
        return
    try:
        pg.mixer.music.load(path)
        pg.mixer.music.set_volume(0.5)  # 音量調整 (0.0 〜 1.0)
        pg.mixer.music.play(-1)         # -1で無限ループ再生
        print(f"[OK] Playing BGM: {path}")
    except Exception as e:
        print(f"[ERROR] Cannot play BGM: {path}")
        print("Reason:", e)

# -----------------------------
# Score（スコア表示）
# -----------------------------
class Score:
    def __init__(self):
        self.value = 0
        self.font = pg.font.Font(None, 36)

    def add(self, amount):
        self.value += amount

    def draw(self, surface):
        txt = self.font.render(f"Score: {self.value}", True, (255, 255, 255))
        surface.blit(txt, (10, 10))

# -----------------------------
# Player（画像3種：通常・上・下）
# -----------------------------
class Player(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # 画像読み込み
        self.img_normal = load_image_safe("fig/gura2.png")
        self.img_up     = load_image_safe("fig/gura3.png")
        self.img_down   = load_image_safe("fig/gura4.png")

        # 自動縮小（40%）
        def scale(img):
            w, h = img.get_size()
            return pg.transform.smoothscale(img, (int(w*0.4), int(h*0.4)))

        self.img_normal = scale(self.img_normal)
        self.img_up     = scale(self.img_up)
        self.img_down   = scale(self.img_down)

        # 初期画像
        self.image = self.img_normal
        self.rect = self.image.get_rect()
        self.rect.center = (100, HEIGHT // 2)

        self.speed = 5
        self.dy = 0  

    def update(self):
        keys = pg.key.get_pressed()
        self.dy = 0

        if keys[pg.K_UP]:
            self.rect.y -= self.speed
            self.dy = -1
        if keys[pg.K_DOWN]:
            self.rect.y += self.speed
            self.dy = 1
        if keys[pg.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pg.K_RIGHT]:
            self.rect.x += self.speed

        # 状態に応じて画像切り替え
        if self.dy < 0:
            self.image = self.img_up
        elif self.dy > 0:
            self.image = self.img_down
        else:
            self.image = self.img_normal

        self.rect.clamp_ip(screen.get_rect())

# -----------------------------
# Bullet
# -----------------------------
class Bullet(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pg.Surface((10, 4))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 10

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > WIDTH:
            self.kill()

# -----------------------------
# Enemy（画像読み込み＋自動縮小）
# -----------------------------
class Enemy(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # 画像読み込み
        self.image = load_image_safe("fig/enemy.png")

        # 自動縮小（10%）
        w, h = self.image.get_size()
        self.image = pg.transform.smoothscale(self.image, (int(w*0.1), int(h*0.1)))

        try:
            self.image = self.image.convert_alpha()
        except:
            pass

        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(20, HEIGHT - 20)
        self.speed = random.randint(3, 6)

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

# -----------------------------
# Background scroll
# -----------------------------
bg = pg.Surface((WIDTH, HEIGHT))
bg.fill((10, 10, 30))
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(80)]

def draw_background(scroll_x):
    screen.blit(bg, (0, 0))
    for x, y in stars:
        pg.draw.circle(screen, (200, 200, 255), ((x - scroll_x) % WIDTH, y), 2)

# -----------------------------
# アセットの読み込み（天国画像＆ゲームオーバーSE）
# -----------------------------
heaven_raw = load_image_safe("fig/heaven.png")
heaven_img = pg.transform.smoothscale(heaven_raw, (WIDTH, HEIGHT))

gameover_se = load_sound_safe("BGM/heaven.wav")
bgm_file = "BGM/背景BGM.mp3"  # ★ 追加: BGMのファイルパス

fade_surface = pg.Surface((WIDTH, HEIGHT))
fade_surface.fill((255, 255, 255))
fade_timer = 0
heaven_timer = 0

# -----------------------------
# Main Game Loop
# -----------------------------
player = Player()
player_group = pg.sprite.Group(player)
bullet_group = pg.sprite.Group()
enemy_group = pg.sprite.Group()
score = Score()

enemy_spawn_timer = 0
scroll_x = 0

game_state = "playing" 
font = pg.font.Font(None, 80)
font_small = pg.font.Font(None, 40)

# ★ 追加: ゲーム開始時にBGMを再生
play_bgm_safe(bgm_file)

while True:
    for ev in pg.event.get():
        if ev.type == pg.QUIT:
            pg.quit()
            sys.exit()
            
        if ev.type == pg.KEYDOWN:
            # プレイ中のスペースキー（射撃）
            if game_state == "playing":
                if ev.key == pg.K_SPACE:
                    bullet_group.add(Bullet(player.rect.right, player.rect.centery))
            
            # ゲームオーバー中のエンターキー（コンティニュー）
            elif game_state == "gameover":
                if ev.key == pg.K_RETURN:  # Enterキー
                    if gameover_se:
                        gameover_se.stop()

                    # ゲーム状態をリセット
                    game_state = "playing"
                    score.value = 0
                    scroll_x = 0
                    enemy_spawn_timer = 0
                    player.rect.center = (100, HEIGHT // 2)
                    
                    # 画面上の敵と弾をすべて消去
                    enemy_group.empty()
                    bullet_group.empty()

                    # ★ 追加: コンティニュー時にBGMを再スタート
                    play_bgm_safe(bgm_file)

    # --- 更新処理 ---
    if game_state == "playing":
        scroll_x += 3
        enemy_spawn_timer += 1
        if enemy_spawn_timer > 40:
            enemy_group.add(Enemy())
            enemy_spawn_timer = 0

        player_group.update()
        bullet_group.update()
        enemy_group.update()

        # 敵と衝突 → フェード処理へ移行
        if pg.sprite.spritecollide(player, enemy_group, True):
            game_state = "fading"
            fade_timer = 0
            
            # ★ 追加: 敵にぶつかったらBGMを止める
            pg.mixer.music.stop()

        # 弾が敵に当たったらスコア加算
        hits = pg.sprite.groupcollide(bullet_group, enemy_group, True, True)
        if hits:
            score.add(100)

    # --- 描画処理 ---
    if game_state == "playing" or game_state == "fading":
        draw_background(scroll_x)
        player_group.draw(screen)
        bullet_group.draw(screen)
        enemy_group.draw(screen)
        score.draw(screen)

    # 画面を段々白くする
    if game_state == "fading":
        fade_timer += 1
        alpha = int(255 * (fade_timer / 120))
        if alpha >= 255:
            alpha = 255
            game_state = "heaven" 
            heaven_timer = 0
            
            # 天国の画面に切り替わった瞬間にSEを再生！
            if gameover_se:
                gameover_se.play()
            
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))

    # 天国の画像を表示する（2秒間）
    elif game_state == "heaven":
        screen.blit(heaven_img, (0, 0))
        heaven_timer += 1
        
        # 2秒経ったらゲームオーバー画面へ移行
        if heaven_timer >= 120: 
            game_state = "gameover"

    # 天国を表示したまま GAME OVER 文字とコンティニューの案内を出す
    elif game_state == "gameover":
        screen.blit(heaven_img, (0, 0))
        txt = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(txt, (WIDTH // 2 - 180, HEIGHT // 2 - 60))
        
        # コンティニュー案内テキスト
        txt_continue = font_small.render("Press ENTER to Continue", True, (0, 0, 0))
        screen.blit(txt_continue, (WIDTH // 2 - 170, HEIGHT // 2 + 20))

    pg.display.update()
    main_clock.tick(60)