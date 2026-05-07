import pygame
import sys
import json
import os
import random
import math

pygame.init()

WIDTH, HEIGHT = 1000, 650
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mars Mission - Survival Game")
clock = pygame.time.Clock()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 150, 255)
ORANGE = (255, 120, 0)
YELLOW = (255, 220, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (60, 60, 60)

font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 52)
small_font = pygame.font.Font(None, 24)

pygame.mixer.init()
sound_enabled = True
music_volume = 0.5
music_paused = False

def init_music():
    global music_paused
    paths = ["music/music.ogg", "music/music.mp3", "music/music.wav", "images/music.ogg", "music.ogg"]
    for path in paths:
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(music_volume)
            pygame.mixer.music.play(-1)
            music_paused = False
            break

def set_music_volume(vol):
    global music_volume
    music_volume = vol
    pygame.mixer.music.set_volume(music_volume)

def toggle_music():
    global music_paused
    if pygame.mixer.music.get_busy() or music_paused:
        if music_paused:
            pygame.mixer.music.unpause()
            music_paused = False
        else:
            pygame.mixer.music.pause()
            music_paused = True
    else:
        init_music()

init_music()

def load_img(path, size=None):
    try:
        if os.path.exists(path):
            img = pygame.image.load(path)
            if size:
                img = pygame.transform.scale(img, size)
            return img
    except:
        pass
    return None

if not os.path.exists("images"):
    os.makedirs("images")

# завантаження картинок
BASE_IMG = load_img("images/base.png", (60, 60))
if BASE_IMG is None:
    BASE_IMG = load_img("images/base.jpg", (60, 60))
if BASE_IMG is None:
    BASE_IMG = pygame.Surface((60, 60))
    BASE_IMG.fill(GREEN)
    pygame.draw.rect(BASE_IMG, WHITE, BASE_IMG.get_rect(), 3)

FUEL_IMG = load_img("images/fuel.png", (30, 30))
if FUEL_IMG is None:
    FUEL_IMG = pygame.Surface((22, 26))
    FUEL_IMG.fill(ORANGE)

OXYGEN_IMG = load_img("images/oxygen.png", (30, 30))
if OXYGEN_IMG is None:
    OXYGEN_IMG = pygame.Surface((24, 26))
    OXYGEN_IMG.fill(BLUE)

class AnimatedPlayer:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 45, 45)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.fuel = 100
        self.oxygen = 100
        self.coins = 0
        
        self.walk_frames = []
        for i in range(1, 4):
            img = load_img(f"images/astronaut{i}.png", (45, 45))
            if img:
                self.walk_frames.append(img)
        
        if not self.walk_frames:
            surf = pygame.Surface((45, 45))
            surf.fill(WHITE)
            self.walk_frames = [surf, surf, surf]
        
        self.walk_frame = 1
        self.anim_speed = 0.12
        self.walk_dir = 1
    
    def update(self, keys, platforms, storm=False):
        self.vel_x = 0
        speed = 5.5
        moving = False
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -speed
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = speed
            moving = True
        
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = -13
        
        self.vel_y += 0.55
        if self.vel_y > 12:
            self.vel_y = 12
        
        self.rect.x += self.vel_x
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_x > 0:
                    self.rect.right = p.left
                elif self.vel_x < 0:
                    self.rect.left = p.right
        
        self.rect.y += self.vel_y
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_y > 0:
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.bottom
                    self.vel_y = 0
        
        if moving:
            self.walk_frame += self.anim_speed * self.walk_dir
            if self.walk_frame >= len(self.walk_frames):
                self.walk_frame = len(self.walk_frames) - 1
                self.walk_dir = -1
            elif self.walk_frame < 0:
                self.walk_frame = 0
                self.walk_dir = 1
        else:
            self.walk_frame = 1
            if self.walk_frame >= len(self.walk_frames):
                self.walk_frame = 0
        
        if moving and not self.on_ground:
            self.fuel -= 0.06
            self.oxygen -= 0.05
        elif moving:
            self.fuel -= 0.03
            self.oxygen -= 0.02
        
        if storm:
            self.oxygen -= 0.1
        
        self.fuel = max(0, min(100, self.fuel))
        self.oxygen = max(0, min(100, self.oxygen))
    
    def draw(self, surface, camera_x):
        frame = int(self.walk_frame)
        if frame >= len(self.walk_frames):
            frame = len(self.walk_frames) - 1
        img = self.walk_frames[frame]
        if self.vel_x < 0:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, (self.rect.x - camera_x, self.rect.y))
    
    def collect_coin(self):
        self.coins += 1
    
    def collect_fuel(self):
        self.fuel = min(100, self.fuel + 25)
    
    def collect_oxygen(self):
        self.oxygen = min(100, self.oxygen + 25)

