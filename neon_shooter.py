import pygame
import random
import math
import sys

# 初始化Pygame
pygame.init()

# 游戏窗口设置
WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("霓虹战机 - Neon Shooter")

# 帧率控制
clock = pygame.time.Clock()
FPS = 60

# 霓虹色彩定义
BLACK = (0, 0, 0)
NEON_CYAN = (0, 255, 255)
NEON_PINK = (255, 0, 255)
NEON_YELLOW = (255, 255, 0)
NEON_GREEN = (0, 255, 0)
NEON_PURPLE = (128, 0, 255)
NEON_RED = (255, 0, 0)
COLORS = [NEON_CYAN, NEON_PINK, NEON_YELLOW, NEON_GREEN, NEON_PURPLE]

# 特效缓冲层（用于粒子效果的离屏渲染）
effect_buffer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# 粒子类 - 用于爆炸等特效
class Particle:
    def __init__(self, pos, color):
        self.pos = pygame.Vector2(pos)
        # 随机爆炸方向和速度
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 8)
        self.vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
        self.life = 1.0  # 生命周期
        self.decay = random.uniform(0.02, 0.05)  # 衰减速度
        self.radius = random.uniform(2, 5)
        self.color = color

    def update(self):
        self.pos += self.vel
        self.vel *= 0.95  # 空气阻力
        self.life -= self.decay
        self.radius *= 0.98

    def draw(self, surface, shake_offset):
        if self.life > 0:
            alpha = int(255 * self.life)
            color = (*self.color, alpha)
            draw_pos = self.pos + shake_offset
            pygame.draw.circle(surface, color, (int(draw_pos.x), int(draw_pos.y)), int(self.radius))

# 玩家类
class Player:
    def __init__(self):
        self.pos = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
        self.radius = 15
        self.speed = 300  # 移动速度（像素/秒）
        self.shoot_cooldown = 0.15  # 射击冷却时间
        self.last_shot = 0
        self.health = 100
        self.max_health = 100
        self.color = NEON_CYAN

    def update(self, dt, keys):
        # WASD移动控制
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move.x += 1
        
        # 归一化移动向量，防止斜向移动过快
        if move.length() > 0:
            move.normalize_ip()
        self.pos += move * self.speed * dt
        
        # 限制玩家在屏幕内
        self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))

    def shoot(self, mouse_pos, bullets, current_time):
        if current_time - self.last_shot >= self.shoot_cooldown:
            self.last_shot = current_time
            # 计算子弹方向
            direction = pygame.Vector2(mouse_pos) - self.pos
            direction.normalize_ip()
            speed = 500
            bullet = Bullet(self.pos.copy(), direction * speed, NEON_YELLOW)
            bullets.append(bullet)
            return True
        return False

    def draw(self, surface, shake_offset):
        draw_pos = self.pos + shake_offset
        # 玩家主体
        pygame.draw.circle(surface, self.color, (int(draw_pos.x), int(draw_pos.y)), self.radius, 2)
        pygame.draw.circle(surface, self.color, (int(draw_pos.x), int(draw_pos.y)), 5)
        # 瞄准线
        mouse_pos = pygame.mouse.get_pos()
        end_pos = pygame.Vector2(mouse_pos) + shake_offset
        pygame.draw.line(surface, self.color, (int(draw_pos.x), int(draw_pos.y)), (int(end_pos.x), int(end_pos.y)), 1)

# 子弹类
class Bullet:
    def __init__(self, pos, vel, color):
        self.pos = pos
        self.vel = vel
        self.radius = 5
        self.color = color

    def update(self, dt):
        self.pos += self.vel * dt

    def draw(self, surface, shake_offset):
        draw_pos = self.pos + shake_offset
        pygame.draw.circle(surface, self.color, (int(draw_pos.x), int(draw_pos.y)), self.radius)

# 敌人类
class Enemy:
    def __init__(self, player_pos):
        # 从屏幕边缘随机生成
        side = random.randint(0, 3)
        if side == 0:  # 上
            x = random.randint(0, WIDTH)
            y = -20
        elif side == 1:  # 右
            x = WIDTH + 20
            y = random.randint(0, HEIGHT)
        elif side == 2:  # 下
            x = random.randint(0, WIDTH)
            y = HEIGHT + 20
        else:  # 左
            x = -20
            y = random.randint(0, HEIGHT)
        
        self.pos = pygame.Vector2(x, y)
        # 朝向玩家移动
        direction = player_pos - self.pos
        direction.normalize_ip()
        self.speed = random.uniform(100, 200)
        self.vel = direction * self.speed
        self.radius = random.uniform(10, 20)
        self.color = random.choice(COLORS)
        self.health = 1

    def update(self, dt, difficulty):
        # 难度越高，敌人速度越快
        self.pos += self.vel * dt * (1 + difficulty * 0.1)

    def draw(self, surface, shake_offset):
        draw_pos = self.pos + shake_offset
        pygame.draw.circle(surface, self.color, (int(draw_pos.x), int(draw_pos.y)), int(self.radius), 2)
        pygame.draw.circle(surface, self.color, (int(draw_pos.x), int(draw_pos.y)), 3)

