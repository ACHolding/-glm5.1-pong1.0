import pygame
import sys
import random

# ─── Constants ───────────────────────────────────────────────
SCREEN_W, SCREEN_H = 640, 480
FPS = 60

BALL_SPEED = 3
PADDLE_SPEED = 4
AI_SPEED = 3
PADDLE_W, PADDLE_H = 10, 50
BALL_SIZE = 8
WIN_SCORE = 5
MAX_BALL_SPEED = 7.0

COL_BG = (0, 0, 0)
COL_MID = (56, 56, 56)
COL_BALL = (252, 252, 252)
COL_PADDLE = (252, 252, 252)
COL_TEXT = (252, 252, 252)
COL_PROMPT = (180, 180, 180)


class Paddle:
    def __init__(self, x):
        self.rect = pygame.Rect(x, SCREEN_H // 2 - PADDLE_H // 2, PADDLE_W, PADDLE_H)

    def move(self, dy):
        self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_W, SCREEN_H))

    def draw(self, surf):
        pygame.draw.rect(surf, COL_PADDLE, self.rect)


class Ball:
    def __init__(self):
        self.reset()

    def reset(self, toward_player: bool | None = None):
        self.x = float(SCREEN_W // 2 - BALL_SIZE // 2)
        self.y = float(SCREEN_H // 2 - BALL_SIZE // 2)
        if toward_player is None:
            toward_player = random.choice([True, False])
        direction = -1 if toward_player else 1
        angle = random.uniform(0.3, 0.7)
        self.vx = direction * BALL_SPEED
        self.vy = BALL_SPEED * random.choice([-1, 1]) * angle
        self.rect = pygame.Rect(int(self.x), int(self.y), BALL_SIZE, BALL_SIZE)

    def sync_rect(self):
        self.rect.topleft = (int(self.x), int(self.y))

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.y <= 0:
            self.y = 0
            self.vy = abs(self.vy)
        elif self.y >= SCREEN_H - BALL_SIZE:
            self.y = SCREEN_H - BALL_SIZE
            self.vy = -abs(self.vy)

        self.sync_rect()


class Pong:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Famicom Pong")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("couriernew", 52, bold=True)
        self.font_med = pygame.font.SysFont("couriernew", 28, bold=True)
        self.font_small = pygame.font.SysFont("couriernew", 20)

        self.reset_game()

    def reset_game(self):
        self.player = Paddle(20)
        self.ai = Paddle(SCREEN_W - 20 - PADDLE_W)
        self.ball = Ball()
        self.p_score = 0
        self.a_score = 0
        self.game_over = False
        self.winner = ""
        self.countdown = 90
        self._paddle_hit = False

    def ai_move(self):
        centre = self.ai.rect.centery
        target = self.ball.rect.centery
        diff = target - centre
        if abs(diff) > 4:
            self.ai.move(max(-AI_SPEED, min(AI_SPEED, diff)))

    def check_paddle(self, paddle, is_player: bool):
        if self._paddle_hit:
            return

        # Only bounce when the ball is moving toward this paddle
        if is_player and self.ball.vx >= 0:
            return
        if not is_player and self.ball.vx <= 0:
            return

        prev_x = self.ball.x - self.ball.vx
        prev_rect = pygame.Rect(int(prev_x), int(self.ball.y), BALL_SIZE, BALL_SIZE)
        hit = self.ball.rect.colliderect(paddle.rect) or prev_rect.colliderect(
            paddle.rect
        )
        if not hit:
            return

        rel = (self.ball.rect.centery - paddle.rect.centery) / (PADDLE_H / 2)
        rel = max(-1.0, min(1.0, rel))
        angle = rel * 0.75

        speed = (self.ball.vx**2 + self.ball.vy**2) ** 0.5
        speed = min(max(speed * 1.04, BALL_SPEED), MAX_BALL_SPEED)

        vx_mag = max(BALL_SPEED * 0.5, speed * (1 - angle**2) ** 0.5)
        self.ball.vx = vx_mag if is_player else -vx_mag
        self.ball.vy = speed * angle

        if is_player:
            self.ball.x = paddle.rect.right + 1
        else:
            self.ball.x = paddle.rect.left - BALL_SIZE - 1

        self.ball.sync_rect()
        self._paddle_hit = True

    def serve_after_point(self, toward_player: bool):
        self.ball.reset(toward_player=toward_player)
        self.countdown = 90

    def check_score(self):
        if self.game_over:
            return

        if self.ball.x + BALL_SIZE < 0:
            self.a_score += 1
            if self.a_score >= WIN_SCORE:
                self.game_over = True
                self.winner = "CPU"
            else:
                self.serve_after_point(toward_player=True)
        elif self.ball.x > SCREEN_W:
            self.p_score += 1
            if self.p_score >= WIN_SCORE:
                self.game_over = True
                self.winner = "PLAYER"
            else:
                self.serve_after_point(toward_player=False)

    def draw_field(self):
        for y in range(0, SCREEN_H, 16):
            pygame.draw.rect(self.screen, COL_MID, (SCREEN_W // 2 - 2, y, 4, 8))

    def draw_scores(self):
        t1 = self.font_big.render(str(self.p_score), True, COL_TEXT)
        t2 = self.font_big.render(str(self.a_score), True, COL_TEXT)
        self.screen.blit(t1, (SCREEN_W // 4 - t1.get_width() // 2, 20))
        self.screen.blit(t2, (3 * SCREEN_W // 4 - t2.get_width() // 2, 20))

    def draw_countdown(self):
        if self.countdown <= 0 or self.game_over:
            return
        secs = max(1, (self.countdown + FPS - 1) // FPS)
        msg = self.font_med.render(str(secs), True, COL_PROMPT)
        self.screen.blit(
            msg, (SCREEN_W // 2 - msg.get_width() // 2, SCREEN_H // 2 - 14)
        )

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        w = self.font_med.render(f"{self.winner} WINS!", True, COL_TEXT)
        self.screen.blit(w, (SCREEN_W // 2 - w.get_width() // 2, SCREEN_H // 2 - 60))

        go = self.font_med.render("GAME OVER", True, COL_TEXT)
        self.screen.blit(go, (SCREEN_W // 2 - go.get_width() // 2, SCREEN_H // 2 - 20))

        r = self.font_small.render("Y = Restart   N / ESC = Quit", True, COL_PROMPT)
        self.screen.blit(r, (SCREEN_W // 2 - r.get_width() // 2, SCREEN_H // 2 + 30))

    def run(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_ESCAPE,):
                        running = False
                    elif self.game_over:
                        if ev.key == pygame.K_y:
                            self.reset_game()
                        elif ev.key == pygame.K_n:
                            running = False

            if not self.game_over:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    self.player.move(-PADDLE_SPEED)
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    self.player.move(PADDLE_SPEED)

                if self.countdown > 0:
                    self.countdown -= 1
                else:
                    self._paddle_hit = False
                    self.ball.update()
                    self.ai_move()
                    self.check_paddle(self.player, True)
                    self.check_paddle(self.ai, False)
                    self.check_score()

            self.screen.fill(COL_BG)
            self.draw_field()
            self.draw_scores()
            self.player.draw(self.screen)
            self.ai.draw(self.screen)
            if not self.game_over:
                self.ball.draw(self.screen)
                self.draw_countdown()
            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    Pong().run()
    sys.exit(0)


if __name__ == "__main__":
    main()
