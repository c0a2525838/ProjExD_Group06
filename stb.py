import pygame as pg
import random
import sys
import os
import math

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
# BGM 再生（完全版）
# -----------------------------
pg.mixer.init()
try:
    pg.mixer.music.load("BGM/senntou.wav")   # BGM
    pg.mixer.music.set_volume(0.6)        # 音量
    pg.mixer.music.play(-1)               # ループ再生
    print("[OK] BGM loaded")
except Exception as e:
    print("[ERROR] BGM load failed:", e)

# -----------------------------
# 安全な読み込み関数（画像・音声）
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

# コード1から追加：安全な音声読み込み関数
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
        self.dy = 0  # 上下移動の状態

        self.shield = False  # シールド状態
        self.shield_stock = 3  # シールドストック（残り数）を追加

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

    def draw_shield(self, surface):
        font = pg.font.Font(None, 30)
        txt = font.render(f"Shield: {self.shield_stock}",True,(0, 255, 255))
        surface.blit(txt, (10, 50))

        if self.shield:
            pg.draw.circle(surface,(0, 255, 255),self.rect.center,40,3) # シールド描画追加

# -----------------------------
# Bullet
# -----------------------------
class Bullet(pg.sprite.Sprite):
    def __init__(self, x, y, speed = 10):
        super().__init__()
        self.image = pg.Surface((10, 4))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > WIDTH:
            self.kill()