class AnimatedCoin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 28, 28)
        self.collected = False
        self.anim_y = 0
        self.anim_dir = 1
        self.frame = 0
        self.frames = []
        
        for i in range(1, 7):
            path = f"images/coin{i}.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path)
                    img = pygame.transform.scale(img, (28, 28))
                    self.frames.append(img)
                except:
                    pass
        
        if not self.frames:
            for angle in range(0, 360, 60):
                surf = pygame.Surface((28, 28), pygame.SRCALPHA)
                c = 14
                sx = 12 + 4 * abs(math.sin(math.radians(angle)))
                sy = 12 - 2 * abs(math.sin(math.radians(angle)))
                for j in range(3):
                    r = int(sx - j*2)
                    col = (255 - j*40, 220 - j*30, 50 - j*10)
                    pygame.draw.ellipse(surf, col, (c - r//2, c - r//2, r, r))
                pygame.draw.ellipse(surf, (180, 100, 20), (c - 13, c - 13, 26, 26), 2)
                self.frames.append(surf)
    
    def update(self):
        if not self.collected:
            self.anim_y += 0.3 * self.anim_dir
            if self.anim_y > 5:
                self.anim_dir = -1
            elif self.anim_y < -5:
                self.anim_dir = 1
            self.frame += 0.12
            if self.frame >= len(self.frames):
                self.frame = 0
    
    def draw(self, surface, camera_x):
        if not self.collected and self.frames:
            idx = int(self.frame) % len(self.frames)
            img = self.frames[idx]
            glow = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 255, 100, 60), (18, 18), 18)
            surface.blit(glow, (self.x - camera_x - 4, self.y - 4 + self.anim_y))
            surface.blit(img, (self.x - camera_x, self.y + self.anim_y))

