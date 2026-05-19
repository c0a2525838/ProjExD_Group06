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
# 安全な画像読み込み関数
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

# -----------------------------
# Enemy（画像読み込み＋自動縮小）
# -----------------------------
class Enemy(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # 画像読み込み
        self.image = load_image_safe("fig/enemy.png")

        # 自動縮小（40%）
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

powerup_group = pg.sprite.Group()
powerup_timer = 0
powerup_active = False
powerup_end_time = 0
threeway_group = pg.sprite.Group()
threeway_timer = 0

threeway_active = False 
threeway_end_time = 0

# 連射間隔（通常：15フレーム）
shot_interval = 15
shot_timer = 0


# -----------------------------
# Main Game Loop
# -----------------------------
player = Player()
player_group = pg.sprite.Group(player)
bullet_group = pg.sprite.Group()
enemy_group = pg.sprite.Group()
score = Score()  # ★ スコア追加

enemy_spawn_timer = 0
scroll_x = 0
game_over = False
font = pg.font.Font(None, 80)

while True:
    for ev in pg.event.get():
        if ev.type == pg.QUIT:
            pg.quit()
            sys.exit()
        if not game_over and ev.type == pg.KEYDOWN:
            if ev.key == pg.K_SPACE:
                if shot_timer <= 0:
                    bullet_speed = 10

                    if threeway_active:
                        # ★★★ 3WAYショット ★★★
                        bullet_group.add(Bullet(player.rect.right, player.rect.centery, bullet_speed))
                        bullet_group.add(Bullet(player.rect.right, player.rect.centery - 15, bullet_speed))
                        bullet_group.add(Bullet(player.rect.right, player.rect.centery + 15, bullet_speed))
                    else:
                        # 通常ショット
                        bullet_group.add(Bullet(player.rect.right, player.rect.centery, bullet_speed))
                    
                    shot_timer = shot_interval
    if not game_over:
        scroll_x += 3

        enemy_spawn_timer += 1
        if enemy_spawn_timer > 40:
            enemy_group.add(Enemy())
            enemy_spawn_timer = 0

        player_group.update()
        bullet_group.update()
        enemy_group.update()

        # 連射タイマー
        if shot_timer > 0:
            shot_timer -= 1

        # パワーアップ出現
        powerup_timer += 1
        if powerup_timer > 300:  # 5秒に1回くらい
            powerup_group.add(PowerUp())
            powerup_timer = 0

        powerup_group.update()

        # 3WAYアイテム出現
        threeway_timer += 1
        if threeway_timer > 500:  # 出現頻度は調整可
            threeway_group.add(PowerUp3Way())
            threeway_timer = 0

        threeway_group.update()


        # プレイヤーがパワーアップ取得
        if pg.sprite.spritecollide(player, powerup_group, True):
            powerup_active = True
            shot_interval = 1  # ★ 連射速度アップ！
            powerup_end_time = pg.time.get_ticks() + 8000  # 8秒間

        # 3WAYアイテム取得
        if pg.sprite.spritecollide(player, threeway_group, True):   
            threeway_active = True
            threeway_end_time = pg.time.get_ticks() + 8000  # 8秒間


        # 効果時間が切れたら戻す
        if powerup_active and pg.time.get_ticks() > powerup_end_time:
            powerup_active = False
            shot_interval = 15

        # 3WAY効果終了
        if threeway_active and pg.time.get_ticks() > threeway_end_time:
            threeway_active = False



        # 敵と衝突 → ゲームオーバー
        if pg.sprite.spritecollide(player, enemy_group, True):
            game_over = True

        # 弾が敵に当たったらスコア加算
        hits = pg.sprite.groupcollide(bullet_group, enemy_group, True, True)
        if hits:
            score.add(100)

    draw_background(scroll_x)
    player_group.draw(screen)
    bullet_group.draw(screen)
    enemy_group.draw(screen)
    powerup_group.draw(screen)
    threeway_group.draw(screen)
    score.draw(screen)  # ★ スコア表示

    if game_over:
        txt = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(txt, (WIDTH // 2 - 180, HEIGHT // 2 - 40))

    pg.display.update()
    main_clock.tick(60)





