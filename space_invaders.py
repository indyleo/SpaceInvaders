import random
import sys

import pygame

# Initialize Pygame
pygame.init()

# Get screen resolution
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
FPS = 60

# Colors
BLACK = (12, 12, 30)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
LIME = (150, 255, 150)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 200, 255)
PINK = (255, 100, 100)

# Create screen
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Space Invaders")
clock = pygame.time.Clock()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width = int(WIDTH * 0.0625)
        self.height = int(self.width * 0.6)
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Draw triangle ship
        p1 = (self.width // 2, 0)
        p2 = (0, self.height)
        p3 = (self.width, self.height)
        pygame.draw.polygon(self.image, CYAN, [p1, p2, p3])
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - int(HEIGHT * 0.1)
        self.speed = int(WIDTH * 0.00625)
        self.shoot_delay = 300
        self.last_shot = pygame.time.get_ticks()
        self.max_bullets = 3
        self.invulnerable = 0
        self.blink_timer = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if self.rect.left > 0:
                self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if self.rect.right < WIDTH:
                self.rect.x += self.speed

        if self.invulnerable > 0:
            self.invulnerable -= 1
            self.blink_timer += 1
            # Blinking effect
            if self.blink_timer % 10 < 5:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def shoot(self, bullets_group):
        current_bullets = sum(1 for b in bullets_group if isinstance(b, Bullet) and b.friendly)
        if current_bullets >= self.max_bullets:
            return False

        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            return True
        return False

class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.size = int(WIDTH * 0.045)
        self.image = pygame.Surface((self.size, int(self.size * 0.75)))
        self.image.fill(BLACK)
        # Draw alien body
        pygame.draw.rect(self.image, LIME, (int(self.size * 0.1), int(self.size * 0.2),
                                             int(self.size * 0.8), int(self.size * 0.5)))
        # Draw eyes
        pygame.draw.circle(self.image, BLACK, (int(self.size * 0.3), int(self.size * 0.35)),
                          int(self.size * 0.08))
        pygame.draw.circle(self.image, BLACK, (int(self.size * 0.7), int(self.size * 0.35)),
                          int(self.size * 0.08))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.base_x = x
        self.base_y = y

class UFO(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = int(WIDTH * 0.06)
        self.image = pygame.Surface((self.size, int(self.size * 0.5)), pygame.SRCALPHA)
        # Draw UFO
        pygame.draw.ellipse(self.image, RED, (0, int(self.size * 0.1),
                                               self.size, int(self.size * 0.3)))
        pygame.draw.ellipse(self.image, YELLOW, (int(self.size * 0.2), 0,
                                                  int(self.size * 0.6), int(self.size * 0.25)))
        pygame.draw.circle(self.image, WHITE, (int(self.size * 0.5), int(self.size * 0.15)),
                          int(self.size * 0.1))
        self.rect = self.image.get_rect()
        self.rect.y = int(HEIGHT * 0.05)
        self.speed = int(WIDTH * 0.004)
        if random.choice([True, False]):
            self.rect.x = -self.size
            self.direction = 1
        else:
            self.rect.x = WIDTH
            self.direction = -1
        self.points = random.choice([50, 100, 150, 300])

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, friendly=True):
        super().__init__()
        self.radius = int(WIDTH * 0.005)
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        color = YELLOW if friendly else PINK
        pygame.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.friendly = friendly
        self.speed = int(HEIGHT * 0.013) if friendly else int(HEIGHT * 0.008)

    def update(self):
        if self.friendly:
            self.rect.y -= self.speed
            if self.rect.bottom < 0:
                self.kill()
        else:
            self.rect.y += self.speed
            if self.rect.top > HEIGHT:
                self.kill()

class Barrier(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = int(WIDTH * 0.1)
        self.height = int(HEIGHT * 0.1)
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.health = 5

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.kill()
        else:
            color_intensity = int(255 * (self.health / 5))
            self.image.fill((0, color_intensity, 0))

class AlienFormation:
    def __init__(self, level=1):
        self.aliens = pygame.sprite.Group()
        self.direction = 1
        self.speed = 1 + (level - 1) * 0.3
        self.drop_amount = int(HEIGHT * 0.03)
        self.level = level
        self.create_formation()

    def create_formation(self):
        rows = min(4 + (self.level - 1) // 2, 6)
        cols = 11
        spacing_x = int(WIDTH * 0.075)
        spacing_y = int(HEIGHT * 0.075)
        start_x = int(WIDTH * 0.1)
        start_y = int(HEIGHT * 0.1)

        for row in range(rows):
            for col in range(cols):
                alien = Alien(col * spacing_x + start_x, row * spacing_y + start_y, row, col)
                self.aliens.add(alien)

    def update(self):
        if not self.aliens:
            return False

        # Adjust speed based on remaining aliens
        current_speed = self.speed * (1 + (1 - len(self.aliens) / 40) * 0.5)

        # Move aliens
        needs_drop = False
        for alien in self.aliens:
            alien.rect.x += self.direction * current_speed
            if alien.rect.left <= 0 or alien.rect.right >= WIDTH:
                needs_drop = True

        if needs_drop:
            self.direction *= -1
            for alien in self.aliens:
                alien.rect.y += self.drop_amount

        # Check if aliens reached bottom
        for alien in self.aliens:
            if alien.rect.bottom >= HEIGHT - int(HEIGHT * 0.15):
                return True  # Game over
        return False

    def get_random_shooter(self):
        if self.aliens:
            return random.choice(self.aliens.sprites())
        return None

# Game state
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.paused = False

        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.barriers = pygame.sprite.Group()
        self.ufos = pygame.sprite.Group()

        self.player = Player()
        self.all_sprites.add(self.player)

        self.formation = AlienFormation(self.level)
        self.all_sprites.add(self.formation.aliens)

        self.create_barriers()

        self.alien_shoot_delay = max(800, 1500 - self.level * 100)
        self.last_alien_shot = pygame.time.get_ticks()

        self.ufo_spawn_delay = random.randint(15000, 30000)
        self.last_ufo_spawn = pygame.time.get_ticks()

    def create_barriers(self):
        barrier_y = HEIGHT - int(HEIGHT * 0.25)
        positions = [int(WIDTH * p) for p in [0.15, 0.38, 0.62, 0.85]]
        for pos in positions:
            barrier = Barrier(pos - int(WIDTH * 0.05), barrier_y)
            self.barriers.add(barrier)
            self.all_sprites.add(barrier)

    def next_level(self):
        self.level += 1
        self.lives += 1

        # Clear old sprites
        for sprite in self.all_sprites:
            if sprite != self.player:
                sprite.kill()
        for sprite in self.bullets:
            sprite.kill()

        # Create new formation
        self.formation = AlienFormation(self.level)
        self.all_sprites.add(self.formation.aliens)

        # Recreate barriers
        self.barriers.empty()
        self.create_barriers()

        self.player.invulnerable = 120
        self.alien_shoot_delay = max(600, 1500 - self.level * 100)

    def update(self):
        if self.paused or self.game_over:
            return

        self.all_sprites.update()

        # Update formation
        if self.formation.update():
            self.game_over = True

        # Alien shooting
        now = pygame.time.get_ticks()
        if now - self.last_alien_shot > self.alien_shoot_delay:
            shooter = self.formation.get_random_shooter()
            if shooter:
                self.last_alien_shot = now
                bullet = Bullet(shooter.rect.centerx, shooter.rect.bottom, friendly=False)
                self.bullets.add(bullet)
                self.all_sprites.add(bullet)

        # UFO spawning
        if now - self.last_ufo_spawn > self.ufo_spawn_delay and len(self.ufos) == 0:
            self.last_ufo_spawn = now
            self.ufo_spawn_delay = random.randint(15000, 30000)
            ufo = UFO()
            self.ufos.add(ufo)
            self.all_sprites.add(ufo)

        # Collisions: Player bullets vs aliens
        for bullet in self.bullets:
            if bullet.friendly:
                hits = pygame.sprite.spritecollide(bullet, self.formation.aliens, True)
                if hits:
                    bullet.kill()
                    self.score += 10 * len(hits)

        # Collisions: Player bullets vs UFO
        for bullet in self.bullets:
            if bullet.friendly:
                hits = pygame.sprite.spritecollide(bullet, self.ufos, True)
                for ufo in hits:
                    bullet.kill()
                    self.score += ufo.points

        # Collisions: Bullets vs barriers
        for bullet in self.bullets:
            hits = pygame.sprite.spritecollide(bullet, self.barriers, False)
            for barrier in hits:
                barrier.hit()
                bullet.kill()

        # Collisions: Enemy bullets vs player
        if self.player.invulnerable <= 0:
            for bullet in self.bullets:
                if not bullet.friendly and bullet.rect.colliderect(self.player.rect):
                    bullet.kill()
                    self.lives -= 1
                    self.player.invulnerable = 120
                    if self.lives <= 0:
                        self.game_over = True

        # Check level complete
        if len(self.formation.aliens) == 0:
            self.next_level()

    def draw(self):
        screen.fill(BLACK)
        self.all_sprites.draw(screen)

        # HUD
        font = pygame.font.SysFont(None, int(HEIGHT * 0.04))
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        lives_text = font.render(f"Lives: {self.lives}", True, WHITE)
        level_text = font.render(f"Level: {self.level}", True, WHITE)

        screen.blit(score_text, (int(WIDTH * 0.02), int(HEIGHT * 0.02)))
        screen.blit(lives_text, (WIDTH - int(WIDTH * 0.15), int(HEIGHT * 0.02)))
        screen.blit(level_text, (WIDTH // 2 - int(WIDTH * 0.04), int(HEIGHT * 0.02)))

        if self.paused:
            big_font = pygame.font.SysFont(None, int(HEIGHT * 0.08))
            pause_text = big_font.render("PAUSED", True, WHITE)
            rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(pause_text, rect)

        if self.game_over:
            big_font = pygame.font.SysFont(None, int(HEIGHT * 0.1))
            small_font = pygame.font.SysFont(None, int(HEIGHT * 0.05))

            game_over_text = big_font.render("GAME OVER", True, RED)
            score_text = small_font.render(f"Final Score: {self.score}", True, WHITE)
            restart_text = small_font.render("Press R to Restart or ESC to Quit", True, WHITE)

            rect1 = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - int(HEIGHT * 0.05)))
            rect2 = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + int(HEIGHT * 0.05)))
            rect3 = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + int(HEIGHT * 0.13)))

            screen.blit(game_over_text, rect1)
            screen.blit(score_text, rect2)
            screen.blit(restart_text, rect3)

# Main game loop
def main():
    game = Game()
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game.game_over and not game.paused:
                    if game.player.shoot(game.bullets):
                        bullet = Bullet(game.player.rect.centerx, game.player.rect.top)
                        game.bullets.add(bullet)
                        game.all_sprites.add(bullet)
                elif event.key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
                elif event.key == pygame.K_r and game.game_over:
                    game.reset()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        game.update()
        game.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
