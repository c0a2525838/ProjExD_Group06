# =============================================================
# 凡例：このファイルでボス戦担当（松本光司）が追加した箇所の見方
#   ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼ 〜 ▲▲▲ ここまで ▲▲▲
#       で囲んだブロックが「丸ごと新規追加」した部分
#   行末コメントの「★」が付いている行は元コードに変更/追記した行
#   それ以外（マーカー無し）は元コード（初期状態2 = 9f69d64）のまま
# =============================================================
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
    def __init__(self, stage=1):  # ★ 変更：stage引数を追加
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
        base = 3 + (stage - 1)                       # ★ 変更：ステージ毎に速度UP
        self.speed = random.randint(base, base + 3)  # ★ 変更：元は randint(3, 6)

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

# ═══════════════════════════════════════════════════════════════
# ▼▼▼ 追加機能：ボス戦  ここから ▼▼▼
#   ・EnemyBullet : ボスが撃つ弾
#   ・Boss        : HP制ボス本体（ステージごとに難易度UP）
# ═══════════════════════════════════════════════════════════════
# -----------------------------
# EnemyBullet（ボスがプレイヤー側に撃つ弾）
# -----------------------------
class EnemyBullet(pg.sprite.Sprite):
    def __init__(self, x, y, speed=7):
        super().__init__()
        self.image = pg.Surface((12, 6))
        self.image.fill((255, 80, 80))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

# -----------------------------
# Boss（HP制・上下移動・定期発射、ステージごとに難易度UP）
# -----------------------------
class Boss(pg.sprite.Sprite):
    BASE_HP = 15

    def __init__(self, bullet_group, stage=1):
        super().__init__()
        img = load_image_safe("fig/boss.png")
        w, h = img.get_size()
        target_h = 240
        s = target_h / h if h else 1
        self.image = pg.transform.smoothscale(img, (max(1, int(w * s)), max(1, int(h * s))))
        try:
            self.image = self.image.convert_alpha()
        except Exception:
            pass

        self.rect = self.image.get_rect()
        self.target_x = WIDTH - 40 - self.rect.width
        self.rect.x = WIDTH + 10
        self.rect.centery = HEIGHT // 2

        self.stage = stage
        self.max_hp = Boss.BASE_HP + (stage - 1) * 5
        self.hp = self.max_hp
        self.dy = 2 + (stage - 1)
        self.bullet_speed = 7 + (stage - 1)
        self.shoot_interval = max(15, 50 - (stage - 1) * 5)
        self.shoot_timer = 0
        self.entering = True
        self.bullet_group = bullet_group

    def update(self):
        if self.entering:
            if self.rect.x > self.target_x:
                self.rect.x -= 4
                return
            self.rect.x = self.target_x
            self.entering = False
            return

        self.rect.y += self.dy
        if self.rect.top <= 40:
            self.rect.top = 40
            self.dy = abs(self.dy)
        elif self.rect.bottom >= HEIGHT - 10:
            self.rect.bottom = HEIGHT - 10
            self.dy = -abs(self.dy)

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            self.bullet_group.add(
                EnemyBullet(self.rect.left, self.rect.centery, speed=self.bullet_speed)
            )

    def hit(self):
        self.hp -= 1
        return self.hp <= 0

# ═══════════════════════════════════════════════════════════════
# ▲▲▲ 追加機能：ボス戦  ここまで（EnemyBullet / Boss クラス） ▲▲▲
# ═══════════════════════════════════════════════════════════════

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
# Main Game Loop
# -----------------------------
player = Player()
player_group = pg.sprite.Group(player)
bullet_group = pg.sprite.Group()
enemy_group = pg.sprite.Group()
# ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（スプライトグループ）
enemy_bullet_group = pg.sprite.Group()   # ★ ボスの弾を入れる新グループ
boss_group = pg.sprite.Group()           # ★ ボス本体を入れる新グループ
# ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲
score = Score()  # ★ スコア追加

enemy_spawn_timer = 0
scroll_x = 0
game_over = False
# ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（ゲーム状態フラグ／タイマー）
boss = None                               # ★ 現ボス参照（出てなければNone）
stage = 1                                 # ★ 現在のステージ番号
stage_kills = 0                           # ★ 現ステージで倒したザコ数
clear_timer = 0                           # ★ クリア演出残フレーム（>0で演出中）
CLEAR_FRAMES = 150                        # ★ クリア演出の長さ（2.5秒）
# ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲
font = pg.font.Font(None, 80)
boss_label_font = pg.font.Font(None, 24)  # ★ HPバー上のラベル用
stage_font = pg.font.Font(None, 36)       # ★ STAGE表示用


# ▼▼▼ 追加機能：ボス戦 ここから ▼▼▼（難易度スケーリング関数）
def kill_quota(s):
    """ステージsでボスが出現するために必要なザコ撃破数"""
    return 5 + (s - 1) * 2


def spawn_interval(s):
    """ステージsのザコスポーン間隔（フレーム）"""
    return max(12, 40 - (s - 1) * 4)
# ▲▲▲ 追加機能：ボス戦 ここまで ▲▲▲

