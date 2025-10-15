#!/bin/env python
"""
Simple Space Invaders clone using Pygame.
Save as space_invaders.py and run with: python3 space_invaders.py
Requires: pygame (pip install pygame)
Controls: Left/Right arrows or A/D to move, Space to fire, P to pause, Esc to quit
This is a single-file implementation that uses simple shapes (no external assets).
"""

import math
import random
import sys

import pygame

# ---------- Initialization (pygame) ----------
pygame.init()

# ---------- Config ----------
info = pygame.display.Info()  # get screen info
WIDTH, HEIGHT = info.current_w, info.current_h  # get screen width and height
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 8
ENEMY_SPEED_BASE = 0.5
ENEMY_DROP = 20
ENEMY_FIRE_CHANCE = 0.0015  # per frame per enemy
ENEMY_ROWS = 4
ENEMY_COLS = 8
ENEMY_X_PADDING = 60
ENEMY_Y_PADDING = 40
ENEMY_X_GAP = 60
ENEMY_Y_GAP = 45
MAX_PLAYER_BULLETS = 3
PLAYER_LIVES = 3

# ---------- Initialization ----------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders - Pygame")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 64)


# ---------- Helpers ----------
def draw_text(surf, text, size, x, y, center=False):
    f = pygame.font.SysFont(None, size)
    r = f.render(text, True, (255, 255, 255))
    if center:
        rect = r.get_rect(center=(x, y))
        surf.blit(r, rect)
    else:
        surf.blit(r, (x, y))