def main():
    player = Player()
    bullets = []
    enemies = []
    particles = []
    score = 0
    difficulty = 1
    last_enemy_spawn = 0
    enemy_spawn_rate = 1.0  # 初始敌人生成间隔
    game_over = False
    screen_shake = 0
    shake_intensity = 5
    
    # 字体
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 72)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000  # 转换为秒
        current_time = pygame.time.get_ticks() / 1000

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        # 重新开始游戏
                        return main()
                    if event.key == pygame.K_q:
                        running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game_over:
                    if event.button == 1:  # 左键射击
                        mouse_pos = pygame.mouse.get_pos()
                        player.shoot(mouse_pos, bullets, current_time)

        if not game_over:
            # 输入处理
            keys = pygame.key.get_pressed()
            player.update(dt, keys)

            # 按住鼠标持续射击
            if pygame.mouse.get_pressed()[0]:
                mouse_pos = pygame.mouse.get_pos()
                player.shoot(mouse_pos, bullets, current_time)

            # 生成敌人
            if current_time - last_enemy_spawn >= enemy_spawn_rate:
                last_enemy_spawn = current_time
                enemies.append(Enemy(player.pos))
                # 难度递增，敌人越来越多
                enemy_spawn_rate = max(0.1, 1.0 - difficulty * 0.05)
                difficulty += 0.1

            # 更新子弹
            for bullet in bullets[:]:
                bullet.update(dt)
                # 移除出界的子弹
                if bullet.pos.x < 0 or bullet.pos.x > WIDTH or bullet.pos.y < 0 or bullet.pos.y > HEIGHT:
                    bullets.remove(bullet)

            # 更新敌人
            for enemy in enemies[:]:
                enemy.update(dt, difficulty)

            # 更新粒子
            for particle in particles[:]:
                particle.update()
                if particle.life <= 0:
                    particles.remove(particle)

            # 碰撞检测：子弹 vs 敌人
            for bullet in bullets[:]:
                for enemy in enemies[:]:
                    dist = bullet.pos.distance_to(enemy.pos)
                    if dist < bullet.radius + enemy.radius:
                        bullets.remove(bullet)
                        enemies.remove(enemy)
                        score += 10
                        # 生成爆炸粒子
                        for _ in range(20):
                            particles.append(Particle(enemy.pos, enemy.color))
                        # 屏幕震动反馈
                        screen_shake = 0.1
                        break

            # 碰撞检测：敌人 vs 玩家
            for enemy in enemies[:]:
                dist = player.pos.distance_to(enemy.pos)
                if dist < player.radius + enemy.radius:
                    player.health -= 20
                    enemies.remove(enemy)
                    # 受伤爆炸效果
                    for _ in range(15):
                        particles.append(Particle(enemy.pos, NEON_RED))
                    screen_shake = 0.2
                    # 检查游戏结束
                    if player.health <= 0:
                        game_over = True
                        break

            # 更新屏幕震动
            if screen_shake > 0:
                screen_shake -= dt

        # 计算屏幕震动偏移
        shake_offset = pygame.Vector2(0, 0)
        if screen_shake > 0:
            shake_offset.x = random.uniform(-shake_intensity, shake_intensity)
            shake_offset.y = random.uniform(-shake_intensity, shake_intensity)

        # 绘制
        screen.fill(BLACK)
        effect_buffer.fill((0, 0, 0, 0))  # 清空特效层

        if not game_over:
            # 绘制游戏元素
            player.draw(screen, shake_offset)
            for bullet in bullets:
                bullet.draw(screen, shake_offset)
            for enemy in enemies:
                enemy.draw(screen, shake_offset)
            for particle in particles:
                particle.draw(effect_buffer, shake_offset)
            
            # 合并特效层到主屏幕
            screen.blit(effect_buffer, (0, 0))

            # 绘制UI
            score_text = font.render(f"分数: {score}", True, NEON_CYAN)
            screen.blit(score_text, (10, 10))
            
            # 血条
            health_bar_width = 200
            health_bar_height = 20
            health_percent = player.health / player.max_health
            pygame.draw.rect(screen, NEON_RED, (10, HEIGHT - 30, health_bar_width, health_bar_height), 2)
            pygame.draw.rect(screen, NEON_GREEN, (12, HEIGHT - 28, (health_bar_width - 4) * health_percent, health_bar_height - 4))
        else:
            # 游戏结束画面
            game_over_text = big_font.render("游戏结束", True, NEON_RED)
            score_text = font.render(f"最终分数: {score}", True, NEON_CYAN)
            restart_text = font.render("按 R 重新开始, 按 Q 退出", True, NEON_YELLOW)
            
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 100))
            screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