class ResourceItem:
    def __init__(self, x, y, rtype):
        self.x = x
        self.y = y
        self.rtype = rtype
        self.collected = False
        self.anim_y = 0
        self.anim_dir = 1
        self.img = FUEL_IMG if rtype == "fuel" else OXYGEN_IMG
        self.rect = pygame.Rect(x, y, self.img.get_width(), self.img.get_height())
    
    def update(self):
        if not self.collected:
            self.anim_y += 0.3 * self.anim_dir
            if self.anim_y > 5:
                self.anim_dir = -1
            elif self.anim_y < -5:
                self.anim_dir = 1
    
    def draw(self, surface, camera_x):
        if not self.collected:
            col = ORANGE if self.rtype == "fuel" else BLUE
            glow = pygame.Surface((self.img.get_width() + 10, self.img.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow, (col[0], col[1], col[2], 80), (glow.get_width()//2, glow.get_height()//2), glow.get_width()//2)
            surface.blit(glow, (self.x - camera_x - 5, self.y - 5 + self.anim_y))
            surface.blit(self.img, (self.x - camera_x, self.y + self.anim_y))

LEVEL1_BG = load_img("images/level1_bg.jpg", (WIDTH, HEIGHT))
LEVEL2_BG = load_img("images/level2_bg.jpg", (WIDTH, HEIGHT))
LEVEL3_BG = load_img("images/level3_bg.jpg", (WIDTH, HEIGHT))
LEVEL4_BG = load_img("images/level4_bg.jpg", (WIDTH, HEIGHT))
LEVEL5_BG = load_img("images/level5_bg.jpg", (WIDTH, HEIGHT))
LEVEL6_BG = load_img("images/level6_bg.jpg", (WIDTH, HEIGHT))

PLATFORM_TEXTURE = load_img("images/platform_texture.png", (100, 20))

textures = {}

def get_texture(w, h):
    key = (w, h)
    if key not in textures:
        if PLATFORM_TEXTURE:
            textures[key] = pygame.transform.scale(PLATFORM_TEXTURE, (w, h))
        else:
            tex = pygame.Surface((w, h))
            base = (160, 90, 50)
            tex.fill(base)
            for _ in range(w * h // 15):
                x = random.randint(0, w - 1)
                y = random.randint(0, h - 1)
                b = random.randint(-20, 20)
                col = (min(255, max(0, base[0] + b)),
                       min(255, max(0, base[1] + b - 10)),
                       min(255, max(0, base[2] + b - 15)))
                pygame.draw.circle(tex, col, (x, y), random.randint(1, 2))
            textures[key] = tex
    return textures[key]

class BeautifulPlatform:
    @staticmethod
    def draw(surf, x, y, w, h, cam_x):
        sx = x - cam_x
        tex = get_texture(w, h)
        surf.blit(tex, (sx, y))
        pygame.draw.line(surf, (120, 70, 40), (sx, y), (sx, y + h), 2)
        pygame.draw.line(surf, (120, 70, 40), (sx + w - 1, y), (sx + w - 1, y + h), 2)
        pygame.draw.line(surf, (220, 160, 100), (sx + 2, y + 1), (sx + w - 3, y + 1), 1)

def create_gear(size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    pygame.draw.circle(surf, GRAY, (c, c), size//2 - 2)
    pygame.draw.circle(surf, DARK_GRAY, (c, c), size//2 - 4)
    for i in range(8):
        ang = i * 45
        rad = math.radians(ang)
        x1 = c + (size//2 - 2) * math.cos(rad)
        y1 = c + (size//2 - 2) * math.sin(rad)
        x2 = c + (size//2 + 4) * math.cos(rad)
        y2 = c + (size//2 + 4) * math.sin(rad)
        pygame.draw.line(surf, GRAY, (x1, y1), (x2, y2), 3)
    pygame.draw.circle(surf, DARK_GRAY, (c, c), size//4)
    return surf

GEAR = create_gear(36)

SAVE_FILE = "save.json"

def save_progress(lvl):
    with open(SAVE_FILE, "w") as f:
        json.dump({"unlocked_level": lvl}, f)

def load_progress():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f).get("unlocked_level", 1)
    return 1

class SettingsButton:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.open = False
        self.vol = music_volume
        self.slider = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 8)
        self.knob = pygame.Rect(WIDTH//2 - 100 + int(200 * self.vol), HEIGHT//2 + 75, 15, 18)
        self.drag = False
    
    def draw(self, surf):
        surf.blit(GEAR, (self.rect.x, self.rect.y))
        if not self.open:
            return None, None, None
        
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        surf.blit(overlay, (0, 0))
        
        pw, ph = 400, 330
        px = WIDTH//2 - pw//2
        py = HEIGHT//2 - ph//2
        panel = pygame.Surface((pw, ph))
        panel.fill(DARK_GRAY)
        pygame.draw.rect(panel, WHITE, panel.get_rect(), 3, border_radius=10)
        surf.blit(panel, (px, py))
        
        title = font.render("SETTINGS", True, WHITE)
        surf.blit(title, (WIDTH//2 - title.get_width()//2, py + 20))
        
        home_btn = pygame.Rect(px + 50, py + 80, 300, 50)
        pygame.draw.rect(surf, (80, 80, 200), home_btn, border_radius=8)
        pygame.draw.rect(surf, WHITE, home_btn, 2, border_radius=8)
        home_text = font.render("MAIN MENU", True, WHITE)
        surf.blit(home_text, (WIDTH//2 - home_text.get_width()//2, py + 92))
        
        sound_btn = pygame.Rect(px + 50, py + 150, 300, 45)
        if not music_paused:
            btn_col = (80, 180, 80)
            sound_txt = "MUSIC ON"
        else:
            btn_col = (180, 80, 80)
            sound_txt = "MUSIC OFF"
        pygame.draw.rect(surf, btn_col, sound_btn, border_radius=8)
        pygame.draw.rect(surf, WHITE, sound_btn, 2, border_radius=8)
        sound_text = font.render(sound_txt, True, WHITE)
        surf.blit(sound_text, (WIDTH//2 - sound_text.get_width()//2, py + 160))
        
        vol_text = small_font.render(f"VOLUME: {int(self.vol * 100)}%", True, WHITE)
        surf.blit(vol_text, (WIDTH//2 - vol_text.get_width()//2, py + 225))
        
        pygame.draw.rect(surf, GRAY, self.slider, border_radius=4)
        pygame.draw.rect(surf, BLUE, (self.slider.x, self.slider.y, self.slider.width * self.vol, self.slider.height), border_radius=4)
        knob_x = self.slider.x + int(self.slider.width * self.vol) - 7
        self.knob = pygame.Rect(knob_x, self.slider.y - 5, 15, 18)
        pygame.draw.rect(surf, WHITE, self.knob, border_radius=7)
        
        close_btn = pygame.Rect(WIDTH//2 - 50, py + 280, 100, 30)
        pygame.draw.rect(surf, (200, 100, 100), close_btn, border_radius=8)
        close_text = small_font.render("CLOSE", True, WHITE)
        surf.blit(close_text, (WIDTH//2 - close_text.get_width()//2, py + 287))
        
        return home_btn, sound_btn, close_btn
    
    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.open = not self.open
            return "open", None
        
        if self.open:
            home = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 85, 300, 50)
            sound = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 15, 300, 45)
            close = pygame.Rect(WIDTH//2 - 50, HEIGHT//2 + 115, 100, 30)
            
            if home.collidepoint(pos):
                self.open = False
                return "home", None
            elif sound.collidepoint(pos):
                toggle_music()
                return "sound", not music_paused
            elif close.collidepoint(pos):
                self.open = False
                return "close", None
            elif self.slider.collidepoint(pos):
                self.drag = True
        return None, None
    
    def handle_drag(self, pos):
        if self.drag and self.open:
            x = max(self.slider.x, min(self.slider.x + self.slider.width, pos[0]))
            self.vol = (x - self.slider.x) / self.slider.width
            set_music_volume(self.vol)
    
    def stop_drag(self):
        self.drag = False

class Level:
    def __init__(self, num):
        self.num = num
        self.platforms = []
        self.items = []
        self.base_rect = None
        self.start = (100, 500)
        self.req_coins = 0
        self.storm = False
        self.load()
    
    def load(self):
        self.platforms = [pygame.Rect(0, HEIGHT - 50, 5000, 20)]
        if self.num == 1:
            self.lvl1()
        elif self.num == 2:
            self.lvl2()
        elif self.num == 3:
            self.lvl3()
        elif self.num == 4:
            self.lvl4()
        elif self.num == 5:
            self.lvl5()
        elif self.num == 6:
            self.lvl6()
        
        if self.platforms:
            last = self.platforms[-1]
            self.base_rect = pygame.Rect(last.x + last.width - 80, last.y - 65, 55, 55)
    
    def add_coin(self, x, y):
        self.items.append(AnimatedCoin(x, y))
    
    def add_fuel(self, x, y):
        self.items.append(ResourceItem(x, y, "fuel"))
    
    def add_oxygen(self, x, y):
        self.items.append(ResourceItem(x, y, "oxygen"))
    
    def lvl1(self):
        data = [
            (200, 520, 120), (350, 480, 80), (480, 440, 100), (620, 500, 70),
            (740, 460, 90), (880, 410, 80), (1020, 450, 100), (1170, 390, 70),
            (1300, 430, 90), (1440, 370, 80), (1580, 410, 100), (1730, 460, 70),
            (1870, 420, 90), (2010, 380, 80), (2150, 440, 100), (2300, 490, 80),
            (2450, 450, 90), (2600, 400, 70), (2750, 360, 100), (2910, 420, 80),
            (3060, 470, 90), (3210, 430, 70), (3360, 390, 100), (3510, 450, 80),
            (3660, 500, 120),
        ]
        for x, y, w in data:
            self.platforms.append(pygame.Rect(x, y, w, 20))
        
        for i in [2, 5, 8, 12, 16, 20]:
            if i <= len(data):
                p = data[i-1]
                self.add_coin(p[0] + 40, p[1] - 25)
        for i in [4, 9, 13, 22]:
            if i <= len(data):
                p = data[i-1]
                self.add_fuel(p[0] + 50, p[1] - 25)
        for i in [6, 10, 14, 18]:
            if i <= len(data):
                p = data[i-1]
                self.add_oxygen(p[0] + 30, p[1] - 25)
        
        self.req_coins = 6
        self.storm = False
    
    def lvl2(self):
        data = [
            (200, 520, 100), (360, 470, 80), (520, 490, 90), (680, 440, 70),
            (840, 460, 100), (1000, 420, 80), (1160, 440, 90), (1320, 390, 70),
            (1480, 410, 100), (1640, 370, 80), (1800, 390, 90), (1960, 350, 70),
            (2120, 370, 100), (2280, 340, 80), (2440, 360, 90), (2600, 330, 70),
            (2760, 350, 100), (2920, 340, 80), (3080, 370, 90), (3240, 390, 70),
            (3400, 410, 100), (3560, 430, 80), (3720, 450, 90),
        ]
        for x, y, w in data:
            self.platforms.append(pygame.Rect(x, y, w, 20))
        
        for i in [2, 5, 8, 11, 14, 17, 20]:
            if i <= len(data):
                p = data[i-1]
                self.add_coin(p[0] + 35, p[1] - 25)
        for i in [4, 10, 16]:
            if i <= len(data):
                p = data[i-1]
                self.add_fuel(p[0] + 50, p[1] - 25)
        for i in [7, 13, 19]:
            if i <= len(data):
                p = data[i-1]
                self.add_oxygen(p[0] + 20, p[1] - 25)
        
        self.req_coins = 7
        self.storm = True
    
    def lvl3(self):
        data = [
            (200, 520, 90), (350, 460, 80), (500, 480, 70), (640, 420, 80),
            (790, 440, 70), (940, 390, 80), (1090, 410, 70), (1240, 360, 80),
            (1390, 380, 70), (1540, 340, 80), (1690, 360, 70), (1840, 330, 80),
            (1990, 350, 70), (2140, 320, 80), (2290, 340, 70), (2440, 310, 80),
            (2590, 330, 70), (2740, 320, 80), (2890, 350, 70), (3040, 370, 80),
            (3190, 390, 70), (3340, 410, 80), (3490, 430, 70), (3640, 450, 80),
            (3790, 470, 90),
        ]
        for x, y, w in data:
            self.platforms.append(pygame.Rect(x, y, w, 20))
        
        for i in [2, 5, 8, 11, 14, 17, 20, 23]:
            if i <= len(data):
                p = data[i-1]
                self.add_coin(p[0] + 30, p[1] - 25)
        for i in [4, 10, 16, 22]:
            if i <= len(data):
                p = data[i-1]
                self.add_fuel(p[0] + 45, p[1] - 25)
        for i in [7, 13, 19]:
            if i <= len(data):
                p = data[i-1]
                self.add_oxygen(p[0] + 18, p[1] - 25)
        
        self.req_coins = 8
        self.storm = True
    
    def lvl4(self):
        data = [
            (200, 520, 80), (330, 450, 70), (460, 470, 80), (590, 400, 70),
            (720, 420, 80), (850, 370, 70), (980, 390, 80), (1110, 340, 70),
            (1240, 360, 80), (1370, 310, 70), (1500, 330, 80), (1630, 290, 70),
            (1760, 310, 80), (1890, 280, 70), (2020, 300, 80), (2150, 270, 70),
            (2280, 290, 80), (2410, 280, 70), (2540, 310, 80), (2670, 330, 70),
            (2800, 350, 80), (2930, 370, 70), (3060, 390, 80), (3190, 410, 70),
            (3320, 430, 80), (3450, 450, 70), (3580, 470, 80), (3710, 490, 80),
        ]
        for x, y, w in data:
            self.platforms.append(pygame.Rect(x, y, w, 20))
        
        for i in [2, 5, 8, 11, 14, 17, 20, 23, 26]:
            if i <= len(data):
                p = data[i-1]
                self.add_coin(p[0] + 30, p[1] - 25)
        for i in [4, 10, 16, 22]:
            if i <= len(data):
                p = data[i-1]
                self.add_fuel(p[0] + 45, p[1] - 25)
        for i in [7, 13, 19, 25]:
            if i <= len(data):
                p = data[i-1]
                self.add_oxygen(p[0] + 18, p[1] - 25)
        
        self.req_coins = 9
        self.storm = True
    
    def lvl5(self):
        data = [
            (200, 520, 70), (320, 440, 60), (440, 460, 70), (560, 390, 60),
            (680, 410, 70), (800, 350, 60), (920, 370, 70), (1040, 310, 60),
            (1160, 330, 70), (1280, 280, 60), (1400, 300, 70), (1520, 260, 60),
            (1640, 280, 70), (1760, 250, 60), (1880, 270, 70), (2000, 240, 60),
            (2120, 260, 70), (2240, 250, 60), (2360, 280, 70), (2480, 300, 60),
            (2600, 320, 70), (2720, 340, 60), (2840, 360, 70), (2960, 380, 60),
            (3080, 400, 70), (3200, 420, 60), (3320, 440, 70), (3440, 460, 60),
            (3560, 480, 70), (3680, 500, 70),
        ]
        for x, y, w in data:
            self.platforms.append(pygame.Rect(x, y, w, 20))
        
        for i in [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]:
            if i <= len(data):
                p = data[i-1]
                self.add_coin(p[0] + 25, p[1] - 25)
        for i in [4, 10, 16, 22, 28]:
            if i <= len(data):
                p = data[i-1]
                self.add_fuel(p[0] + 40, p[1] - 25)
        for i in [7, 13, 19, 25]:
            if i <= len(data):
                p = data[i-1]
                self.add_oxygen(p[0] + 15, p[1] - 25)
        
        self.req_coins = 10
        self.storm = True
    
    def lvl6(self):
        data = [
            (200, 520, 70), (310, 450, 60), (420, 470, 70), (540, 400, 60),
            (660, 420, 70), (780, 360, 60), (900, 380, 70), (1020, 320, 60),
            (1140, 340, 70), (1260, 290, 60), (1380, 310, 70), (1500, 260, 60),
            (1620, 280, 70), (1740, 240, 60), (1860, 260, 70), (1980, 230, 60),
            (2100, 250, 70), (2220, 240, 60), (2340, 270, 70), (2460, 290, 60),
            (2580, 310, 70), (2700, 330, 60), (2820, 350, 70), (2940, 370, 60),
            (3060, 390, 70), (3180, 410, 60), (3300, 430, 70), (3420, 450, 60),
            (3540, 470, 70), (3660, 490, 60), (3780, 510, 70), (3900, 490, 60),
            (4020, 470, 70), (4140, 450, 60), (4260, 470, 70), (4380, 490, 70),
        ]
        for x, y, w in data:
            self.platforms.append(pygame.Rect(x, y, w, 20))
        
        for i in [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]:
            if i <= len(data):
                p = data[i-1]
                self.add_coin(p[0] + 25, p[1] - 25)
        for i in [4, 10, 16, 22, 28, 34]:
            if i <= len(data):
                p = data[i-1]
                self.add_fuel(p[0] + 40, p[1] - 25)
        for i in [7, 13, 19, 25, 31]:
            if i <= len(data):
                p = data[i-1]
                self.add_oxygen(p[0] + 15, p[1] - 25)
        
        self.req_coins = 12
        self.storm = True

class Game:
    def __init__(self):
        self.state = "menu"
        self.current = load_progress()
        self.unlocked = self.current
        self.player = None
        self.level = None
        self.cam_x = 0
        self.storm_timer = 0
        self.storm_active = False
        self.msg_timer = 0
        self.msg = ""
        self.victory_anim = 0
        self.btn = SettingsButton(WIDTH - 50, 15, 36)
        
    def start_level(self, num):
        self.current = num
        self.level = Level(num)
        self.player = AnimatedPlayer(self.level.start[0], self.level.start[1])
        self.cam_x = 0
        self.storm_timer = random.randint(400, 700)
        self.storm_active = False
        self.victory_anim = 0
        self.state = "playing"
    
    def update(self, keys):
        if self.state != "playing":
            return
        
        if self.btn.open:
            return
        
        if self.level.storm:
            self.storm_timer -= 1
            if self.storm_timer <= 0:
                self.storm_active = not self.storm_active
                if self.storm_active:
                    self.storm_timer = random.randint(300, 500)
                else:
                    self.storm_timer = random.randint(400, 700)
        
        self.player.update(keys, self.level.platforms, self.storm_active)
        
        for item in self.level.items[:]:
            if not item.collected and self.player.rect.colliderect(item.rect):
                item.collected = True
                if isinstance(item, AnimatedCoin):
                    self.player.collect_coin()
                elif hasattr(item, 'rtype'):
                    if item.rtype == "fuel":
                        self.player.collect_fuel()
                    elif item.rtype == "oxygen":
                        self.player.collect_oxygen()
        
        for item in self.level.items:
            item.update()
        
        self.cam_x = self.player.rect.x - 350
        if self.cam_x < 0:
            self.cam_x = 0
        if self.cam_x > 5000:
            self.cam_x = 5000
        
        if self.player.fuel <= 0 or self.player.oxygen <= 0 or self.player.rect.y > HEIGHT + 200:
            self.state = "game_over"
        
        if self.level.base_rect and self.player.rect.colliderect(self.level.base_rect):
            if self.player.coins >= self.level.req_coins:
                self.victory_anim += 1
                if self.victory_anim > 20:
                    self.state = "level_complete"
                    if self.current < 6 and self.current + 1 > self.unlocked:
                        self.unlocked = self.current + 1
                        save_progress(self.unlocked)
            else:
                self.msg = f"ТРЕБА ЩЕ {self.level.req_coins - self.player.coins} МОНЕТ"
                self.msg_timer = 90
                if self.player.rect.x < self.level.base_rect.x:
                    self.player.rect.x -= 30
                else:
                    self.player.rect.x += 30
    
    def draw_menu(self):
        for y in range(HEIGHT):
            r = 40 + y // 10
            g = 20 + y // 15
            b = 60 + y // 8
            pygame.draw.line(screen, (min(255, r), min(255, g), min(255, b)), (0, y), (WIDTH, y))
        
        mars_x, mars_y = WIDTH - 150, HEIGHT - 150
        for i in range(4):
            alpha = 120 - i * 30
            glow = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(glow, (180, 80, 50, alpha), (60, 60), 60 - i * 10)
            screen.blit(glow, (mars_x - 60, mars_y - 60))
        pygame.draw.circle(screen, (200, 100, 60), (mars_x, mars_y), 50)
        pygame.draw.circle(screen, (160, 70, 35), (mars_x - 15, mars_y - 10), 8)
        pygame.draw.circle(screen, (140, 60, 25), (mars_x + 10, mars_y - 20), 5)
        pygame.draw.circle(screen, (150, 65, 30), (mars_x + 20, mars_y + 15), 6)
        
        small_x, small_y = 120, 150
        pygame.draw.circle(screen, (100, 70, 140), (small_x, small_y), 25)
        pygame.draw.circle(screen, (80, 50, 110), (small_x - 5, small_y - 3), 8)
        pygame.draw.circle(screen, (90, 55, 120), (small_x + 8, small_y + 5), 5)
        for offset in range(-2, 3):
            pygame.draw.ellipse(screen, (120, 90, 160, 80), 
                               (small_x - 40, small_y + offset - 5, 80, 15), 1)
        
        title = big_font.render("MARS MISSION", True, (255, 200, 100))
        shadow = big_font.render("MARS MISSION", True, (80, 50, 20))
        screen.blit(shadow, (WIDTH//2 - title.get_width()//2 + 3, 63))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))
        
        sub = font.render("Виживи на Марсі", True, WHITE)
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 130))
        
        ys = 200
        bw, bh = 90, 70
        gap = 20
        
        for i in range(1, 7):
            r = (i-1) // 3
            c = (i-1) % 3
            x = WIDTH//2 - 150 + c * (bw + gap)
            y = ys + r * (bh + gap)
            pygame.draw.rect(screen, (0, 0, 0, 100), (x + 3, y + 3, bw, bh), border_radius=10)
        
        for i in range(1, 7):
            r = (i-1) // 3
            c = (i-1) % 3
            x = WIDTH//2 - 150 + c * (bw + gap)
            y = ys + r * (bh + gap)
            
            col = (80, 180, 80) if i <= self.unlocked else (100, 100, 100)
            lock = "OPEN" if i <= self.unlocked else "LOCK"
            
            pygame.draw.rect(screen, col, (x, y, bw, bh), border_radius=10)
            pygame.draw.rect(screen, WHITE, (x, y, bw, bh), 3, border_radius=10)
            
            lvl_txt = big_font.render(str(i), True, WHITE)
            screen.blit(lvl_txt, (x + 35, y + 18))
            screen.blit(small_font.render(lock, True, WHITE), (x + 30, y + 50))
        
        pygame.draw.line(screen, (100, 80, 150), (50, HEIGHT - 100), (WIDTH - 50, HEIGHT - 100), 2)
        pygame.draw.line(screen, (80, 60, 120), (50, HEIGHT - 102), (WIDTH - 50, HEIGHT - 102), 1)
        
        ctrl = small_font.render("WASD або СТРІЛКИ : рух   |   ПРОБІЛ / ВВЕРХ / W : стрибок", True, WHITE)
        ctrl_sh = small_font.render("WASD або СТРІЛКИ : рух   |   ПРОБІЛ / ВВЕРХ / W : стрибок", True, BLACK)
        screen.blit(ctrl_sh, (WIDTH//2 - ctrl.get_width()//2 + 1, 431))
        screen.blit(ctrl, (WIDTH//2 - ctrl.get_width()//2, 430))
        
        tip = small_font.render("Збери монети та дійди до ЗЕЛЕНОЇ БАЗИ", True, YELLOW)
        screen.blit(tip, (WIDTH//2 - tip.get_width()//2, 480))
        
        start_txt = font.render("Натисни на рівень мишкою", True, GREEN)
        screen.blit(start_txt, (WIDTH//2 - start_txt.get_width()//2, 550))
        
        mx, my = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()[0]
        
        for i in range(1, 7):
            r = (i-1) // 3
            c = (i-1) % 3
            x = WIDTH//2 - 150 + c * (bw + gap)
            y = ys + r * (bh + gap)
            if x < mx < x + bw and y < my < y + bh and click:
                if i <= self.unlocked:
                    self.start_level(i)
    
    def draw(self):
        if self.state == "menu":
            self.draw_menu()
            return
        
        if self.current == 1 and LEVEL1_BG:
            screen.blit(LEVEL1_BG, (0, 0))
        elif self.current == 2 and LEVEL2_BG:
            screen.blit(LEVEL2_BG, (0, 0))
        elif self.current == 3 and LEVEL3_BG:
            screen.blit(LEVEL3_BG, (0, 0))
        elif self.current == 4 and LEVEL4_BG:
            screen.blit(LEVEL4_BG, (0, 0))
        elif self.current == 5 and LEVEL5_BG:
            screen.blit(LEVEL5_BG, (0, 0))
        elif self.current == 6 and LEVEL6_BG:
            screen.blit(LEVEL6_BG, (0, 0))
        else:
            screen.fill((30, 25, 45))
        
        for p in self.level.platforms:
            BeautifulPlatform.draw(screen, p.x, p.y, p.width, p.height, self.cam_x)
        
        for item in self.level.items:
            item.draw(screen, self.cam_x)
        
        if self.level.base_rect:
            if self.victory_anim > 0:
                sz = 20 + self.victory_anim
                glow = pygame.Surface((sz*2, sz*2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (0, 255, 0, 100 - self.victory_anim*3), (sz, sz), sz)
                screen.blit(glow, (self.level.base_rect.x - self.cam_x - sz + 25, self.level.base_rect.y - sz + 25))
            screen.blit(BASE_IMG, (self.level.base_rect.x - self.cam_x, self.level.base_rect.y))
            base_txt = small_font.render("БАЗА", True, WHITE)
            screen.blit(base_txt, (self.level.base_rect.x - self.cam_x + 12, self.level.base_rect.y + 18))
        
        self.player.draw(screen, self.cam_x)
        self.draw_hud()
        self.btn.draw(screen)
        
        if self.msg_timer > 0:
            msg_txt = font.render(self.msg, True, YELLOW)
            screen.blit(msg_txt, (WIDTH//2 - msg_txt.get_width()//2, HEIGHT//2 - 80))
            self.msg_timer -= 1
        
        if self.state == "level_complete":
            self.draw_complete()
        elif self.state == "game_over":
            self.draw_game_over()
    
    def draw_hud(self):
        panel = pygame.Surface((WIDTH, 80))
        panel.set_alpha(180)
        panel.fill(BLACK)
        screen.blit(panel, (0, 0))
        
        pygame.draw.rect(screen, GRAY, (20, 15, 200, 18))
        pygame.draw.rect(screen, ORANGE, (20, 15, 200 * (self.player.fuel/100), 18))
        screen.blit(small_font.render(f"ПАЛИВО: {int(self.player.fuel)}%", True, WHITE), (20, 12))
        
        pygame.draw.rect(screen, GRAY, (20, 40, 200, 18))
        pygame.draw.rect(screen, BLUE, (20, 40, 200 * (self.player.oxygen/100), 18))
        screen.blit(small_font.render(f"КИСЕНЬ: {int(self.player.oxygen)}%", True, WHITE), (20, 37))
        
        coin_bg = pygame.Rect(WIDTH - 170, 12, 130, 32)
        pygame.draw.rect(screen, DARK_GRAY, coin_bg, border_radius=8)
        pygame.draw.rect(screen, YELLOW, coin_bg, 2, border_radius=8)
        screen.blit(font.render(f"{self.player.coins}/{self.level.req_coins}", True, YELLOW), (WIDTH - 160, 18))
        screen.blit(font.render(f"РІВЕНЬ {self.current}", True, WHITE), (WIDTH//2 - 60, 20))
        
        if self.storm_active:
            storm_txt = small_font.render("ПИЛОВА БУРЯ", True, RED)
            screen.blit(storm_txt, (WIDTH//2 - 60, 55))
    
    def draw_complete(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        txt = big_font.render("РІВЕНЬ ПРОЙДЕНО", True, GREEN)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 200))
        
        if self.current < 6:
            nxt = font.render(f"ВІДКРИТО РІВЕНЬ {self.current + 1}", True, YELLOW)
            screen.blit(nxt, (WIDTH//2 - nxt.get_width()//2, 300))
            cont = font.render("Натисни ENTER або ПРОБІЛ", True, ORANGE)
        else:
            cont = font.render("ВІТАЮ! ТИ ПРОЙШОВ ВСЮ ГРУ!", True, ORANGE)
        
        screen.blit(cont, (WIDTH//2 - cont.get_width()//2, 450))
    
    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(RED)
        screen.blit(overlay, (0, 0))
        
        txt = big_font.render("GAME OVER", True, WHITE)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 200))
        
        restart = font.render("Натисни R для виходу в меню", True, YELLOW)
        screen.blit(restart, (WIDTH//2 - restart.get_width()//2, 400))
    
    def handle_events(self, event):
        if self.state == "menu":
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            act, val = self.btn.handle_click(event.pos)
            if act == "home":
                self.state = "menu"
        
        if event.type == pygame.MOUSEBUTTONUP:
            self.btn.stop_drag()
        
        if event.type == pygame.MOUSEMOTION:
            self.btn.handle_drag(event.pos)
        
        if self.state == "level_complete" and event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                if self.current < 6:
                    self.start_level(self.current + 1)
                else:
                    self.state = "menu"
        
        if self.state == "game_over" and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.state = "menu"

def main():
    game = Game()
    run = True
    
    while run:
        keys = pygame.key.get_pressed()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
            game.handle_events(e)
        
        game.update(keys)
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