# ---------- Game Objects ----------
class Player:
    def __init__(self):
        self.width = 50
        self.height = 18
        self.x = WIDTH // 2
        self.y = HEIGHT - 60
        self.speed = PLAYER_SPEED
        self.lives = PLAYER_LIVES
        self.respawn_timer = 0
        self.invulnerable = 0

    def move(self, dx):
        self.x += dx * self.speed
        self.x = max(self.width // 2, min(WIDTH - self.width // 2, self.x))

    def draw(self, surf):
        # simple ship: a triangle
        p1 = (self.x, self.y - self.height)
        p2 = (self.x - self.width // 2, self.y + self.height // 2)
        p3 = (self.x + self.width // 2, self.y + self.height // 2)
        color = (0, 200, 255) if self.invulnerable % 10 < 5 else (0, 120, 220)
        pygame.draw.polygon(surf, color, [p1, p2, p3])

    def rect(self):
        return pygame.Rect(
            self.x - self.width // 2, self.y - self.height, self.width, self.height * 2
        )


class Bullet:
    def __init__(self, x, y, dy, friendly=True):
        self.x = x
        self.y = y
        self.dy = dy
        self.radius = 4
        self.friendly = friendly

    def update(self):
        self.y += self.dy

    def draw(self, surf):
        color = (255, 255, 0) if self.friendly else (255, 100, 100)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), self.radius)

    def rect(self):
        return pygame.Rect(
            self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2
        )


class Enemy:
    def __init__(self, x, y, row, col):
        self.x = x
        self.y = y
        self.row = row
        self.col = col
        self.alive = True
        self.width = 36
        self.height = 24

    def draw(self, surf, offset_x=0, offset_y=0):
        if not self.alive:
            return
        rx = int(self.x + offset_x)
        ry = int(self.y + offset_y)
        # simple invader shape
        body = pygame.Rect(
            rx - self.width // 2, ry - self.height // 2, self.width, self.height
        )
        pygame.draw.rect(surf, (150, 255, 150), body)
        # eyes
        pygame.draw.circle(surf, (0, 0, 0), (rx - 8, ry - 4), 3)
        pygame.draw.circle(surf, (0, 0, 0), (rx + 8, ry - 4), 3)

    def rect(self, offset_x=0, offset_y=0):
        return pygame.Rect(
            int(self.x + offset_x - self.width // 2),
            int(self.y + offset_y - self.height // 2),
            self.width,
            self.height,
        )


# ---------- Level / Enemy Grid ----------
class EnemyGroup:
    def __init__(self, rows=ENEMY_ROWS, cols=ENEMY_COLS):
        self.rows = rows
        self.cols = cols
        self.enemies = []
        self.offset_x = 0
        self.offset_y = 0
        self.direction = 1
        self.speed = ENEMY_SPEED_BASE
        self.create_grid()

    def create_grid(self):
        start_x = (WIDTH - ((self.cols - 1) * ENEMY_X_GAP)) // 2
        start_y = 80
        self.enemies = []
        for r in range(self.rows):
            for c in range(self.cols):
                x = start_x + c * ENEMY_X_GAP
                y = start_y + r * ENEMY_Y_GAP
                self.enemies.append(Enemy(x, y, r, c))

    def alive_enemies(self):
        return [e for e in self.enemies if e.alive]

    def update(self):
        alive = self.alive_enemies()
        if not alive:
            return
        # speed up slightly as there are fewer enemies
        self.speed = ENEMY_SPEED_BASE + (
            0.02 * (1 - len(alive) / (self.rows * self.cols))
        )
        dx = self.direction * self.speed
        self.offset_x += dx
        # check bounds
        left = min((e.x + self.offset_x) for e in alive)
        right = max((e.x + self.offset_x) for e in alive)
        if left < 20 or right > WIDTH - 20:
            self.direction *= -1
            self.offset_y += ENEMY_DROP

    def draw(self, surf):
        for e in self.enemies:
            e.draw(surf, self.offset_x, self.offset_y)

    def rects(self):
        return [e.rect(self.offset_x, self.offset_y) for e in self.enemies if e.alive]

    def any_reached_bottom(self):
        for e in self.alive_enemies():
            if e.y + self.offset_y + e.height // 2 >= HEIGHT - 100:
                return True
        return False


# ---------- Game State ----------
class Game:
    def __init__(self):
        self.player = Player()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = EnemyGroup()
        self.score = 0
        self.running = True
        self.paused = False
        self.game_over = False
        self.level = 1

    def reset_level(self):
        self.enemies = EnemyGroup(
            rows=ENEMY_ROWS + (self.level - 1) // 2, cols=ENEMY_COLS
        )
        self.bullets = []
        self.enemy_bullets = []
        self.player.x = WIDTH // 2
        self.player.invulnerable = 60

    def fire_player(self):
        if len([b for b in self.bullets if b.friendly]) >= MAX_PLAYER_BULLETS:
            return
        b = Bullet(self.player.x, self.player.y - 28, -BULLET_SPEED, friendly=True)
        self.bullets.append(b)

    def update(self):
        if self.paused or self.game_over:
            return
        # update player invulnerability
        if self.player.invulnerable > 0:
            self.player.invulnerable -= 1
        # update bullets
        for b in list(self.bullets):
            b.update()
            if b.y < -10 or b.y > HEIGHT + 10:
                self.bullets.remove(b)
        for b in list(self.enemy_bullets):
            b.update()
            if b.y < -10 or b.y > HEIGHT + 10:
                self.enemy_bullets.remove(b)
        # enemies
        self.enemies.update()
        # enemy firing
        for e in self.enemies.alive_enemies():
            if random.random() < ENEMY_FIRE_CHANCE:
                self.enemy_bullets.append(
                    Bullet(
                        e.x + self.enemies.offset_x,
                        e.y + self.enemies.offset_y + 10,
                        BULLET_SPEED,
                        friendly=False,
                    )
                )
        # collisions: player bullets vs enemies
        for b in [bb for bb in self.bullets if bb.friendly]:
            for e in self.enemies.alive_enemies():
                if b.rect().colliderect(
                    e.rect(self.enemies.offset_x, self.enemies.offset_y)
                ):
                    e.alive = False
                    try:
                        self.bullets.remove(b)
                    except ValueError:
                        pass
                    self.score += 10
                    break
        # collisions: enemy bullets vs player
        if self.player.invulnerable <= 0:
            for b in list(self.enemy_bullets):
                if b.rect().colliderect(self.player.rect()):
                    try:
                        self.enemy_bullets.remove(b)
                    except ValueError:
                        pass
                    self.player.lives -= 1
                    self.player.invulnerable = 120
                    if self.player.lives <= 0:
                        self.game_over = True
                    break
        # enemy reaches bottom
        if self.enemies.any_reached_bottom():
            self.game_over = True
        # level complete
        if not self.enemies.alive_enemies():
            self.level += 1
            self.player.lives += 1
            self.reset_level()

    def draw(self, surf):
        surf.fill((12, 12, 30))
        # HUD
        draw_text(surf, f"Score: {self.score}", 24, 10, 8)
        draw_text(surf, f"Lives: {self.player.lives}", 24, WIDTH - 120, 8)
        draw_text(surf, f"Level: {self.level}", 24, WIDTH // 2 - 30, 8)
        # entities
        self.enemies.draw(surf)
        for b in list(self.bullets):
            b.draw(surf)
        for b in list(self.enemy_bullets):
            b.draw(surf)
        if not self.game_over:
            self.player.draw(surf)
        # messages
        if self.paused:
            draw_text(surf, "PAUSED", 48, WIDTH // 2, HEIGHT // 2, center=True)
        if self.game_over:
            draw_text(surf, "GAME OVER", 64, WIDTH // 2, HEIGHT // 2 - 30, center=True)
            draw_text(
                surf,
                f"Final Score: {self.score}",
                36,
                WIDTH // 2,
                HEIGHT // 2 + 30,
                center=True,
            )
            draw_text(
                surf,
                "Press R to restart or Esc to quit",
                24,
                WIDTH // 2,
                HEIGHT // 2 + 80,
                center=True,
            )


# ---------- Main Loop ----------


def main():
    game = Game()
    game.reset_level()

    move_dir = 0
    running = True

    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    move_dir = -1
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    move_dir = 1
                elif event.key == pygame.K_SPACE:
                    if not game.game_over:
                        game.fire_player()
                elif event.key == pygame.K_p:
                    game.paused = not game.paused
                elif event.key == pygame.K_r:
                    if game.game_over:
                        game = Game()
                        game.reset_level()
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    move_dir = 0

        # continuous key checking for smoother movement
        keys = pygame.key.get_pressed()
        d = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            d -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            d += 1
        game.player.move(d)

        # update
        game.update()

        # draw
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