# =========================================================
# Laser（貫通レーザー）
# =========================================================
class Laser(pg.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # レーザー画像
        self.image = pg.Surface((120, 12))
        self.image.fill((0, 255, 255))
        self.rect = self.image.get_rect(midleft=(x, y))
        self.speed = 18

    def update(self):
        self.rect.x += self.speed
        if self.rect.left > WIDTH:
            self.kill()     

# -----------------------------
# Enemy（画像読み込み＋自動縮小）
# -----------------------------
class Enemy(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 画像読み込み
        self.image = load_image_safe("fig/enemy.png")

        # 自動縮小（40%）※コード2の設定を優先
        w, h = self.image.get_size()
        self.image = pg.transform.smoothscale(self.image, (int(w*0.1), int(h*0.1)))

        try:
            self.image = self.image.convert_alpha()
        except:
            pass

        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(20, HEIGHT - 20)
        self.speed = random.randint(4, 6)

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

class ChaserEnemy(pg.sprite.Sprite):
    def __init__(self):
        """
        追従型敵（Playerの上下に追従して移動）
        """
        super().__init__()
        self.image = load_image_safe("fig/enemy.png")
        w, h = self.image.get_size()
        self.image = pg.transform.smoothscale(self.image, (int(w*0.1), int(h*0.1)))
        try:
            self.image = self.image.convert_alpha()
        except:
            pass
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(20, HEIGHT - 20)
        self.speed_x = 4
        self.speed_y = 1

    def update(self, player_rect: pg.Rect):
        if player_rect.centery < self.rect.centery: # Playerが上にいる → 敵は上に移動
            self.rect.y -= self.speed_y
        elif player_rect.centery > self.rect.centery:   # Playerが下にいる → 敵は下に移動
            self.rect.y += self.speed_y
        self.rect.x -= self.speed_x
        if self.rect.right < 0:
            self.kill()

class WavyEnemy(pg.sprite.Sprite):
    def __init__(self):
        """
        うねうねする敵
        """
        super().__init__()
        self.image = load_image_safe("fig/enemy.png")
        w, h = self.image.get_size()
        self.image = pg.transform.smoothscale(self.image, (int(w*0.1), int(h*0.1)))
        try:
            self.image = self.image.convert_alpha()
        except:
            pass
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(20, HEIGHT - 20)
        self.base_y = self.rect.y
        self.speed = 4
        self.angle = 0
        self.wave_speed = 0.1
        self.wave_amp = 50

    def update(self):
        self.rect.x -= self.speed
        self.angle += self.wave_speed
        self.rect.y = self.base_y + math.sin(self.angle) * self.wave_amp
        if self.rect.right < 0:
            self.kill()

# -----------------------------
# PowerUp（パワーアップアイテム）
# -----------------------------
class PowerUp(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.Surface((20, 20))
        self.image.fill((0, 255, 255))  # 水色のアイテム
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(50, HEIGHT - 50)
        self.speed = 3

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

class PowerUp3Way(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pg.Surface((20, 20))
        self.image.fill((255, 100, 0))  # オレンジ色のアイテム
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(50, HEIGHT - 50)
        self.speed = 3

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
# アセットの読み込み（天国画像＆ゲームオーバーSE）※コード1から追加
# -----------------------------
heaven_raw = load_image_safe("fig/heaven.png")
heaven_img = pg.transform.smoothscale(heaven_raw, (WIDTH, HEIGHT))
gameover_se = load_sound_safe("BGM/heaven.wav")

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
chaser_enemy_group = pg.sprite.Group()    # 追従型敵グループ
wavy_enemy_group = pg.sprite.Group()    # うねうね敵グループ
laser_group = pg.sprite.Group()  # レーザーグループ追加
powerup_group = pg.sprite.Group()
threeway_group = pg.sprite.Group()

score = Score()

enemy_spawn_timer = 0
scroll_x = 0

# コード1の状態管理を復活
game_state = "playing" 
font = pg.font.Font(None, 80)
font_small = pg.font.Font(None, 40)

powerup_timer = 0
powerup_active = False
powerup_end_time = 0
threeway_timer = 0
threeway_active = False 
threeway_end_time = 0

# 連射間隔
shot_interval = 15
shot_timer = 0
laser_cooldown = 0  

while True:
    for ev in pg.event.get():
        if ev.type == pg.QUIT:
            pg.quit()
            sys.exit()
            
        if ev.type == pg.KEYDOWN:
            # プレイ中のキー操作
            if game_state == "playing":
                if ev.key == pg.K_SPACE:
                    if shot_timer <= 0:
                        bullet_speed = 10
                        if threeway_active:
                            bullet_group.add(Bullet(player.rect.right, player.rect.centery, bullet_speed))
                            bullet_group.add(Bullet(player.rect.right, player.rect.centery - 15, bullet_speed))
                            bullet_group.add(Bullet(player.rect.right, player.rect.centery + 15, bullet_speed))
                        else:
                            bullet_group.add(Bullet(player.rect.right, player.rect.centery, bullet_speed))
                        shot_timer = shot_interval
                        
                elif ev.key == pg.K_x and laser_cooldown <= 0:
                    laser_group.add(Laser(player.rect.right, player.rect.centery))
                    laser_cooldown = 60
                    
                if ev.key == pg.K_s:
                    if player.shield_stock > 0 and not player.shield:
                        player.shield = True
                        player.shield_stock -= 1

            # ゲームオーバー中のエンターキー（コンティニュー）※コード1から追加
            elif game_state == "gameover":
                if ev.key == pg.K_RETURN:  # Enterキー
                    if gameover_se:
                        gameover_se.stop()
                    
                    # BGM再開
                    try:
                        pg.mixer.music.play(-1)
                    except:
                        pass

                    # ゲーム状態をリセット
                    game_state = "playing"
                    score.value = 0
                    scroll_x = 0
                    enemy_spawn_timer = 0
                    player.rect.center = (100, HEIGHT // 2)
                    player.shield = False
                    player.shield_stock = 3
                    
                    # 画面上のエンティティを消去
                    enemy_group.empty()
                    chaser_enemy_group.empty()
                    wavy_enemy_group.empty()
                    bullet_group.empty()
                    laser_group.empty()
                    powerup_group.empty()
                    threeway_group.empty()
                    
                    powerup_active = False
                    threeway_active = False
                    shot_interval = 15

    # --- 更新処理 ---
    if game_state == "playing":
        scroll_x += 3

        if laser_cooldown > 0:
            laser_cooldown -= 1
        if shot_timer > 0:
            shot_timer -= 1

        # 敵の出現
        enemy_spawn_timer += 1
        if enemy_spawn_timer > 40:
            spawn_chance = random.random()
            if spawn_chance < 0.6:
                enemy_group.add(Enemy())
            elif spawn_chance < 0.8:
                chaser_enemy_group.add(ChaserEnemy())
            else:
                wavy_enemy_group.add(WavyEnemy())
            enemy_spawn_timer = 0

        # パワーアップアイテムの出現
        powerup_timer += 1
        if powerup_timer > 300:
            powerup_group.add(PowerUp())
            powerup_timer = 0
            
        threeway_timer += 1
        if threeway_timer > 500:
            threeway_group.add(PowerUp3Way())
            threeway_timer = 0

        # グループの更新
        player_group.update()
        bullet_group.update()
        laser_group.update()
        enemy_group.update()
        chaser_enemy_group.update(player.rect)
        wavy_enemy_group.update()
        powerup_group.update()
        threeway_group.update()

        # パワーアップ取得処理
        if pg.sprite.spritecollide(player, powerup_group, True):
            powerup_active = True
            shot_interval = 1 
            powerup_end_time = pg.time.get_ticks() + 8000
            
        if pg.sprite.spritecollide(player, threeway_group, True):   
            threeway_active = True
            threeway_end_time = pg.time.get_ticks() + 8000

        # パワーアップ終了処理
        if powerup_active and pg.time.get_ticks() > powerup_end_time:
            powerup_active = False
            shot_interval = 15
        if threeway_active and pg.time.get_ticks() > threeway_end_time:
            threeway_active = False

        # --- 当たり判定（プレイヤー VS 敵）---
        # 関数にまとめて処理
        def handle_player_hit():
            global game_state, fade_timer
            if player.shield:
                player.shield = False
            else:
                game_state = "fading"
                fade_timer = 0
                pg.mixer.music.stop() # BGM停止

        if pg.sprite.spritecollide(player, enemy_group, True):
            handle_player_hit()
        if pg.sprite.spritecollide(player, chaser_enemy_group, True):
            handle_player_hit()
        if pg.sprite.spritecollide(player, wavy_enemy_group, True):
            handle_player_hit()

        # --- 当たり判定（攻撃 VS 敵）---
        hits = pg.sprite.groupcollide(bullet_group, enemy_group, True, True)
        if hits: score.add(100)
        hits2 = pg.sprite.groupcollide(bullet_group, chaser_enemy_group, True, True)
        if hits2: score.add(50)
        hits3 = pg.sprite.groupcollide(bullet_group, wavy_enemy_group, True, True)
        if hits3: score.add(150)
        
        laser_hits = pg.sprite.groupcollide(laser_group, enemy_group, False, True)
        if laser_hits: score.add(100)
        laser_hits2 = pg.sprite.groupcollide(laser_group, chaser_enemy_group, False, True)
        if laser_hits2: score.add(50)
        laser_hits3 = pg.sprite.groupcollide(laser_group, wavy_enemy_group, False, True)
        if laser_hits3: score.add(150)

    # --- 描画処理 ---
    if game_state in ["playing", "fading"]:
        draw_background(scroll_x)
        player_group.draw(screen)
        player.draw_shield(screen)
        bullet_group.draw(screen)
        laser_group.draw(screen)
        enemy_group.draw(screen)
        chaser_enemy_group.draw(screen)
        wavy_enemy_group.draw(screen)
        powerup_group.draw(screen)
        threeway_group.draw(screen)
        score.draw(screen)

    # --- ゲームオーバー演出（コード1より復活） ---
    if game_state == "fading":
        fade_timer += 1
        alpha = int(255 * (fade_timer / 120))
        if alpha >= 255:
            alpha = 255
            game_state = "heaven" 
            heaven_timer = 0
            
            # 天国の画面に切り替わった瞬間にSEを再生
            if gameover_se:
                gameover_se.play()
                
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))

    elif game_state == "heaven":
        screen.blit(heaven_img, (0, 0))
        heaven_timer += 1
        if heaven_timer >= 120: 
            game_state = "gameover"

    elif game_state == "gameover":
        screen.blit(heaven_img, (0, 0))
        txt = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(txt, (WIDTH // 2 - 180, HEIGHT // 2 - 60))
        
        txt_continue = font_small.render("Press ENTER to Continue", True, (0, 0, 0))
        screen.blit(txt_continue, (WIDTH // 2 - 170, HEIGHT // 2 + 20))

    pg.display.update()
    main_clock.tick(60)