while True:
    for ev in pg.event.get():
        if ev.type == pg.QUIT:
            pg.quit()
            sys.exit()
        if not game_over and ev.type == pg.KEYDOWN:
            if ev.key == pg.K_SPACE:
                bullet_group.add(Bullet(player.rect.right, player.rect.centery))

    if not game_over:
        scroll_x += 3

        # ▼ 追加：クリア演出のカウントダウン（終了で次ステージへ）
        if clear_timer > 0:
            clear_timer -= 1
            if clear_timer == 0:
                stage += 1
                stage_kills = 0
                enemy_group.empty()
                enemy_bullet_group.empty()
                enemy_spawn_timer = 0
        # ▲

        # ▼ 追加：ボス出現判定（ザコをノルマ分倒したら登場）
        if boss is None and clear_timer == 0 and stage_kills >= kill_quota(stage):
            enemy_group.empty()
            boss = Boss(enemy_bullet_group, stage=stage)
            boss_group.add(boss)
        # ▲

        # ★ 変更：ザコ生成条件にボス/演出中/ノルマ未達成のガードを追加
        if boss is None and clear_timer == 0 and stage_kills < kill_quota(stage):
            enemy_spawn_timer += 1
            if enemy_spawn_timer > spawn_interval(stage):  # ★ 変更：元は固定40
                enemy_group.add(Enemy(stage=stage))         # ★ 変更：stage引数を渡す
                enemy_spawn_timer = 0

        player_group.update()
        bullet_group.update()
        enemy_group.update()
        enemy_bullet_group.update()  # ★ 追加：敵弾の更新
        boss_group.update()          # ★ 追加：ボスの更新

        # 敵と衝突 → ゲームオーバー
        if pg.sprite.spritecollide(player, enemy_group, True):
            game_over = True

        # ▼ 追加：敵弾／ボス本体との衝突判定
        if pg.sprite.spritecollide(player, enemy_bullet_group, True):
            game_over = True
        if boss is not None and not boss.entering:
            if pg.sprite.spritecollide(player, boss_group, False):
                game_over = True
        # ▲

        # 弾が敵に当たったらスコア加算＆ノルマ進行
        hits = pg.sprite.groupcollide(bullet_group, enemy_group, True, True)
        if hits:
            killed = sum(len(v) for v in hits.values())  # ★ 変更：撃破数を集計
            score.add(100 * killed)                       # ★ 変更：撃破数分加算（元は固定100）
            stage_kills += killed                         # ★ 追加：ノルマカウント

        # ▼ 追加：自弾がボスに当たったらHP減少、撃破でクリア演出開始
        if boss is not None:
            boss_hits = pg.sprite.groupcollide(bullet_group, boss_group, True, False)
            for _bullet, hit_bosses in boss_hits.items():
                for b in hit_bosses:
                    if b.hit():
                        b.kill()
                        score.add(1000 * stage)
                        boss = None
                        enemy_bullet_group.empty()  # 残弾も掃除
                        clear_timer = CLEAR_FRAMES   # クリア演出開始
                    else:
                        score.add(50)
        # ▲

    draw_background(scroll_x)
    player_group.draw(screen)
    bullet_group.draw(screen)
    enemy_group.draw(screen)
    enemy_bullet_group.draw(screen)  # ★ 追加：敵弾の描画
    boss_group.draw(screen)           # ★ 追加：ボスの描画
    score.draw(screen)  # ★ スコア表示

    # ▼ 追加：STAGE表示（右上）＋ ザコフェーズ中は撃破進捗を表示
    stage_txt = stage_font.render(f"STAGE {stage}", True, (255, 255, 255))
    screen.blit(stage_txt, (WIDTH - stage_txt.get_width() - 10, 10))
    if boss is None and clear_timer == 0:
        prog = boss_label_font.render(
            f"KILLS {min(stage_kills, kill_quota(stage))}/{kill_quota(stage)}",
            True, (255, 220, 100)
        )
        screen.blit(prog, (WIDTH - prog.get_width() - 10, 44))
    # ▲

    # ▼ 追加：ボスHPバー（出現演出中は非表示）
    if boss is not None and boss.alive() and not boss.entering:
        bar_w, bar_h = 320, 14
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = 50
        ratio = max(0.0, boss.hp / boss.max_hp)
        pg.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pg.draw.rect(screen, (255, 60, 60), (bar_x, bar_y, int(bar_w * ratio), bar_h))
        pg.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2)
        label = boss_label_font.render(f"BOSS  STAGE {boss.stage}", True, (255, 255, 255))
        screen.blit(label, (bar_x, bar_y - 22))
    # ▲

    if game_over:
        txt = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(txt, (WIDTH // 2 - 180, HEIGHT // 2 - 40))

    # ▼ 追加：ステージクリア演出（"STAGE N CLEAR!" → "NEXT: STAGE N+1"）
    if clear_timer > 0:
        clear_txt = font.render(f"STAGE {stage} CLEAR!", True, (255, 220, 0))
        screen.blit(clear_txt, (WIDTH // 2 - clear_txt.get_width() // 2, HEIGHT // 2 - 60))
        if clear_timer < CLEAR_FRAMES // 2:
            nxt = stage_font.render(f"NEXT: STAGE {stage + 1}", True, (255, 255, 255))
            screen.blit(nxt, (WIDTH // 2 - nxt.get_width() // 2, HEIGHT // 2 + 20))
    # ▲

    pg.display.update()
    main_clock.tick(60)





