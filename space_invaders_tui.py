#!/usr/bin/env python3
"""
Space Invaders - TUI (Text User Interface) version using curses.
Runs in terminal, no extra dependencies.
Controls: Left/Right arrows or A/D to move, Space to fire, Q to quit.
"""

import curses
import random
import time

WIDTH = 60
HEIGHT = 20
PLAYER_CHAR = "^"
ENEMY_CHAR = "W"
BULLET_CHAR = "|"
ENEMY_BULLET_CHAR = "!"
PLAYER_LIVES = 3
FRAME_DELAY = 0.05


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player_x = WIDTH // 2
        self.player_lives = PLAYER_LIVES
        self.score = 0
        self.level = 1
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = self.make_enemies()
        self.running = True
        self.game_over = False
        self.last_fire_time = 0

    def make_enemies(self):
        enemies = []
        rows, cols = 4, 10
        for r in range(rows):
            for c in range(cols):
                x = 5 + c * 5
                y = 2 + r * 2
                enemies.append([x, y])
        return enemies

    def move_player(self, dx):
        self.player_x = max(1, min(WIDTH - 2, self.player_x + dx))

    def fire(self):
        now = time.time()
        if now - self.last_fire_time < 0.3:
            return
        self.last_fire_time = now
        self.bullets.append([self.player_x, HEIGHT - 3])

    def update(self):
        if self.game_over:
            return
        for b in self.bullets:
            b[1] -= 1
        self.bullets = [b for b in self.bullets if b[1] > 0]

        for eb in self.enemy_bullets:
            eb[1] += 1
        self.enemy_bullets = [eb for eb in self.enemy_bullets if eb[1] < HEIGHT - 1]

        move_dir = 1 if int(time.time() * 2) % 4 < 2 else -1
        for e in self.enemies:
            e[0] += move_dir * 0.2

        fire_chance = 0.05 * (1 + (self.level - 1) * 0.2)
        fire_chance = min(fire_chance, 0.3)  # optional cap
        if random.random() < fire_chance and self.enemies:
            shooter = random.choice(self.enemies)
            self.enemy_bullets.append([int(shooter[0]), int(shooter[1]) + 1])

        for b in list(self.bullets):
            for e in list(self.enemies):
                if abs(b[0] - e[0]) < 1 and abs(b[1] - e[1]) < 1:
                    self.score += 10
                    self.enemies.remove(e)
                    self.bullets.remove(b)
                    break

        for eb in list(self.enemy_bullets):
            if abs(eb[0] - self.player_x) < 1 and eb[1] >= HEIGHT - 3:
                self.player_lives -= 1
                self.enemy_bullets.remove(eb)
                if self.player_lives <= 0:
                    self.game_over = True
                break

        if not self.enemies:
            self.level += 1
            self.enemies = self.make_enemies()

    def draw(self, stdscr):
        stdscr.clear()
        for e in self.enemies:
            x, y = int(e[0]), int(e[1])
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                stdscr.addch(y, x, ENEMY_CHAR)

        for b in self.bullets:
            x, y = int(b[0]), int(b[1])
            if 0 <= y < HEIGHT:
                stdscr.addch(y, x, BULLET_CHAR)

        for eb in self.enemy_bullets:
            x, y = int(eb[0]), int(eb[1])
            if 0 <= y < HEIGHT:
                stdscr.addch(y, x, ENEMY_BULLET_CHAR)

        stdscr.addch(HEIGHT - 2, self.player_x, PLAYER_CHAR)

        info = f"Score: {self.score}  Lives: {self.player_lives}  Level: {self.level}"
        stdscr.addstr(HEIGHT, 0, info)

        if self.game_over:
            msg = " GAME OVER - Press R to restart, Q to quit "
            stdscr.addstr(HEIGHT // 2, (WIDTH - len(msg)) // 2, msg)
        stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    game = Game()

    while game.running:
        key = stdscr.getch()
        if key in [ord("q"), ord("Q")]:
            game.running = False
        elif key in [ord("a"), curses.KEY_LEFT]:
            game.move_player(-1)
        elif key in [ord("d"), curses.KEY_RIGHT]:
            game.move_player(1)
        elif key == ord(" "):
            game.fire()
        elif key in [ord("r"), ord("R")]:
            if game.game_over:
                game.reset()

        game.update()
        game.draw(stdscr)
        time.sleep(FRAME_DELAY)


if __name__ == "__main__":
    curses.wrapper(main)
