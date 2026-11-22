import array
import math
import random
import pygame

pygame.init()
pygame.font.init()
try:
  pygame.mixer.pre_init(22050, -16, 1, 512)
  pygame.mixer.init()
except Exception:
  pass

# === ШАБЛОН ЕКРАНА (міняй тут під тест) ===
BASE_W, BASE_H = 960, 540
FLAGS = getattr(pygame, "SCALED", 0) | pygame.FULLSCREEN
try:
  screen = pygame.display.set_mode((BASE_W, BASE_H), FLAGS)
except Exception:
  screen = pygame.display.set_mode((BASE_W, BASE_H))
W, H = BASE_W, BASE_H
# =========================================

pygame.display.set_caption("2D Voxel Shahed")
clock = pygame.time.Clock()

WORLD_W, WORLD_H = 32000, 540
CELL = 10
COLS, ROWS = WORLD_W // CELL, WORLD_H // CELL
GROUND_Y = ROWS - 7
DAY_CYCLE_PERIOD = 100.0

HALF_COLS = COLS // 2
BRIDGE_START_COL = HALF_COLS - 32
BRIDGE_END_COL = HALF_COLS + 32
BRIDGE_DECK_Y = GROUND_Y - 5

font = pygame.font.SysFont(None, 26)
btn_font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 48)

COLORS = {
    1: (92, 70, 48),
    2: (118, 124, 134),
    3: (154, 162, 174),
    4: (58, 62, 70),
    5: (68, 138, 62),
    6: (102, 72, 44),
    7: (56, 122, 54),
    8: (132, 148, 56),
    9: (242, 198, 56),
    10: (66, 70, 78),
    11: (82, 86, 94),
    12: (196, 182, 152),
    13: (42, 92, 148),
    14: (118, 124, 134),
}

BACK_COLORS = {
    1: (48, 36, 24),
    2: (62, 66, 74),
    3: (78, 84, 92),
    4: (34, 37, 42),
    5: (38, 76, 35),
    6: (54, 38, 24),
    7: (30, 66, 29),
    8: (72, 80, 30),
    9: (145, 118, 34),
    10: (38, 40, 46),
    11: (46, 49, 55),
    12: (104, 96, 80),
    13: (24, 52, 88),
    14: (66, 70, 78),
}


def lerp(a, b, t):
  return a + (b - a) * t


def lerp_col(c1, c2, t):
  return (
      int(lerp(c1[0], c2[0], t)),
      int(lerp(c1[1], c2[1], t)),
      int(lerp(c1[2], c2[2], t)),
  )


def get_daylight_state(cycle_t):
  p = (cycle_t % DAY_CYCLE_PERIOD) / DAY_CYCLE_PERIOD
  morning_sky = (118, 162, 208)
  day_sky = (68, 114, 166)
  evening_sky = (168, 92, 74)
  night_sky = (18, 26, 48)

  if p < 0.15:
    t = p / 0.15
    sky = lerp_col(morning_sky, day_sky, t)
    sun_col = lerp_col((255, 210, 140), (255, 236, 165), t)
    cloud_col = lerp_col((245, 226, 210), (238, 244, 250), t)
    light = lerp(0.86, 1.0, t)
  elif p < 0.60:
    t = (p - 0.15) / 0.45
    sky = lerp_col(day_sky, evening_sky, max(0.0, (t - 0.65) / 0.35))
    sun_col = lerp_col(
        (255, 236, 165), (255, 138, 72), max(0.0, (t - 0.65) / 0.35)
    )
    cloud_col = lerp_col(
        (238, 244, 250), (225, 152, 126), max(0.0, (t - 0.65) / 0.35)
    )
    light = lerp(1.0, 0.75, max(0.0, (t - 0.65) / 0.35))
  elif p < 0.80:
    t = (p - 0.60) / 0.20
    sky = lerp_col(evening_sky, night_sky, t)
    sun_col = lerp_col((255, 138, 72), (185, 205, 245), t)
    cloud_col = lerp_col((225, 152, 126), (52, 64, 92), t)
    light = lerp(0.75, 0.44, t)
  else:
    t = (p - 0.80) / 0.20
    sky = lerp_col(night_sky, morning_sky, t)
    sun_col = lerp_col((185, 205, 245), (255, 210, 140), t)
    cloud_col = lerp_col((52, 64, 92), (245, 226, 210), t)
    light = lerp(0.44, 0.86, t)

  ang = p * math.tau - math.pi * 0.5
  sun_x = int(W * 0.5 + math.cos(ang) * (W * 0.38))
  sun_y = int(155 - math.sin(ang) * 115)
  return sky, sun_x, sun_y, sun_col, cloud_col, light


def make_level_engine_sound(dive=False):
  if not pygame.mixer.get_init():
    return None
  try:
    sr = 22050
    dur = 1.0
    n = int(sr * dur)
    buf = array.array("h")
    rng_s = random.Random(818 if dive else 717)
    phase = 0.0
    sub_phase = 0.0
    lp = 0.0
    for i in range(n):
      t = i / sr
      edge = min(1.0, i / 180.0, (n - i) / 180.0)
      if not dive:
        base_freq = 66.0 + 5.0 * math.sin(2.0 * math.pi * 5.0 * t)
        phase += base_freq / sr
        p = phase % 1.0
        saw = 2.0 * p - 1.0
        pulse = 1.0 if p < 0.38 else -1.0
        noise = (rng_s.random() * 2.0 - 1.0) * 0.22
        raw = 0.62 * saw + 0.32 * pulse + noise
        lp = lp + 0.14 * (raw - lp)
        amp = 21500
      else:
        base_freq = 112.0 + 20.0 * math.sin(2.0 * math.pi * 9.0 * t)
        phase += base_freq / sr
        sub_phase += (base_freq * 0.5) / sr
        p = phase % 1.0
        saw = 2.0 * p - 1.0
        square = 1.0 if p < 0.45 else -1.0
        sub = math.sin(2.0 * math.pi * sub_phase) * 0.72
        noise = (rng_s.random() * 2.0 - 1.0) * 0.38
        raw = 0.45 * saw + 0.48 * square + sub + noise
        lp = lp + 0.28 * (raw - lp)
        amp = 27500
      val = int(max(-32767, min(32767, lp * amp * edge)))
      buf.append(val)
    return pygame.mixer.Sound(buffer=buf.tobytes())
  except Exception:
    return None


def make_boom_sound():
  if not pygame.mixer.get_init():
    return None
  try:
    sr = 22050
    dur = 1.55
    n = int(sr * dur)
    buf = array.array("h")
    rng_b = random.Random(909)
    sub_phase = 0.0
    rumble_phase = 0.0
    lp1 = 0.0
    lp2 = 0.0
    for i in range(n):
      t = i / sr
      atk = min(1.0, i / 45.0)
      env = atk * math.exp(-t * 2.5)
      tail_env = atk * math.exp(-t * 1.4)

      sub_freq = (
          38.0
          + 16.0 * math.exp(-t * 4.5)
          + 4.0 * math.sin(2.0 * math.pi * 2.5 * t)
      )
      sub_phase += sub_freq / sr
      sub = math.sin(2.0 * math.pi * sub_phase) * 1.0

      rumble_phase += (25.0 + 4.0 * math.sin(2.0 * math.pi * 1.6 * t)) / sr
      rumble = math.sin(2.0 * math.pi * rumble_phase) * 0.6

      white = rng_b.random() * 2.0 - 1.0
      alpha = max(0.02, 0.14 * math.exp(-t * 2.1))
      lp1 = lp1 + alpha * (white - lp1)
      lp2 = lp2 + (alpha * 0.45) * (lp1 - lp2)

      crackle = 0.0
      if 0.04 < t < 1.15 and rng_b.random() < 0.022:
        crackle = (
            (rng_b.random() * 2.0 - 1.0)
            * 0.75
            * math.exp(-(t - 0.04) * 2.6)
        )

      mix = (sub + rumble) * env + (lp1 * 1.9 + lp2 * 1.5) * tail_env + crackle
      val = int(max(-32767, min(32767, mix * 21500)))
      buf.append(val)
    return pygame.mixer.Sound(buffer=buf.tobytes())
  except Exception:
    return None


def make_siren_sound():
  if not pygame.mixer.get_init():
    return None
  try:
    sr = 22050
    dur = 12.0
    n = int(sr * dur)
    buf = array.array("h")
    p1 = 0.0
    p2 = 0.0
    p3 = 0.0
    lp = 0.0
    for i in range(n):
      t = i / sr
      edge = min(1.0, i / 800.0, (n - i) / 800.0)
      if t < 6.5:
        u = t / 6.5
        curve = u * u * (3.0 - 2.0 * u)
      else:
        u = (t - 6.5) / 5.5
        curve = 1.0 - (u**1.35)
      freq = 185.0 + 275.0 * curve
      p1 += freq / sr
      p2 += (freq * 2.0) / sr
      p3 += (freq * 3.0) / sr
      tone = (
          0.72 * math.sin(2.0 * math.pi * p1)
          + 0.34 * math.sin(2.0 * math.pi * p2)
          + 0.14 * math.sin(2.0 * math.pi * p3)
      )
      lp = lp + 0.09 * (tone - lp)
      dyn_amp = 7500 + 8500 * curve
      val = int(max(-32767, min(32767, lp * dyn_amp * edge)))
      buf.append(val)
    return pygame.mixer.Sound(buffer=buf.tobytes())
  except Exception:
    return None


level_snd = make_level_engine_sound(dive=False)
dive_snd = make_level_engine_sound(dive=True)
boom_snd = make_boom_sound()
siren_snd = make_siren_sound()
active_mode = None
siren_playing = False


def update_flight_sound(active, speed=180.0, vy=0.0):
  global active_mode
  if level_snd is None or dive_snd is None:
    return
  try:
    if not active:
      if active_mode == "level":
        level_snd.stop()
      elif active_mode == "dive":
        dive_snd.stop()
      active_mode = None
      return

    mode = "dive" if vy > 25.0 else "level"
    if mode != active_mode:
      if active_mode == "level":
        level_snd.stop()
      elif active_mode == "dive":
        dive_snd.stop()
      if mode == "level":
        level_snd.play(-1)
      else:
        dive_snd.play(-1)
      active_mode = mode

    if mode == "level":
      vol = max(0.45, min(0.88, 0.55 + abs(speed) / 650.0))
      level_snd.set_volume(vol)
    else:
      dive_factor = min(1.0, max(0.0, (vy - 25.0) / 150.0))
      vol = max(0.70, min(1.0, 0.75 + dive_factor * 0.25))
      dive_snd.set_volume(vol)
  except Exception:
    active_mode = None


def update_siren_sound(active):
  global siren_playing
  if siren_snd is None:
    return
  try:
    if active and not siren_playing:
      siren_snd.set_volume(0.35)
      siren_snd.play(-1)
      siren_playing = True
    elif not active and siren_playing:
      siren_snd.stop()
      siren_playing = False
  except Exception:
    siren_playing = False


def play_boom_sound(radius=32):
  if boom_snd is None:
    return
  try:
    vol = max(0.60, min(1.0, radius / 40.0))
    boom_snd.set_volume(vol)
    boom_snd.play()
  except Exception:
    pass


def is_bridge_span(col):
  return BRIDGE_START_COL <= col <= BRIDGE_END_COL


def add_tree(grid, bx, gy, th=4, cr=2):
  if bx - cr < 2 or bx + cr >= COLS - 2:
    return
  for dx in range(-cr - 1, cr + 2):
    if is_bridge_span(bx + dx):
      return
  tt = max(2, gy - th)
  for y in range(tt, gy):
    if grid[y][bx] == 0:
      grid[y][bx] = 6
  for dy in range(-cr, cr + 1):
    for dx in range(-cr, cr + 1):
      if dx * dx + dy * dy <= cr * cr:
        tx, ty = bx + dx, tt + dy
        if 1 <= ty < gy and 1 <= tx < COLS - 1 and grid[ty][tx] == 0:
          grid[ty][tx] = 7


def add_village_house(grid, x0, gy, w=8, h=4):
  if x0 < 2 or x0 + w >= COLS - 2:
    return
  for x in range(x0 - 1, x0 + w + 2):
    if is_bridge_span(x):
      return
  wall_top = max(4, gy - h)
  roof_h = max(2, w // 3)
  for r in range(roof_h):
    ry = wall_top - roof_h + r
    span_start = x0 + (roof_h - 1 - r)
    span_end = x0 + w - (roof_h - 1 - r)
    if 2 <= ry < gy:
      for x in range(max(2, span_start), min(COLS - 2, span_end)):
        grid[ry][x] = 6 if r == 0 else 11
  for y in range(wall_top, gy):
    for x in range(x0, x0 + w):
      if y == wall_top + 1 and (x - x0) in (2, w - 3):
        grid[y][x] = 3
      else:
        grid[y][x] = 12


def add_field_zone(grid, start_col, end_col, gy):
  x0 = max(2, start_col)
  x1 = min(COLS - 3, end_col)
  if x1 - x0 < 6:
    return
  road_end = min(x1, x0 + 4)
  for x in range(x0, road_end):
    if not is_bridge_span(x):
      grid[gy][x] = 10
  for x in range(road_end, x1):
    if not is_bridge_span(x):
      grid[gy][x] = 8
      if gy - 1 >= 2 and grid[gy - 1][x] == 0:
        grid[gy - 1][x] = 9


def build_long_city_and_stations():
  rng = random.Random(2026)
  grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
  stations = []

  for x in range(COLS):
    if is_bridge_span(x):
      for y in range(GROUND_Y + 2, ROWS):
        grid[y][x] = 13
      grid[BRIDGE_DECK_Y][x] = 14
      if (x - BRIDGE_START_COL) % 16 == 0:
        for py in range(BRIDGE_DECK_Y + 1, ROWS):
          grid[py][x] = 14
    else:
      for y in range(GROUND_Y, ROWS):
        if y == GROUND_Y:
          grid[y][x] = 4
        elif y == GROUND_Y + 1:
          grid[y][x] = 5
        else:
          grid[y][x] = 1

  city_end_col = min(BRIDGE_START_COL - 8, int(HALF_COLS * 0.62))
  xc = 6
  last_b_end = xc
  while xc + 18 < city_end_col:
    bw, bh = rng.randint(12, 18), rng.randint(8, 14)
    ty = max(4, GROUND_Y - bh)
    for y in range(ty, GROUND_Y):
      for x in range(xc, xc + bw):
        if y == ty:
          grid[y][x] = 11
        elif ((y - ty) % 3 == 1 and (x - xc) % 3 == 1):
          grid[y][x] = 3
        else:
          grid[y][x] = 2
    gap = rng.randint(6, 11)
    if gap >= 8 and len(stations) < 12 and rng.random() < 0.55:
      st_x = (xc + bw + gap // 2) * CELL
      st_y = GROUND_Y * CELL
      stations.append([float(st_x), float(st_y), 52.0, 26.0, True])
    tx = xc + bw + rng.randint(2, 4)
    if tx + 4 < city_end_col and rng.random() < 0.65:
      add_tree(grid, tx, GROUND_Y, rng.randint(3, 5), rng.randint(2, 3))
    last_b_end = xc + bw
    xc += bw + gap

  cur = last_b_end + rng.randint(8, 12)
  zone_idx = 0
  while cur + 14 < BRIDGE_START_COL - 6:
    f_len = rng.randint(16, 24)
    add_field_zone(grid, cur, min(BRIDGE_START_COL - 6, cur + f_len), GROUND_Y)
    v_start = cur + f_len + rng.randint(2, 4)
    if zone_idx % 2 == 0 and v_start + 22 < BRIDGE_START_COL - 6:
      for x in range(v_start, min(BRIDGE_START_COL - 6, v_start + 16)):
        grid[GROUND_Y][x] = 10
      hx = v_start + 1
      for _ in range(rng.randint(2, 3)):
        hw = rng.randint(7, 9)
        hh = rng.randint(3, 4)
        add_village_house(grid, hx, GROUND_Y, hw, hh)
        if rng.random() < 0.5 and hx + hw + 3 < BRIDGE_START_COL - 6:
          add_tree(grid, hx + hw + 1, GROUND_Y, 3, 2)
        hx += hw + rng.randint(3, 5)
      cur = hx + rng.randint(3, 6)
    else:
      if (
          cur + f_len + 8 < BRIDGE_START_COL - 6
          and len(stations) < 16
          and rng.random() < 0.35
      ):
        st_x = (cur + f_len + 4) * CELL
        st_y = GROUND_Y * CELL
        stations.append([float(st_x), float(st_y), 52.0, 26.0, True])
      cur += f_len + rng.randint(8, 12)
    zone_idx += 1

  return grid, stations


def is_solid(grid, px, py):
  gx, gy = int(px) // CELL, int(py) // CELL
  if 0 <= gx < COLS and 0 <= gy < ROWS:
    return grid[gy][gx] not in (0, 9, 13)
  return False


def is_solid_for_people(grid, px, py):
  gx, gy = int(px) // CELL, int(py) // CELL
  if 0 <= gx < COLS and 0 <= gy < ROWS:
    val = grid[gy][gx]
    return val not in (0, 2, 3, 6, 7, 9, 11, 12, 13)
  return False


boom_radius = 32
shelters = [
    float(x)
    for x in range(380, WORLD_W - 200, 640)
    if not (BRIDGE_START_COL * CELL - 50 <= x <= BRIDGE_END_COL * CELL + 50)
]
def spawn_people(count=150):
  rng = random.Random(404)
  shirts = [
      (225, 80, 80),
      (75, 155, 230),
      (240, 195, 65),
      (95, 200, 125),
      (205, 115, 215),
  ]
  pants = [(45, 55, 75), (65, 52, 42), (38, 42, 48)]
  hair = [
      (42, 30, 22),
      (98, 66, 38),
      (20, 22, 28),
      (155, 112, 58),
      (62, 44, 34),
  ]
  people = [
      [
          240.0 + i * 95.0,
          float(GROUND_Y * CELL),
          0.0,
          32.0 if i % 2 == 0 else -32.0,
          shirts[i % len(shirts)],
          pants[i % len(pants)],
          float(i),
          0.0,
          0.0,
          hair[i % len(hair)],
      ]
      for i in range(6)
  ]
  for _ in range(count):
    px = rng.uniform(160.0, WORLD_W - 160.0)
    if BRIDGE_START_COL * CELL - 30 <= px <= BRIDGE_END_COL * CELL + 30:
      px = BRIDGE_END_COL * CELL + 120.0
    people.append([
        px,
        float(GROUND_Y * CELL),
        0.0,
        rng.choice([-1.0, 1.0]) * rng.uniform(22.0, 44.0),
        rng.choice(shirts),
        rng.choice(pants),
        rng.uniform(0.0, math.tau),
        0.0,
        0.0,
        rng.choice(hair),
    ])
  return people


def has_line_of_sight(grid, x0, y0, x1, y1):
  dist = math.hypot(x1 - x0, y1 - y0)
  steps = max(1, int(dist // (CELL * 0.9)))
  blocked_cells = 0
  for i in range(1, steps):
    t = i / steps
    px = x0 + (x1 - x0) * t
    py = y0 + (y1 - y0) * t
    if is_solid(grid, px, py):
      blocked_cells += 1
      if blocked_cells > 2 or py > y0 - 8.0:
        return False
  return True


def spawn_map_shooters(count=24):
  rng = random.Random(777)
  shooters = []
  if count <= 1:
    positions = [WORLD_W * 0.5]
  else:
    positions = [
        200.0 + (WORLD_W - 400.0) * i / (count - 1) for i in range(count)
    ]
  for idx, base_x in enumerate(positions):
    gx = max(
        60.0, min(float(WORLD_W - 60.0), base_x + rng.uniform(-90.0, 90.0))
    )
    on_bridge = BRIDGE_START_COL * CELL <= gx <= BRIDGE_END_COL * CELL
    gy = float(BRIDGE_DECK_Y * CELL) if on_bridge else float(GROUND_Y * CELL)
    shooters.append({
        "id": idx,
        "x": gx,
        "y": gy,
        "home_x": gx,
        "vx": rng.choice([-1.0, 1.0]) * 42.0,
        "vy": 0.0,
        "phase": rng.uniform(0.0, math.tau),
        "cd": rng.uniform(0.2, 0.55),
        "burst_left": 0,
        "burst_gap": 0.0,
        "aim_x": gx,
        "aim_y": gy - 90.0,
        "persistent": True,
    })
  return shooters


def spawn_guards_after_strike(cx, count=5):
  rng = random.Random(int(cx) + 77)
  new_guards = []
  for i in range(count):
    gx = max(60.0, min(float(WORLD_W - 60.0), cx + rng.uniform(-650.0, 650.0)))
    on_bridge = BRIDGE_START_COL * CELL <= gx <= BRIDGE_END_COL * CELL
    gy = float(BRIDGE_DECK_Y * CELL) if on_bridge else float(GROUND_Y * CELL)
    new_guards.append({
        "x": gx,
        "y": gy,
        "home_x": gx,
        "vx": rng.choice([-1.0, 1.0]) * 42.0,
        "vy": 0.0,
        "phase": rng.uniform(0.0, math.tau) + i,
        "cd": rng.uniform(0.2, 0.5),
        "burst_left": 0,
        "burst_gap": 0.0,
        "aim_x": gx,
        "aim_y": gy - 80.0,
        "persistent": True,
    })
  return new_guards


def spawn_village_mg_trucks(grid):
  rng = random.Random(9091)
  trucks = []
  x = 10
  while x < COLS - 14:
    if is_bridge_span(x):
      x = BRIDGE_END_COL + 6
      continue
    has_road_or_field = False
    for dx in range(-10, 12):
      if 0 <= x + dx < COLS and grid[GROUND_Y][x + dx] in (8, 9, 10):
        has_road_or_field = True
        break
    if has_road_or_field and grid[GROUND_Y][x] in (4, 5, 8, 10):
      clear_above = all(
          grid[yy][x] == 0 for yy in range(max(2, GROUND_Y - 8), GROUND_Y)
      )
      if clear_above:
        trucks.append({
            "x": float(x * CELL + CELL // 2),
            "y": float(GROUND_Y * CELL),
            "alive": True,
            "cd": rng.uniform(0.6, 1.8),
            "burst_left": 0,
            "burst_gap": 0.0,
            "aim_x": float(x * CELL),
            "aim_y": float(GROUND_Y * CELL - 120.0),
            "gunner_ang": 0.0,
            "gunner_face": 1,
        })
        x += rng.randint(60, 95)
        continue
    x += 8
  return trucks


class VirtualJoystick:

  def __init__(self, cx, cy, radius=58, knob_radius=23):
    self.base_x, self.base_y, self.radius, self.knob_radius = (
        cx,
        cy,
        radius,
        knob_radius,
    )
    self.reset()

  def reset(self):
    self.pointer_id = None
    self.active = False
    self.knob_x, self.knob_y = float(self.base_x), float(self.base_y)
    self.vx = self.vy = 0.0

  def _move(self, px, py):
    dx, dy = px - self.base_x, py - self.base_y
    d = math.hypot(dx, dy)
    if d > self.radius and d > 0:
      dx, dy = dx / d * self.radius, dy / d * self.radius
    self.knob_x, self.knob_y = self.base_x + dx, self.base_y + dy
    self.vx, self.vy = dx / self.radius, dy / self.radius

  def handle_event(self, event):
    if event.type == pygame.FINGERDOWN:
      px, py = event.x * W, event.y * H
      if (
          not self.active
          and math.hypot(px - self.base_x, py - self.base_y)
          <= self.radius + 40
      ):
        self.active, self.pointer_id = True, event.finger_id
        self._move(px, py)
        return True
    elif (
        event.type == pygame.FINGERMOTION
        and self.active
        and event.finger_id == self.pointer_id
    ):
      self._move(event.x * W, event.y * H)
      return True
    elif (
        event.type == pygame.FINGERUP
        and self.active
        and event.finger_id == self.pointer_id
    ):
      self.reset()
      return True
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
      px, py = event.pos
      if (
          not self.active
          and math.hypot(px - self.base_x, py - self.base_y)
          <= self.radius + 30
      ):
        self.active, self.pointer_id = True, "mouse"
        self._move(px, py)
        return True
    elif (
        event.type == pygame.MOUSEMOTION
        and self.active
        and self.pointer_id == "mouse"
    ):
      self._move(event.pos[0], event.pos[1])
      return True
    elif (
        event.type == pygame.MOUSEBUTTONUP
        and event.button == 1
        and self.active
        and self.pointer_id == "mouse"
    ):
      self.reset()
      return True
    return False

  def draw(self, surf):
    pygame.draw.circle(
        surf, (35, 42, 56), (self.base_x, self.base_y), self.radius
    )
    pygame.draw.circle(
        surf, (160, 175, 195), (self.base_x, self.base_y), self.radius, 2
    )
    pygame.draw.circle(
        surf,
        (215, 225, 235),
        (int(self.knob_x), int(self.knob_y)),
        self.knob_radius,
    )
    pygame.draw.circle(
        surf,
        (45, 55, 70),
        (int(self.knob_x), int(self.knob_y)),
        self.knob_radius,
        2,
    )


class Button:

  def __init__(self, rect, label, bg=(55, 65, 85), big=False):
    self.rect = pygame.Rect(rect)
    self.label, self.bg, self.big = label, bg, big

  def hit(self, px, py):
    return self.rect.inflate(18, 18).collidepoint(px, py)

  def draw(self, surf):
    pygame.draw.rect(surf, self.bg, self.rect, border_radius=10)
    pygame.draw.rect(surf, (200, 210, 225), self.rect, 2, border_radius=10)
    f = big_font if self.big else btn_font
    txt = f.render(self.label, True, (245, 248, 252))
    surf.blit(txt, txt.get_rect(center=self.rect.center))


class Shahed:

  def __init__(self):
    self.reset()

  def reset(self):
    self.x, self.y = 140.0, 210.0
    self.vx, self.vy = 180.0, 0.0
    self.facing, self.prop, self.alive = 1, 0.0, True
    self.bullet_hits = 0
    self.engine_smoking = False
    self.engine_slowed = False
    self.engine_hit = False
    self.smoke_timer = 0.0

  def register_bullet_hit(self):
    if not self.alive or self.engine_hit:
      return
    self.bullet_hits += 1
    if self.bullet_hits <= 2:
      self.engine_smoking = True
    elif self.bullet_hits <= 4:
      self.engine_smoking = True
      if not self.engine_slowed:
        self.engine_slowed = True
        self.vx *= 0.72
    else:
      self.engine_smoking = True
      self.engine_slowed = True
      self.engine_hit = True
      self.vx *= 0.65
      self.vy = max(self.vy, 45.0)

  def update(self, dt, keys, joy, dust=None, fires=None):
    if not self.alive:
      return
    if self.engine_hit:
      self.prop = max(0.0, self.prop + 12.0 * dt)
      self.vy = min(340.0, self.vy + 290.0 * dt)
      self.vx *= 1.0 - 0.35 * dt
      self.x = max(24.0, min(WORLD_W - 24.0, self.x + self.vx * dt))
      self.y = max(20.0, min(WORLD_H - 20.0, self.y + self.vy * dt))
      self.smoke_timer += dt
      if dust is not None and self.smoke_timer >= 0.03:
        self.smoke_timer = 0.0
        dust.append([
            self.x - self.facing * 18.0,
            self.y,
            random.uniform(-18, 18),
            random.uniform(-24, -6),
            random.uniform(7, 12),
            0.85,
            0.85,
        ])
        if fires is not None and random.random() < 0.45:
          fires.append([
              self.x - self.facing * 20.0,
              self.y,
              0.0,
              0.0,
              random.uniform(5, 8),
              0.35,
              0.35,
          ])
      return

    diving = self.vy > 25.0
    speed_mult = 0.70 if self.engine_slowed else 1.0
    self.prop += (62.0 if diving else 38.0) * speed_mult * dt
    mx = (
        joy.vx
        + (1.0 if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) else 0.0)
        - (1.0 if (keys[pygame.K_LEFT] or keys[pygame.K_a]) else 0.0)
    )
    my = (
        joy.vy
        + (1.0 if (keys[pygame.K_DOWN] or keys[pygame.K_s]) else 0.0)
        - (1.0 if (keys[pygame.K_UP] or keys[pygame.K_w]) else 0.0)
    )
    mx, my = max(-1.0, min(1.0, mx)), max(-1.0, min(1.0, my))

    if mx < -0.25:
      if self.facing == 1 and self.vx > 35.0:
        tvx = 0.0
      else:
        self.facing = -1
        tvx = mx * 230.0 * speed_mult
    elif mx > 0.25:
      if self.facing == -1 and self.vx < -35.0:
        tvx = 0.0
      else:
        self.facing = 1
        tvx = mx * 240.0 * speed_mult
    else:
      tvx = self.facing * 155.0 * speed_mult

    if my > 0.2:
      tvx *= 1.35

    turn_rate = (
        2.6
        if (
            (mx < -0.25 and self.facing == 1)
            or (mx > 0.25 and self.facing == -1)
        )
        else (7.5 if my > 0.2 else 4.5)
    )
    self.vx += (tvx - self.vx) * turn_rate * dt
    self.vy += (
        (my * 235.0 * speed_mult - self.vy) * (6.5 if my > 0.2 else 4.8) * dt
    )
    self.x = max(24.0, min(WORLD_W - 24.0, self.x + self.vx * dt))
    self.y = max(20.0, min(WORLD_H - 20.0, self.y + self.vy * dt))

    if self.engine_smoking:
      self.smoke_timer += dt
      step_s = 0.05 if self.engine_slowed else 0.09
      if dust is not None and self.smoke_timer >= step_s:
        self.smoke_timer = 0.0
        dust.append([
            self.x - self.facing * 18.0,
            self.y,
            random.uniform(-14, 14),
            random.uniform(-20, -5),
            random.uniform(6, 10),
            0.75,
            0.75,
        ])

  def _tilt(self):
    if self.engine_hit:
      p = 0.85
      return p if self.facing == 1 else -p
    p = max(-0.45, min(0.55, self.vy / 320.0))
    return p if self.facing == 1 else -p

  def hit_point(self):
    a = self._tilt()
    return (
        self.x + self.facing * math.cos(a) * 25,
        self.y + math.sin(a) * 25,
    )

  def _rot(self, sx, sy, lx, ly, ca, sa):
    fx = lx * self.facing
    return (sx + fx * ca - ly * sa, sy + fx * sa + ly * ca)

  def draw(self, surf, cam_x):
    if not self.alive:
      return
    sx, sy, a = self.x - cam_x, self.y, self._tilt()
    ca, sa = math.cos(a), math.sin(a)
    fuselage = [
        self._rot(sx, sy, lx, ly, ca, sa)
        for lx, ly in [
            (25, 0.0),
            (22, -2.6),
            (15, -3.5),
            (-16, -4.4),
            (-22, -7.2),
            (-22, -2.5),
            (-18, 2.2),
            (-18, 4.4),
            (15, 3.5),
            (22, 2.6),
        ]
    ]
    pygame.draw.polygon(surf, (206, 212, 218), fuselage)
    pygame.draw.polygon(surf, (45, 52, 62), fuselage, 2)

    band_pts = [
        self._rot(sx, sy, lx, ly, ca, sa)
        for lx, ly in [(16.5, -3.4), (18.2, -3.2), (18.2, 3.2), (16.5, 3.4)]
    ]
    pygame.draw.polygon(surf, (45, 95, 195), band_pts)

    pod_pts = [
        self._rot(sx, sy, lx, ly, ca, sa)
        for lx, ly in [(4, 3.8), (-4, 3.8), (-5, 5.6), (3, 5.6)]
    ]
    pygame.draw.polygon(surf, (135, 142, 152), pod_pts)

    pygame.draw.rect(
        surf,
        (72, 78, 88),
        pygame.Rect(
            int(self._rot(sx, sy, -24, -2.2, ca, sa)[0]) - 2,
            int(self._rot(sx, sy, -24, -2.2, ca, sa)[1]) - 2,
            4,
            4,
        ),
    )
    sp = 7.5 * abs(math.cos(self.prop)) + 2.0
    p1 = self._rot(sx, sy, -24.5, -sp, ca, sa)
    p2 = self._rot(sx, sy, -24.5, sp, ca, sa)
    pygame.draw.line(surf, (235, 240, 245), p1, p2, 2)
import array
import math
import random
import pygame

pygame.init()
pygame.font.init()
try:
  pygame.mixer.pre_init(22050, -16, 1, 512)
  pygame.mixer.init()
except Exception:
  pass

# === ШАБЛОН ЕКРАНА (міняй тут під тест) ===
BASE_W, BASE_H = 960, 540
FLAGS = getattr(pygame, "SCALED", 0) | pygame.FULLSCREEN
try:
  screen = pygame.display.set_mode((BASE_W, BASE_H), FLAGS)
except Exception:
  screen = pygame.display.set_mode((BASE_W, BASE_H))
W, H = BASE_W, BASE_H
# =========================================

pygame.display.set_caption("2D Voxel Shahed")
clock = pygame.time.Clock()

WORLD_W, WORLD_H = 32000, 540
CELL = 10
COLS, ROWS = WORLD_W // CELL, WORLD_H // CELL
GROUND_Y = ROWS - 7
DAY_CYCLE_PERIOD = 100.0

HALF_COLS = COLS // 2
BRIDGE_START_COL = HALF_COLS - 32
BRIDGE_END_COL = HALF_COLS + 32
BRIDGE_DECK_Y = GROUND_Y - 5

font = pygame.font.SysFont(None, 26)
btn_font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 48)

COLORS = {
    1: (92, 70, 48),
    2: (118, 124, 134),
    3: (154, 162, 174),
    4: (58, 62, 70),
    5: (68, 138, 62),
    6: (102, 72, 44),
    7: (56, 122, 54),
    8: (132, 148, 56),
    9: (242, 198, 56),
    10: (66, 70, 78),
    11: (82, 86, 94),
    12: (196, 182, 152),
    13: (42, 92, 148),
    14: (118, 124, 134),
}

BACK_COLORS = {
    1: (48, 36, 24),
    2: (62, 66, 74),
    3: (78, 84, 92),
    4: (34, 37, 42),
    5: (38, 76, 35),
    6: (54, 38, 24),
    7: (30, 66, 29),
    8: (72, 80, 30),
    9: (145, 118, 34),
    10: (38, 40, 46),
    11: (46, 49, 55),
    12: (104, 96, 80),
    13: (24, 52, 88),
    14: (66, 70, 78),
}


def lerp(a, b, t):
  return a + (b - a) * t


def lerp_col(c1, c2, t):
  return (
      int(lerp(c1[0], c2[0], t)),
      int(lerp(c1[1], c2[1], t)),
      int(lerp(c1[2], c2[2], t)),
  )


def get_daylight_state(cycle_t):
  p = (cycle_t % DAY_CYCLE_PERIOD) / DAY_CYCLE_PERIOD
  morning_sky = (118, 162, 208)
  day_sky = (68, 114, 166)
  evening_sky = (168, 92, 74)
  night_sky = (18, 26, 48)

  if p < 0.15:
    t = p / 0.15
    sky = lerp_col(morning_sky, day_sky, t)
    sun_col = lerp_col((255, 210, 140), (255, 236, 165), t)
    cloud_col = lerp_col((245, 226, 210), (238, 244, 250), t)
    light = lerp(0.86, 1.0, t)
  elif p < 0.60:
    t = (p - 0.15) / 0.45
    sky = lerp_col(day_sky, evening_sky, max(0.0, (t - 0.65) / 0.35))
    sun_col = lerp_col(
        (255, 236, 165), (255, 138, 72), max(0.0, (t - 0.65) / 0.35)
    )
    cloud_col = lerp_col(
        (238, 244, 250), (225, 152, 126), max(0.0, (t - 0.65) / 0.35)
    )
    light = lerp(1.0, 0.75, max(0.0, (t - 0.65) / 0.35))
  elif p < 0.80:
    t = (p - 0.60) / 0.20
    sky = lerp_col(evening_sky, night_sky, t)
    sun_col = lerp_col((255, 138, 72), (185, 205, 245), t)
    cloud_col = lerp_col((225, 152, 126), (52, 64, 92), t)
    light = lerp(0.75, 0.44, t)
  else:
    t = (p - 0.80) / 0.20
    sky = lerp_col(night_sky, morning_sky, t)
    sun_col = lerp_col((185, 205, 245), (255, 210, 140), t)
    cloud_col = lerp_col((52, 64, 92), (245, 226, 210), t)
    light = lerp(0.44, 0.86, t)

  ang = p * math.tau - math.pi * 0.5
  sun_x = int(W * 0.5 + math.cos(ang) * (W * 0.38))
  sun_y = int(155 - math.sin(ang) * 115)
  return sky, sun_x, sun_y, sun_col, cloud_col, light


def make_level_engine_sound(dive=False):
  if not pygame.mixer.get_init():
    return None
  try:
    sr = 22050
    dur = 1.0
    n = int(sr * dur)
    buf = array.array("h")
    rng_s = random.Random(818 if dive else 717)
    phase = 0.0
    sub_phase = 0.0
    lp = 0.0
    for i in range(n):
      t = i / sr
      edge = min(1.0, i / 180.0, (n - i) / 180.0)
      if not dive:
        base_freq = 66.0 + 5.0 * math.sin(2.0 * math.pi * 5.0 * t)
        phase += base_freq / sr
        p = phase % 1.0
        saw = 2.0 * p - 1.0
        pulse = 1.0 if p < 0.38 else -1.0
        noise = (rng_s.random() * 2.0 - 1.0) * 0.22
        raw = 0.62 * saw + 0.32 * pulse + noise
        lp = lp + 0.14 * (raw - lp)
        amp = 21500
      else:
        base_freq = 112.0 + 20.0 * math.sin(2.0 * math.pi * 9.0 * t)
        phase += base_freq / sr
        sub_phase += (base_freq * 0.5) / sr
        p = phase % 1.0
        saw = 2.0 * p - 1.0
        square = 1.0 if p < 0.45 else -1.0
        sub = math.sin(2.0 * math.pi * sub_phase) * 0.72
        noise = (rng_s.random() * 2.0 - 1.0) * 0.38
        raw = 0.45 * saw + 0.48 * square + sub + noise
        lp = lp + 0.28 * (raw - lp)
        amp = 27500
      val = int(max(-32767, min(32767, lp * amp * edge)))
      buf.append(val)
    return pygame.mixer.Sound(buffer=buf.tobytes())
  except Exception:
    return None


def make_boom_sound():
  if not pygame.mixer.get_init():
    return None
  try:
    sr = 22050
    dur = 1.55
    n = int(sr * dur)
    buf = array.array("h")
    rng_b = random.Random(909)
    sub_phase = 0.0
    rumble_phase = 0.0
    lp1 = 0.0
    lp2 = 0.0
    for i in range(n):
      t = i / sr
      atk = min(1.0, i / 45.0)
      env = atk * math.exp(-t * 2.5)
      tail_env = atk * math.exp(-t * 1.4)

      sub_freq = (
          38.0
          + 16.0 * math.exp(-t * 4.5)
          + 4.0 * math.sin(2.0 * math.pi * 2.5 * t)
      )
      sub_phase += sub_freq / sr
      sub = math.sin(2.0 * math.pi * sub_phase) * 1.0

      rumble_phase += (25.0 + 4.0 * math.sin(2.0 * math.pi * 1.6 * t)) / sr
      rumble = math.sin(2.0 * math.pi * rumble_phase) * 0.6

      white = rng_b.random() * 2.0 - 1.0
      alpha = max(0.02, 0.14 * math.exp(-t * 2.1))
      lp1 = lp1 + alpha * (white - lp1)
      lp2 = lp2 + (alpha * 0.45) * (lp1 - lp2)

      crackle = 0.0
      if 0.04 < t < 1.15 and rng_b.random() < 0.022:
        crackle = (
            (rng_b.random() * 2.0 - 1.0)
            * 0.75
            * math.exp(-(t - 0.04) * 2.6)
        )

      mix = (sub + rumble) * env + (lp1 * 1.9 + lp2 * 1.5) * tail_env + crackle
      val = int(max(-32767, min(32767, mix * 21500)))
      buf.append(val)
    return pygame.mixer.Sound(buffer=buf.tobytes())
  except Exception:
    return None


def make_siren_sound():
  if not pygame.mixer.get_init():
    return None
  try:
    sr = 22050
    dur = 12.0
    n = int(sr * dur)
    buf = array.array("h")
    p1 = 0.0
    p2 = 0.0
    p3 = 0.0
    lp = 0.0
    for i in range(n):
      t = i / sr
      edge = min(1.0, i / 800.0, (n - i) / 800.0)
      if t < 6.5:
        u = t / 6.5
        curve = u * u * (3.0 - 2.0 * u)
      else:
        u = (t - 6.5) / 5.5
        curve = 1.0 - (u**1.35)
      freq = 185.0 + 275.0 * curve
      p1 += freq / sr
      p2 += (freq * 2.0) / sr
      p3 += (freq * 3.0) / sr
      tone = (
          0.72 * math.sin(2.0 * math.pi * p1)
          + 0.34 * math.sin(2.0 * math.pi * p2)
          + 0.14 * math.sin(2.0 * math.pi * p3)
      )
      lp = lp + 0.09 * (tone - lp)
      dyn_amp = 7500 + 8500 * curve
      val = int(max(-32767, min(32767, lp * dyn_amp * edge)))
      buf.append(val)
    return pygame.mixer.Sound(buffer=buf.tobytes())
  except Exception:
    return None


level_snd = make_level_engine_sound(dive=False)
dive_snd = make_level_engine_sound(dive=True)
boom_snd = make_boom_sound()
siren_snd = make_siren_sound()
active_mode = None
siren_playing = False


def update_flight_sound(active, speed=180.0, vy=0.0):
  global active_mode
  if level_snd is None or dive_snd is None:
    return
  try:
    if not active:
      if active_mode == "level":
        level_snd.stop()
      elif active_mode == "dive":
        dive_snd.stop()
      active_mode = None
      return

    mode = "dive" if vy > 25.0 else "level"
    if mode != active_mode:
      if active_mode == "level":
        level_snd.stop()
      elif active_mode == "dive":
        dive_snd.stop()
      if mode == "level":
        level_snd.play(-1)
      else:
        dive_snd.play(-1)
      active_mode = mode

    if mode == "level":
      vol = max(0.45, min(0.88, 0.55 + abs(speed) / 650.0))
      level_snd.set_volume(vol)
    else:
      dive_factor = min(1.0, max(0.0, (vy - 25.0) / 150.0))
      vol = max(0.70, min(1.0, 0.75 + dive_factor * 0.25))
      dive_snd.set_volume(vol)
  except Exception:
    active_mode = None


def update_siren_sound(active):
  global siren_playing
  if siren_snd is None:
    return
  try:
    if active and not siren_playing:
      siren_snd.set_volume(0.35)
      siren_snd.play(-1)
      siren_playing = True
    elif not active and siren_playing:
      siren_snd.stop()
      siren_playing = False
  except Exception:
    siren_playing = False


def play_boom_sound(radius=32):
  if boom_snd is None:
    return
  try:
    vol = max(0.60, min(1.0, radius / 40.0))
    boom_snd.set_volume(vol)
    boom_snd.play()
  except Exception:
    pass


def is_bridge_span(col):
  return BRIDGE_START_COL <= col <= BRIDGE_END_COL


def add_tree(grid, bx, gy, th=4, cr=2):
  if bx - cr < 2 or bx + cr >= COLS - 2:
    return
  for dx in range(-cr - 1, cr + 2):
    if is_bridge_span(bx + dx):
      return
  tt = max(2, gy - th)
  for y in range(tt, gy):
    if grid[y][bx] == 0:
      grid[y][bx] = 6
  for dy in range(-cr, cr + 1):
    for dx in range(-cr, cr + 1):
      if dx * dx + dy * dy <= cr * cr:
        tx, ty = bx + dx, tt + dy
        if 1 <= ty < gy and 1 <= tx < COLS - 1 and grid[ty][tx] == 0:
          grid[ty][tx] = 7


def add_village_house(grid, x0, gy, w=8, h=4):
  if x0 < 2 or x0 + w >= COLS - 2:
    return
  for x in range(x0 - 1, x0 + w + 2):
    if is_bridge_span(x):
      return
  wall_top = max(4, gy - h)
  roof_h = max(2, w // 3)
  for r in range(roof_h):
    ry = wall_top - roof_h + r
    span_start = x0 + (roof_h - 1 - r)
    span_end = x0 + w - (roof_h - 1 - r)
    if 2 <= ry < gy:
      for x in range(max(2, span_start), min(COLS - 2, span_end)):
        grid[ry][x] = 6 if r == 0 else 11
  for y in range(wall_top, gy):
    for x in range(x0, x0 + w):
      if y == wall_top + 1 and (x - x0) in (2, w - 3):
        grid[y][x] = 3
      else:
        grid[y][x] = 12


def add_field_zone(grid, start_col, end_col, gy):
  x0 = max(2, start_col)
  x1 = min(COLS - 3, end_col)
  if x1 - x0 < 6:
    return
  road_end = min(x1, x0 + 4)
  for x in range(x0, road_end):
    if not is_bridge_span(x):
      grid[gy][x] = 10
  for x in range(road_end, x1):
    if not is_bridge_span(x):
      grid[gy][x] = 8
      if gy - 1 >= 2 and grid[gy - 1][x] == 0:
        grid[gy - 1][x] = 9


def build_long_city_and_stations():
  rng = random.Random(2026)
  grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
  stations = []

  for x in range(COLS):
    if is_bridge_span(x):
      for y in range(GROUND_Y + 2, ROWS):
        grid[y][x] = 13
      grid[BRIDGE_DECK_Y][x] = 14
      if (x - BRIDGE_START_COL) % 16 == 0:
        for py in range(BRIDGE_DECK_Y + 1, ROWS):
          grid[py][x] = 14
    else:
      for y in range(GROUND_Y, ROWS):
        if y == GROUND_Y:
          grid[y][x] = 4
        elif y == GROUND_Y + 1:
          grid[y][x] = 5
        else:
          grid[y][x] = 1

  city_end_col = min(BRIDGE_START_COL - 8, int(HALF_COLS * 0.62))
  xc = 6
  last_b_end = xc
  while xc + 18 < city_end_col:
    bw, bh = rng.randint(12, 18), rng.randint(8, 14)
    ty = max(4, GROUND_Y - bh)
    for y in range(ty, GROUND_Y):
      for x in range(xc, xc + bw):
        if y == ty:
          grid[y][x] = 11
        elif ((y - ty) % 3 == 1 and (x - xc) % 3 == 1):
          grid[y][x] = 3
        else:
          grid[y][x] = 2
    gap = rng.randint(6, 11)
    if gap >= 8 and len(stations) < 12 and rng.random() < 0.55:
      st_x = (xc + bw + gap // 2) * CELL
      st_y = GROUND_Y * CELL
      stations.append([float(st_x), float(st_y), 52.0, 26.0, True])
    tx = xc + bw + rng.randint(2, 4)
    if tx + 4 < city_end_col and rng.random() < 0.65:
      add_tree(grid, tx, GROUND_Y, rng.randint(3, 5), rng.randint(2, 3))
    last_b_end = xc + bw
    xc += bw + gap

  cur = last_b_end + rng.randint(8, 12)
  zone_idx = 0
  while cur + 14 < BRIDGE_START_COL - 6:
    f_len = rng.randint(16, 24)
    add_field_zone(grid, cur, min(BRIDGE_START_COL - 6, cur + f_len), GROUND_Y)
    v_start = cur + f_len + rng.randint(2, 4)
    if zone_idx % 2 == 0 and v_start + 22 < BRIDGE_START_COL - 6:
      for x in range(v_start, min(BRIDGE_START_COL - 6, v_start + 16)):
        grid[GROUND_Y][x] = 10
      hx = v_start + 1
      for _ in range(rng.randint(2, 3)):
        hw = rng.randint(7, 9)
        hh = rng.randint(3, 4)
        add_village_house(grid, hx, GROUND_Y, hw, hh)
        if rng.random() < 0.5 and hx + hw + 3 < BRIDGE_START_COL - 6:
          add_tree(grid, hx + hw + 1, GROUND_Y, 3, 2)
        hx += hw + rng.randint(3, 5)
      cur = hx + rng.randint(3, 6)
    else:
      if (
          cur + f_len + 8 < BRIDGE_START_COL - 6
          and len(stations) < 16
          and rng.random() < 0.35
      ):
        st_x = (cur + f_len + 4) * CELL
        st_y = GROUND_Y * CELL
        stations.append([float(st_x), float(st_y), 52.0, 26.0, True])
      cur += f_len + rng.randint(8, 12)
    zone_idx += 1

  return grid, stations


def is_solid(grid, px, py):
  gx, gy = int(px) // CELL, int(py) // CELL
  if 0 <= gx < COLS and 0 <= gy < ROWS:
    return grid[gy][gx] not in (0, 9, 13)
  return False


def is_solid_for_people(grid, px, py):
  gx, gy = int(px) // CELL, int(py) // CELL
  if 0 <= gx < COLS and 0 <= gy < ROWS:
    val = grid[gy][gx]
    return val not in (0, 2, 3, 6, 7, 9, 11, 12, 13)
  return False


boom_radius = 32
shelters = [
    float(x)
    for x in range(380, WORLD_W - 200, 640)
    if not (BRIDGE_START_COL * CELL - 50 <= x <= BRIDGE_END_COL * CELL + 50)
]
def spawn_people(count=150):
  rng = random.Random(404)
  shirts = [
      (225, 80, 80),
      (75, 155, 230),
      (240, 195, 65),
      (95, 200, 125),
      (205, 115, 215),
  ]
  pants = [(45, 55, 75), (65, 52, 42), (38, 42, 48)]
  hair = [
      (42, 30, 22),
      (98, 66, 38),
      (20, 22, 28),
      (155, 112, 58),
      (62, 44, 34),
  ]
  people = [
      [
          240.0 + i * 95.0,
          float(GROUND_Y * CELL),
          0.0,
          32.0 if i % 2 == 0 else -32.0,
          shirts[i % len(shirts)],
          pants[i % len(pants)],
          float(i),
          0.0,
          0.0,
          hair[i % len(hair)],
      ]
      for i in range(6)
  ]
  for _ in range(count):
    px = rng.uniform(160.0, WORLD_W - 160.0)
    if BRIDGE_START_COL * CELL - 30 <= px <= BRIDGE_END_COL * CELL + 30:
      px = BRIDGE_END_COL * CELL + 120.0
    people.append([
        px,
        float(GROUND_Y * CELL),
        0.0,
        rng.choice([-1.0, 1.0]) * rng.uniform(22.0, 44.0),
        rng.choice(shirts),
        rng.choice(pants),
        rng.uniform(0.0, math.tau),
        0.0,
        0.0,
        rng.choice(hair),
    ])
  return people


def has_line_of_sight(grid, x0, y0, x1, y1):
  dist = math.hypot(x1 - x0, y1 - y0)
  steps = max(1, int(dist // (CELL * 0.9)))
  blocked_cells = 0
  for i in range(1, steps):
    t = i / steps
    px = x0 + (x1 - x0) * t
    py = y0 + (y1 - y0) * t
    if is_solid(grid, px, py):
      blocked_cells += 1
      if blocked_cells > 2 or py > y0 - 8.0:
        return False
  return True


def spawn_map_shooters(count=24):
  rng = random.Random(777)
  shooters = []
  if count <= 1:
    positions = [WORLD_W * 0.5]
  else:
    positions = [
        200.0 + (WORLD_W - 400.0) * i / (count - 1) for i in range(count)
    ]
  for idx, base_x in enumerate(positions):
    gx = max(
        60.0, min(float(WORLD_W - 60.0), base_x + rng.uniform(-90.0, 90.0))
    )
    on_bridge = BRIDGE_START_COL * CELL <= gx <= BRIDGE_END_COL * CELL
    gy = float(BRIDGE_DECK_Y * CELL) if on_bridge else float(GROUND_Y * CELL)
    shooters.append({
        "id": idx,
        "x": gx,
        "y": gy,
        "home_x": gx,
        "vx": rng.choice([-1.0, 1.0]) * 42.0,
        "vy": 0.0,
        "phase": rng.uniform(0.0, math.tau),
        "cd": rng.uniform(0.2, 0.55),
        "burst_left": 0,
        "burst_gap": 0.0,
        "aim_x": gx,
        "aim_y": gy - 90.0,
        "persistent": True,
    })
  return shooters


def spawn_guards_after_strike(cx, count=5):
  rng = random.Random(int(cx) + 77)
  new_guards = []
  for i in range(count):
    gx = max(60.0, min(float(WORLD_W - 60.0), cx + rng.uniform(-650.0, 650.0)))
    on_bridge = BRIDGE_START_COL * CELL <= gx <= BRIDGE_END_COL * CELL
    gy = float(BRIDGE_DECK_Y * CELL) if on_bridge else float(GROUND_Y * CELL)
    new_guards.append({
        "x": gx,
        "y": gy,
        "home_x": gx,
        "vx": rng.choice([-1.0, 1.0]) * 42.0,
        "vy": 0.0,
        "phase": rng.uniform(0.0, math.tau) + i,
        "cd": rng.uniform(0.2, 0.5),
        "burst_left": 0,
        "burst_gap": 0.0,
        "aim_x": gx,
        "aim_y": gy - 80.0,
        "persistent": True,
    })
  return new_guards


def spawn_village_mg_trucks(grid):
  rng = random.Random(9091)
  trucks = []
  x = 10
  while x < COLS - 14:
    if is_bridge_span(x):
      x = BRIDGE_END_COL + 6
      continue
    has_road_or_field = False
    for dx in range(-10, 12):
      if 0 <= x + dx < COLS and grid[GROUND_Y][x + dx] in (8, 9, 10):
        has_road_or_field = True
        break
    if has_road_or_field and grid[GROUND_Y][x] in (4, 5, 8, 10):
      clear_above = all(
          grid[yy][x] == 0 for yy in range(max(2, GROUND_Y - 8), GROUND_Y)
      )
      if clear_above:
        trucks.append({
            "x": float(x * CELL + CELL // 2),
            "y": float(GROUND_Y * CELL),
            "alive": True,
            "cd": rng.uniform(0.6, 1.8),
            "burst_left": 0,
            "burst_gap": 0.0,
            "aim_x": float(x * CELL),
            "aim_y": float(GROUND_Y * CELL - 120.0),
            "gunner_ang": 0.0,
            "gunner_face": 1,
        })
        x += rng.randint(60, 95)
        continue
    x += 8
  return trucks


class VirtualJoystick:

  def __init__(self, cx, cy, radius=58, knob_radius=23):
    self.base_x, self.base_y, self.radius, self.knob_radius = (
        cx,
        cy,
        radius,
        knob_radius,
    )
    self.reset()

  def reset(self):
    self.pointer_id = None
    self.active = False
    self.knob_x, self.knob_y = float(self.base_x), float(self.base_y)
    self.vx = self.vy = 0.0

  def _move(self, px, py):
    dx, dy = px - self.base_x, py - self.base_y
    d = math.hypot(dx, dy)
    if d > self.radius and d > 0:
      dx, dy = dx / d * self.radius, dy / d * self.radius
    self.knob_x, self.knob_y = self.base_x + dx, self.base_y + dy
    self.vx, self.vy = dx / self.radius, dy / self.radius

  def handle_event(self, event):
    if event.type == pygame.FINGERDOWN:
      px, py = event.x * W, event.y * H
      if (
          not self.active
          and math.hypot(px - self.base_x, py - self.base_y)
          <= self.radius + 40
      ):
        self.active, self.pointer_id = True, event.finger_id
        self._move(px, py)
        return True
    elif (
        event.type == pygame.FINGERMOTION
        and self.active
        and event.finger_id == self.pointer_id
    ):
      self._move(event.x * W, event.y * H)
      return True
    elif (
        event.type == pygame.FINGERUP
        and self.active
        and event.finger_id == self.pointer_id
    ):
      self.reset()
      return True
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
      px, py = event.pos
      if (
          not self.active
          and math.hypot(px - self.base_x, py - self.base_y)
          <= self.radius + 30
      ):
        self.active, self.pointer_id = True, "mouse"
        self._move(px, py)
        return True
    elif (
        event.type == pygame.MOUSEMOTION
        and self.active
        and self.pointer_id == "mouse"
    ):
      self._move(event.pos[0], event.pos[1])
      return True
    elif (
        event.type == pygame.MOUSEBUTTONUP
        and event.button == 1
        and self.active
        and self.pointer_id == "mouse"
    ):
      self.reset()
      return True
    return False

  def draw(self, surf):
    pygame.draw.circle(
        surf, (35, 42, 56), (self.base_x, self.base_y), self.radius
    )
    pygame.draw.circle(
        surf, (160, 175, 195), (self.base_x, self.base_y), self.radius, 2
    )
    pygame.draw.circle(
        surf,
        (215, 225, 235),
        (int(self.knob_x), int(self.knob_y)),
        self.knob_radius,
    )
    pygame.draw.circle(
        surf,
        (45, 55, 70),
        (int(self.knob_x), int(self.knob_y)),
        self.knob_radius,
        2,
    )


class Button:

  def __init__(self, rect, label, bg=(55, 65, 85), big=False):
    self.rect = pygame.Rect(rect)
    self.label, self.bg, self.big = label, bg, big

  def hit(self, px, py):
    return self.rect.inflate(18, 18).collidepoint(px, py)

  def draw(self, surf):
    pygame.draw.rect(surf, self.bg, self.rect, border_radius=10)
    pygame.draw.rect(surf, (200, 210, 225), self.rect, 2, border_radius=10)
    f = big_font if self.big else btn_font
    txt = f.render(self.label, True, (245, 248, 252))
    surf.blit(txt, txt.get_rect(center=self.rect.center))


class Shahed:

  def __init__(self):
    self.reset()

  def reset(self):
    self.x, self.y = 140.0, 210.0
    self.vx, self.vy = 180.0, 0.0
    self.facing, self.prop, self.alive = 1, 0.0, True
    self.bullet_hits = 0
    self.engine_smoking = False
    self.engine_slowed = False
    self.engine_hit = False
    self.smoke_timer = 0.0

  def register_bullet_hit(self):
    if not self.alive or self.engine_hit:
      return
    self.bullet_hits += 1
    if self.bullet_hits <= 2:
      self.engine_smoking = True
    elif self.bullet_hits <= 4:
      self.engine_smoking = True
      if not self.engine_slowed:
        self.engine_slowed = True
        self.vx *= 0.72
    else:
      self.engine_smoking = True
      self.engine_slowed = True
      self.engine_hit = True
      self.vx *= 0.65
      self.vy = max(self.vy, 45.0)

  def update(self, dt, keys, joy, dust=None, fires=None):
    if not self.alive:
      return
    if self.engine_hit:
      self.prop = max(0.0, self.prop + 12.0 * dt)
      self.vy = min(340.0, self.vy + 290.0 * dt)
      self.vx *= 1.0 - 0.35 * dt
      self.x = max(24.0, min(WORLD_W - 24.0, self.x + self.vx * dt))
      self.y = max(20.0, min(WORLD_H - 20.0, self.y + self.vy * dt))
      self.smoke_timer += dt
      if dust is not None and self.smoke_timer >= 0.03:
        self.smoke_timer = 0.0
        dust.append([
            self.x - self.facing * 18.0,
            self.y,
            random.uniform(-18, 18),
            random.uniform(-24, -6),
            random.uniform(7, 12),
            0.85,
            0.85,
        ])
        if fires is not None and random.random() < 0.45:
          fires.append([
              self.x - self.facing * 20.0,
              self.y,
              0.0,
              0.0,
              random.uniform(5, 8),
              0.35,
              0.35,
          ])
      return

    diving = self.vy > 25.0
    speed_mult = 0.70 if self.engine_slowed else 1.0
    self.prop += (62.0 if diving else 38.0) * speed_mult * dt
    mx = (
        joy.vx
        + (1.0 if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) else 0.0)
        - (1.0 if (keys[pygame.K_LEFT] or keys[pygame.K_a]) else 0.0)
    )
    my = (
        joy.vy
        + (1.0 if (keys[pygame.K_DOWN] or keys[pygame.K_s]) else 0.0)
        - (1.0 if (keys[pygame.K_UP] or keys[pygame.K_w]) else 0.0)
    )
    mx, my = max(-1.0, min(1.0, mx)), max(-1.0, min(1.0, my))

    if mx < -0.25:
      if self.facing == 1 and self.vx > 35.0:
        tvx = 0.0
      else:
        self.facing = -1
        tvx = mx * 230.0 * speed_mult
    elif mx > 0.25:
      if self.facing == -1 and self.vx < -35.0:
        tvx = 0.0
      else:
        self.facing = 1
        tvx = mx * 240.0 * speed_mult
    else:
      tvx = self.facing * 155.0 * speed_mult

    if my > 0.2:
      tvx *= 1.35

    turn_rate = (
        2.6
        if (
            (mx < -0.25 and self.facing == 1)
            or (mx > 0.25 and self.facing == -1)
        )
        else (7.5 if my > 0.2 else 4.5)
    )
    self.vx += (tvx - self.vx) * turn_rate * dt
    self.vy += (
        (my * 235.0 * speed_mult - self.vy) * (6.5 if my > 0.2 else 4.8) * dt
    )
    self.x = max(24.0, min(WORLD_W - 24.0, self.x + self.vx * dt))
    self.y = max(20.0, min(WORLD_H - 20.0, self.y + self.vy * dt))

    if self.engine_smoking:
      self.smoke_timer += dt
      step_s = 0.05 if self.engine_slowed else 0.09
      if dust is not None and self.smoke_timer >= step_s:
        self.smoke_timer = 0.0
        dust.append([
            self.x - self.facing * 18.0,
            self.y,
            random.uniform(-14, 14),
            random.uniform(-20, -5),
            random.uniform(6, 10),
            0.75,
            0.75,
        ])

  def _tilt(self):
    if self.engine_hit:
      p = 0.85
      return p if self.facing == 1 else -p
    p = max(-0.45, min(0.55, self.vy / 320.0))
    return p if self.facing == 1 else -p

  def hit_point(self):
    a = self._tilt()
    return (
        self.x + self.facing * math.cos(a) * 25,
        self.y + math.sin(a) * 25,
    )

  def _rot(self, sx, sy, lx, ly, ca, sa):
    fx = lx * self.facing
    return (sx + fx * ca - ly * sa, sy + fx * sa + ly * ca)

  def draw(self, surf, cam_x):
    if not self.alive:
      return
    sx, sy, a = self.x - cam_x, self.y, self._tilt()
    ca, sa = math.cos(a), math.sin(a)
    fuselage = [
        self._rot(sx, sy, lx, ly, ca, sa)
        for lx, ly in [
            (25, 0.0),
            (22, -2.6),
            (15, -3.5),
            (-16, -4.4),
            (-22, -7.2),
            (-22, -2.5),
            (-18, 2.2),
            (-18, 4.4),
            (15, 3.5),
            (22, 2.6),
        ]
    ]
    pygame.draw.polygon(surf, (206, 212, 218), fuselage)
    pygame.draw.polygon(surf, (45, 52, 62), fuselage, 2)

    band_pts = [
        self._rot(sx, sy, lx, ly, ca, sa)
        for lx, ly in [(16.5, -3.4), (18.2, -3.2), (18.2, 3.2), (16.5, 3.4)]
    ]
    pygame.draw.polygon(surf, (45, 95, 195), band_pts)

    pod_pts = [
        self._rot(sx, sy, lx, ly, ca, sa)
        for lx, ly in [(4, 3.8), (-4, 3.8), (-5, 5.6), (3, 5.6)]
    ]
    pygame.draw.polygon(surf, (135, 142, 152), pod_pts)

    pygame.draw.rect(
        surf,
        (72, 78, 88),
        pygame.Rect(
            int(self._rot(sx, sy, -24, -2.2, ca, sa)[0]) - 2,
            int(self._rot(sx, sy, -24, -2.2, ca, sa)[1]) - 2,
            4,
            4,
        ),
    )
    sp = 7.5 * abs(math.cos(self.prop)) + 2.0
    p1 = self._rot(sx, sy, -24.5, -sp, ca, sa)
    p2 = self._rot(sx, sy, -24.5, sp, ca, sa)
    pygame.draw.line(surf, (235, 240, 245), p1, p2, 2)
def explode(
    grid,
    back_grid,
    back_hp,
    back_char,
    blocks,
    fires,
    dust,
    blood_drops,
    blood_stains,
    shockwaves,
    people,
    stations,
    cx,
    cy,
    radius=32,
    depth=0,
    mg_trucks=None,
):
  play_boom_sound(radius)
  shockwaves.append([float(cx), float(cy), 8.0, float(radius) * 3.5, 1.0, 0.0])
  gx, gy = int(cx) // CELL, int(cy) // CELL
  gr = int(radius * 1.35) // CELL + 2
  floor_lock_y = ROWS - 2
  for y in range(max(0, gy - gr), min(ROWS, gy + gr + 1)):
    for x in range(max(0, gx - gr), min(COLS, gx + gr + 1)):
      if y >= floor_lock_y:
        continue
      dx, dy = (x - gx) * CELL, (y - gy) * CELL
      dist = math.hypot(dx, dy)
      ang = math.atan2(dy, dx)
      jagged = (
          1.0
          + 0.24 * math.sin(ang * 5.0 + gx * 0.7)
          + 0.14 * math.cos(ang * 9.0 - gy * 0.5)
          + random.uniform(-0.18, 0.22)
      )
      val = grid[y][x]
      eff_r = radius * jagged * (1.12 if val in (2, 3, 11, 12) else 1.0)
      if dist <= eff_r:
        if val != 0:
          col = COLORS.get(val, (140, 140, 140))
          grid[y][x] = 0
          if val in (2, 3, 6, 7, 8, 9, 10, 11, 12, 14):
            back_grid[y][x] = val
            back_hp[y][x] = 2
          if dist <= eff_r * 0.78 and random.random() < 0.82:
            back_char[y][x] = 1
          spd = random.uniform(95, 250)
          shards = 2 if val in (2, 3, 11, 12) else 1
          for _ in range(shards):
            a_s = ang + random.uniform(-0.6, 0.6)
            blocks.append([
                x * CELL + 5,
                y * CELL + 5,
                math.cos(a_s) * spd,
                math.sin(a_s) * spd - 90,
                random.choice([4, 5, 6]),
                col,
                random.uniform(0.8, 1.35),
                True,
            ])
          if random.random() < (0.80 if val in (2, 3, 9, 11, 12) else 0.65):
            fl = random.uniform(28.0, 32.0)
            fires.append([
                x * CELL + 5,
                y * CELL + 5,
                0.0,
                0.0,
                random.uniform(10, 15),
                fl,
                fl,
            ])
        elif back_grid[y][x] != 0:
          if random.random() < 0.52:
            bcol = BACK_COLORS.get(back_grid[y][x], (68, 72, 80))
            back_grid[y][x] = 0
            back_hp[y][x] = 0
            back_char[y][x] = 0
            dust.append([
                x * CELL + 5,
                y * CELL + 5,
                random.uniform(-30, 30),
                random.uniform(-40, -12),
                random.uniform(8, 13),
                1.0,
                1.0,
            ])
            if random.random() < 0.50:
              blocks.append([
                  x * CELL + 5,
                  y * CELL + 5,
                  random.uniform(-100, 100),
                  random.uniform(-125, -35),
                  4,
                  bcol,
                  random.uniform(0.45, 0.85),
                  False,
              ])
      elif (
          val in (2, 3, 11, 12)
          and dist <= radius * 1.55
          and y <= gy
          and random.random() < 0.26
      ):
        col = COLORS.get(val, (118, 124, 134))
        grid[y][x] = 0
        back_grid[y][x] = val
        back_hp[y][x] = 2
        blocks.append([
            x * CELL + 5,
            y * CELL + 5,
            random.uniform(-35, 35),
            random.uniform(10, 55),
            random.choice([4, 5]),
            col,
            random.uniform(0.85, 1.35),
            False,
        ])

  if mg_trucks:
    for trk in mg_trucks:
      if (
          trk["alive"]
          and math.hypot(trk["x"] - cx, (trk["y"] - 10.0) - cy) <= radius * 0.65
      ):
        for _ in range(8):
          ang, spd = random.uniform(-math.pi, 0.0), random.uniform(50, 140)
          blocks.append([
              trk["x"],
              trk["y"] - 8.0,
              math.cos(ang) * spd,
              math.sin(ang) * spd - 55,
              4,
              random.choice([(75, 92, 56), (45, 52, 42)]),
              random.uniform(0.6, 1.0),
              False,
          ])

  kept = []
  for p in people:
    dist = math.hypot(p[0] - cx, p[1] - cy)
    if dist <= radius + 12:
      blood_stains.append([
          p[0] + random.uniform(-8, 8),
          p[1],
          random.uniform(5, 11),
          random.choice([(145, 18, 22), (175, 24, 28)]),
      ])
      for _ in range(14):
        ang, spd = random.uniform(-math.pi * 0.9, -math.pi * 0.1), random.uniform(
            55, 195
        )
        blood_drops.append([
            p[0],
            p[1] - 10,
            math.cos(ang) * spd,
            math.sin(ang) * spd - 45,
            random.uniform(2, 4),
            random.uniform(0.8, 1.5),
            random.choice([(185, 24, 28), (140, 16, 20)]),
        ])
      for _ in range(2):
        ang, spd = random.uniform(0, math.tau), random.uniform(60, 170)
        blocks.append([
            p[0],
            p[1] - 6,
            math.cos(ang) * spd,
            math.sin(ang) * spd - 70,
            5,
            p[4],
            random.uniform(0.6, 1.0),
            False,
        ])
    else:
      if dist <= radius + 310:
        p[7] = 8.0
        p[8] = 0.0
      kept.append(p)
  people[:] = kept

  for _ in range(20):
    dl, ang, spd = (
        random.uniform(1.2, 2.2),
        random.uniform(0, math.tau),
        random.uniform(24, 130),
    )
    dust.append([
        cx + random.uniform(-14, 14),
        cy + random.uniform(-12, 12),
        math.cos(ang) * spd,
        math.sin(ang) * spd - 28,
        random.uniform(11, 18),
        dl,
        dl,
    ])
  for _ in range(20):
    fl = random.uniform(28.0, 32.0)
    fires.append([
        cx + random.uniform(-16, 16),
        cy + random.uniform(-12, 12),
        0.0,
        0.0,
        random.uniform(10, 15),
        fl,
        fl,
    ])

  if depth < 4:
    for st in stations:
      if not st[4]:
        continue
      st_cx, st_cy = st[0], st[1] - st[3] * 0.5
      if math.hypot(st_cx - cx, st_cy - cy) <= radius + st[2] * 0.7:
        st[4] = False
        for _ in range(24):
          ang, spd = random.uniform(-math.pi, 0.0), random.uniform(70, 240)
          blocks.append([
              st[0] + random.uniform(-22, 22),
              st[1] - random.uniform(2, 20),
              math.cos(ang) * spd,
              math.sin(ang) * spd - 80,
              5,
              random.choice(
                  [(235, 195, 45), (205, 55, 55), (210, 215, 225)]
              ),
              random.uniform(0.8, 1.4),
              True,
          ])
        for _ in range(28):
          fl = random.uniform(28.0, 32.0)
          fires.append([
              st[0] + random.uniform(-26, 26),
              st[1] - random.uniform(0, 14),
              random.uniform(-15, 15),
              random.uniform(-20, 0),
              random.uniform(11, 17),
              fl,
              fl,
          ])
        explode(
            grid,
            back_grid,
            back_hp,
            back_char,
            blocks,
            fires,
            dust,
            blood_drops,
            blood_stains,
            shockwaves,
            people,
            stations,
            st[0],
            st[1] - 6.0,
            radius=int(boom_radius * 1.5),
            depth=depth + 1,
            mg_trucks=mg_trucks,
        )


def rebuild_world():
  global first_strike_done
  first_strike_done = False
  ng, nst = build_long_city_and_stations()
  for y in range(ROWS):
    grid[y][:] = ng[y]
    back_grid[y][:] = [0] * COLS
    back_hp[y][:] = [0] * COLS
    back_char[y][:] = [0] * COLS
  stations[:] = nst
  mg_trucks[:] = spawn_village_mg_trucks(grid)
  guards[:] = spawn_map_shooters(count=24)
  tracers.clear()
  shahed.reset()
  blocks.clear()
  fires.clear()
  dust.clear()
  blood_drops.clear()
  blood_stains.clear()
  shockwaves.clear()
  people[:] = spawn_people()


grid, stations = build_long_city_and_stations()
back_grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
back_hp = [[0 for _ in range(COLS)] for _ in range(ROWS)]
back_char = [[0 for _ in range(COLS)] for _ in range(ROWS)]
mg_trucks = spawn_village_mg_trucks(grid)
shahed = Shahed()
joystick = VirtualJoystick(cx=105, cy=H - 105)
blocks, fires, dust, blood_drops, blood_stains, shockwaves = [], [], [], [], [], []
guards = spawn_map_shooters(count=24)
tracers = []
first_strike_done = False
people = spawn_people()
in_menu = True
console_active = False
console_input = ""
console_log = "Команди: help, reset, rebuild, boom, speed 200, rad 50"
day_time = 0.0

btn_play = Button(
    (W // 2 - 110, H // 2 - 32, 220, 64), "ПЛЕЙ", bg=(45, 120, 80), big=True
)
btn_new_map = Button((18, 18, 145, 42), "НОВА КАРТА", bg=(45, 75, 120))
btn_respawn = Button((W - 148, 18, 130, 42), "РЕСПАВН", bg=(45, 95, 145))
clouds = [
    [220.0 + i * 560.0, 75.0 + (i % 3) * 18.0, 14.0 + (i % 3)]
    for i in range(55)
]


def trigger_strike(sx, sy):
  global first_strike_done
  explode(
      grid,
      back_grid,
      back_hp,
      back_char,
      blocks,
      fires,
      dust,
      blood_drops,
      blood_stains,
      shockwaves,
      people,
      stations,
      sx,
      sy,
      int(boom_radius * 1.5),
      mg_trucks=mg_trucks,
  )
  if not first_strike_done:
    first_strike_done = True
  if len(guards) < 32:
    guards.extend(spawn_guards_after_strike(sx, count=5))
running = True
while running:
  dt = min(clock.tick(60) / 1000.0, 0.05)
  day_time += dt

  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    tap = (
        (event.x * W, event.y * H)
        if event.type == pygame.FINGERDOWN
        else (
            event.pos
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            else None
        )
    )

    if in_menu:
      if (
          event.type == pygame.KEYDOWN
          and event.key in (pygame.K_RETURN, pygame.K_SPACE)
      ) or (tap and btn_play.hit(*tap)):
        in_menu = False
      continue

    if console_active and event.type == pygame.KEYDOWN:
      if event.key in (pygame.K_F1, pygame.K_BACKQUOTE, pygame.K_ESCAPE):
        console_active = False
      elif event.key == pygame.K_RETURN:
        parts = console_input.strip().lower().split()
        if parts:
          cmd = parts[0]
          if cmd == "help":
            console_log = "reset | rebuild | boom | speed 200 | rad 50"
          elif cmd == "reset":
            shahed.reset()
            console_log = "Шахеда респавнуто"
          elif cmd == "rebuild":
            rebuild_world()
            console_log = "Місто відбудовано"
          elif cmd == "boom" and shahed.alive:
            trigger_strike(shahed.x, shahed.y)
            shahed.alive = False
            update_flight_sound(False)
            update_siren_sound(False)
            console_log = f"Вибух! Радіус: {boom_radius}"
          elif cmd == "speed" and len(parts) > 1:
            try:
              val = max(80.0, min(320.0, float(parts[1])))
              shahed.vx = (1 if shahed.facing >= 0 else -1) * val
              console_log = f"Швидкість: {int(val)}"
            except ValueError:
              console_log = "Помилка числа"
          elif cmd == "rad" and len(parts) > 1:
            try:
              boom_radius = max(14, min(120, int(float(parts[1]))))
              console_log = f"Радіус: {boom_radius}"
            except ValueError:
              console_log = "Помилка числа"
          else:
            console_log = f"Невідома команда: {cmd}"
        console_input = ""
      elif event.key == pygame.K_BACKSPACE:
        console_input = console_input[:-1]
      elif event.unicode and event.unicode.isprintable():
        console_input += event.unicode
    elif not console_active and event.type == pygame.KEYDOWN:
      if event.key in (pygame.K_F1, pygame.K_BACKQUOTE):
        console_active = True
      elif event.key == pygame.K_r:
        shahed.reset()
      elif event.key == pygame.K_SPACE and shahed.alive:
        trigger_strike(shahed.x, shahed.y)
        shahed.alive = False
        update_flight_sound(False)
        update_siren_sound(False)

    if tap:
      if btn_respawn.hit(*tap):
        shahed.reset()
        continue
      if btn_new_map.hit(*tap):
        rebuild_world()
        continue

    if not console_active:
      joystick.handle_event(event)

  for c in clouds:
    c[0] += 14.0 * dt
    if c[0] - 80 > WORLD_W:
      c[0] = -80.0

  if not in_menu:
    if not console_active:
      shahed.update(
          dt, pygame.key.get_pressed(), joystick, dust=dust, fires=fires
      )
    else:
      joystick.reset()
    if shahed.alive:
      hx, hy = shahed.hit_point()
      if is_solid(grid, hx, hy) or is_solid(grid, shahed.x, shahed.y):
        trigger_strike(hx, hy)
        shahed.alive = False
        update_flight_sound(False)
        update_siren_sound(False)

    update_flight_sound(
        shahed.alive and not console_active and not shahed.engine_hit,
        shahed.vx,
        shahed.vy,
    )
    update_siren_sound(shahed.alive)

    for g in guards:
      g["phase"] += 7.5 * dt
      muzzle_x = g["x"] + (8.0 if shahed.x >= g["x"] else -8.0)
      muzzle_y = g["y"] - 22.0
      can_shoot = False
      if shahed.alive:
        dist_g = math.hypot(shahed.x - g["x"], shahed.y - (g["y"] - 20.0))
        if dist_g <= 720.0 and has_line_of_sight(
            grid, muzzle_x, muzzle_y, shahed.x, shahed.y
        ):
          can_shoot = True
          spd_b = 620.0
          lead_t = min(0.26, dist_g / spd_b)
          pred_x = shahed.x + shahed.vx * lead_t
          pred_y = shahed.y + shahed.vy * lead_t
          g["aim_x"] += (pred_x - g["aim_x"]) * min(1.0, 8.5 * dt)
          g["aim_y"] += (pred_y - g["aim_y"]) * min(1.0, 8.5 * dt)
          if g["burst_left"] > 0:
            g["burst_gap"] -= dt
            if g["burst_gap"] <= 0.0:
              g["burst_left"] -= 1
              g["burst_gap"] = 0.11
              tx = g["aim_x"] + random.uniform(-14.0, 14.0)
              ty = g["aim_y"] + random.uniform(-14.0, 14.0)
              ang_s = math.atan2(ty - muzzle_y, tx - muzzle_x)
              tracers.append({
                  "x": muzzle_x,
                  "y": muzzle_y,
                  "vx": math.cos(ang_s) * spd_b,
                  "vy": math.sin(ang_s) * spd_b,
                  "life": 1.25,
              })
              if g["burst_left"] == 0:
                g["cd"] = random.uniform(0.55, 0.95)
          else:
            g["cd"] -= dt
            if g["cd"] <= 0.0:
              g["burst_left"] = random.randint(2, 4)
              g["burst_gap"] = 0.0
      if not can_shoot:
        g["burst_left"] = 0
        ngx = g["x"] + g["vx"] * dt
        on_bridge_g = BRIDGE_START_COL * CELL <= ngx <= BRIDGE_END_COL * CELL
        target_y = (
            float(BRIDGE_DECK_Y * CELL)
            if on_bridge_g
            else float(GROUND_Y * CELL)
        )
        g["y"] += (target_y - g["y"]) * min(1.0, 10.0 * dt)
        if (
            ngx < 30.0
            or ngx > WORLD_W - 30.0
            or abs(ngx - g.get("home_x", ngx)) > 360.0
            or is_solid_for_people(grid, ngx, g["y"] - 4.0)
        ):
          g["vx"] = -g["vx"]
        else:
          g["x"] = ngx

    for trk in mg_trucks:
      if not trk["alive"] or not shahed.alive:
        trk["burst_left"] = 0
        continue
      mx = trk["x"] + (12.0 if shahed.x >= trk["x"] else -12.0)
      my = trk["y"] - 18.0
      dist_t = math.hypot(shahed.x - trk["x"], shahed.y - my)
      if dist_t <= 780.0 and has_line_of_sight(
          grid, mx, my, shahed.x, shahed.y
      ):
        spd_m = 660.0
        lead_t = min(0.26, dist_t / spd_m)
        pred_x = shahed.x + shahed.vx * lead_t
        pred_y = shahed.y + shahed.vy * lead_t
        trk["aim_x"] += (pred_x - trk["aim_x"]) * min(1.0, 10.5 * dt)
        trk["aim_y"] += (pred_y - trk["aim_y"]) * min(1.0, 10.5 * dt)
        tur_x = trk["x"] - 10 if shahed.x >= trk["x"] else trk["x"] + 10
        tur_y = trk["y"] - 17
        desired_ang = math.atan2(trk["aim_y"] - tur_y, trk["aim_x"] - tur_x)
        diff_a = (
            desired_ang - trk.get("gunner_ang", desired_ang) + math.pi
        ) % math.tau - math.pi
        trk["gunner_ang"] = trk.get("gunner_ang", desired_ang) + diff_a * min(
            1.0, 10.5 * dt
        )
        trk["gunner_face"] = 1 if trk["aim_x"] >= trk["x"] else -1
        if trk["burst_left"] > 0:
          trk["burst_gap"] -= dt
          if trk["burst_gap"] <= 0.0:
            trk["burst_left"] -= 1
            trk["burst_gap"] = 0.095
            tx = trk["aim_x"] + random.uniform(-12.0, 12.0)
            ty = trk["aim_y"] + random.uniform(-12.0, 12.0)
            ang_m = math.atan2(ty - tur_y, tx - tur_x)
            tracers.append({
                "x": tur_x + math.cos(ang_m) * 14.0,
                "y": tur_y + math.sin(ang_m) * 14.0,
                "vx": math.cos(ang_m) * spd_m,
                "vy": math.sin(ang_m) * spd_m,
                "life": 1.3,
            })
            if trk["burst_left"] == 0:
              trk["cd"] = random.uniform(0.85, 1.55)
        else:
          trk["cd"] -= dt
          if trk["cd"] <= 0.0:
            trk["burst_left"] = random.randint(3, 5)
            trk["burst_gap"] = 0.0

    next_tracers = []
    for tr in tracers:
      tr["life"] -= dt
      if tr["life"] <= 0.0:
        continue
      ntr_x = tr["x"] + tr["vx"] * dt
      ntr_y = tr["y"] + tr["vy"] * dt
      if is_solid(grid, ntr_x, ntr_y):
        dust.append([
            ntr_x,
            ntr_y,
            random.uniform(-15, 15),
            random.uniform(-20, -5),
            5.0,
            0.35,
            0.35,
        ])
        continue
      if (
          shahed.alive
          and math.hypot(ntr_x - shahed.x, ntr_y - shahed.y) <= 25.0
      ):
        shahed.register_bullet_hit()
        for _ in range(5):
          dust.append([
              shahed.x,
              shahed.y,
              random.uniform(-35, 35),
              random.uniform(-35, 25),
              random.uniform(6, 10),
              0.65,
              0.65,
          ])
        continue
      tr["x"], tr["y"] = ntr_x, ntr_y
      next_tracers.append(tr)
    tracers = next_tracers

    for p in people:
      if p[8] > 0.0:
        p[8] = max(0.0, p[8] - dt)
        continue

      px, py, pvy, pvx, psc, ppc, pph, panic_t, hide_t, phair = p
      if shahed.alive and math.hypot(shahed.x - px, shahed.y - py) <= 310.0:
        panic_t = max(panic_t, 5.0)

      if panic_t > 0.0:
        panic_t = max(0.0, panic_t - dt)
        nearest_s = min(shelters, key=lambda sx: abs(sx - px))
        if abs(nearest_s - px) < 15.0:
          p[7], p[8] = 0.0, 5.5
          continue
        spd = 122.0
        pvx = spd if nearest_s > px else -spd
      elif abs(pvx) > 45.0:
        pvx = (1.0 if pvx >= 0 else -1.0) * 32.0

      pph += abs(pvx) * 0.25 * dt
      pvy += 420.0 * dt
      ny = py + pvy * dt
      if is_solid_for_people(grid, px, ny + 1.0):
        py, pvy = float((int(ny + 1.0) // CELL) * CELL), 0.0
      else:
        py = ny

      nx = px + pvx * dt
      if nx < 20.0:
        pvx = abs(pvx)
        nx = 20.0
      elif nx > WORLD_W - 20.0:
        pvx = -abs(pvx)
        nx = WORLD_W - 20.0
      elif is_solid_for_people(grid, nx, py - 4.0):
        climbed = False
        for step_up in (1, 2):
          up_y = py - step_up * CELL
          if not is_solid_for_people(
              grid, nx, up_y - 4.0
          ) and not is_solid_for_people(grid, px, up_y - 16.0):
            py = up_y
            pvy = 0.0
            climbed = True
            break
        if not climbed:
          pvx = -pvx
          nx = max(20.0, min(WORLD_W - 20.0, px + pvx * dt))
      p[0], p[1], p[2], p[3], p[6], p[7] = nx, py, pvy, pvx, pph, panic_t
  else:
    update_flight_sound(False)
    update_siren_sound(False)

  lead = W * 0.35 if shahed.facing >= 0 else W * 0.65
  cam_x = max(0.0, min(float(WORLD_W - W), shahed.x - lead))

  next_b = []
  for b in blocks:
    bx, by, bvx, bvy, bsize, bcol, blife, ign = b
    blife -= dt
    if blife <= 0:
      continue
    bvy += 420.0 * dt
    nbx, nby, landed = bx + bvx * dt, by + bvy * dt, False
    if is_solid(grid, nbx, by):
      bvx, nbx, landed = -bvx * 0.45, bx, True
    if is_solid(grid, nbx, nby):
      bvy, bvx, nby, landed = -bvy * 0.4, bvx * 0.75, by, True
    if landed and ign and random.random() < 0.65:
      fl = random.uniform(28.0, 32.0)
      fires.append([nbx, nby - 2, 0.0, 0.0, random.uniform(9, 14), fl, fl])
      ign = False
    next_b.append([nbx, nby, bvx, bvy, bsize, bcol, blife, ign])
  blocks = next_b

  next_blood = []
  for bd in blood_drops:
    bx, by, bvx, bvy, br, blife, bcol = bd
    blife -= dt
    if blife <= 0:
      continue
    bvy += 440.0 * dt
    nbx, nby = bx + bvx * dt, by + bvy * dt
    if is_solid(grid, nbx, nby):
      if len(blood_stains) < 400:
        blood_stains.append([nbx, nby, br + 1.5, bcol])
      continue
    next_blood.append([nbx, nby, bvx * 0.99, bvy, br, blife, bcol])
  blood_drops = next_blood

  next_sw = []
  for sw in shockwaves:
    swx, swy, swr, swmax, swlife, prev_r = sw
    swlife -= dt * 2.5
    if swlife <= 0.0:
      continue
    new_r = min(swmax, swr + (swmax - 8.0) * (dt * 3.2))
    gx0 = max(0, int(swx - new_r) // CELL)
    gx1 = min(COLS - 1, int(swx + new_r) // CELL)
    gy0 = max(0, int(swy - new_r) // CELL)
    gy1 = min(ROWS - 1, int(swy + new_r) // CELL)
    for wy in range(gy0, gy1 + 1):
      for wx in range(gx0, gx1 + 1):
        if grid[wy][wx] == 3 and random.random() < 0.65:
          d_cell = math.hypot(wx * CELL + 5 - swx, wy * CELL + 5 - swy)
          if prev_r <= d_cell <= new_r:
            grid[wy][wx] = 0
            back_grid[wy][wx] = 3
            back_hp[wy][wx] = 2
            blocks.append([
                wx * CELL + 5,
                wy * CELL + 5,
                random.uniform(-130, 130),
                random.uniform(-135, -30),
                4,
                COLORS[3],
                random.uniform(0.55, 0.95),
                False,
            ])
            dust.append([
                wx * CELL + 5,
                wy * CELL + 5,
                random.uniform(-25, 25),
                random.uniform(-25, -8),
                random.uniform(7, 11),
                0.75,
                0.75,
            ])
    if random.random() < 0.50:
      ang = random.uniform(0.0, math.tau)
      px_w = swx + math.cos(ang) * new_r
      py_w = swy + math.sin(ang) * new_r
      if is_solid(grid, px_w, py_w):
        dust.append([
            px_w,
            py_w - 2.0,
            math.cos(ang) * 35.0,
            -25.0,
            random.uniform(7.0, 12.0),
            0.75,
            0.75,
        ])
    next_sw.append([swx, swy, new_r, swmax, swlife, new_r])
  shockwaves = next_sw

  dust = [
      [
          d[0] + d[2] * dt,
          d[1] + d[3] * dt,
          d[2] * 0.96,
          d[3] * 0.96 - 10.0 * dt,
          d[4] + 6.0 * dt,
          d[5] - dt,
          d[6],
      ]
      for d in dust
      if d[5] - dt > 0
  ]
  fires = [
      [f[0], f[1], f[2], f[3], f[4], f[5] - dt, f[6]]
      for f in fires
      if f[5] - dt > 0
  ]

  sky_col, sun_x, sun_y, sun_col, cloud_col, light = get_daylight_state(
      day_time
  )
  screen.fill(sky_col)
  halo_col = lerp_col(sky_col, sun_col, 0.35)
  pygame.draw.circle(screen, halo_col, (sun_x, sun_y), 52)
  pygame.draw.circle(screen, sun_col, (sun_x, sun_y), 35)
  pygame.draw.circle(
      screen, lerp_col(sun_col, (255, 255, 245), 0.5), (sun_x, sun_y), 22
  )

  cloud_shade = lerp_col(cloud_col, (35, 42, 58), 0.25)
  for cx_w, cy_w, rb in clouds:
    px_c = int(cx_w - cam_x * 0.35)
    if -100 <= px_c <= W + 100:
      cy_i, r_i = int(cy_w), int(rb)
      pygame.draw.circle(screen, cloud_shade, (px_c, cy_i + 3), r_i)
      pygame.draw.circle(screen, cloud_col, (px_c, cy_i), r_i)
      pygame.draw.circle(
          screen, cloud_col, (px_c - r_i, cy_i + 4), int(rb * 0.75)
      )
      pygame.draw.circle(
          screen, cloud_col, (px_c + r_i, cy_i + 3), int(rb * 0.8)
      )

  for y in range(ROWS):
    sy = y * CELL
    for x in range(
        max(0, int(cam_x) // CELL), min(COLS, int(cam_x + W) // CELL + 2)
    ):
      sx = x * CELL - int(cam_x)
      bval = back_grid[y][x]
      if bval != 0:
        bc = lerp_col((12, 14, 20), BACK_COLORS[bval], light)
        if back_char[y][x]:
          bc = (max(14, bc[0] - 24), max(14, bc[1] - 24), max(14, bc[2] - 24))
        pygame.draw.rect(screen, bc, (sx, sy, CELL, CELL))
      val = grid[y][x]
      if val != 0:
        fc = lerp_col((14, 18, 28), COLORS[val], light)
        if val == 3 and light < 0.72:
          lit_seed = ((x * 73856093) ^ (y * 19349663)) & 255
          if lit_seed < 145:
            glow_t = min(1.0, (0.72 - light) / 0.28)
            fc = lerp_col(fc, (255, 214, 118), glow_t)
        if val != 9:
          pygame.draw.rect(screen, fc, (sx, sy, CELL, CELL))
        if val == 2:
          pygame.draw.rect(
              screen,
              lerp_col((10, 12, 18), (104, 110, 120), light),
              (sx, sy + CELL - 2, CELL, 2),
          )
        elif val == 11:
          pygame.draw.rect(
              screen,
              lerp_col((16, 18, 22), (68, 72, 80), light),
              (sx, sy + CELL - 3, CELL, 3),
          )
          if x % 2 == 0:
            pygame.draw.line(
                screen,
                lerp_col((20, 22, 26), (96, 100, 108), light),
                (sx + 2, sy + 2),
                (sx + CELL - 2, sy + 2),
                1,
            )
        elif val == 12:
          pygame.draw.rect(
              screen,
              lerp_col((32, 30, 24), (172, 158, 128), light),
              (sx, sy + CELL - 2, CELL, 2),
          )
        elif val == 4 and (x % 4 in (0, 1)) and y == GROUND_Y:
          pygame.draw.rect(
              screen,
              lerp_col((45, 42, 32), (225, 215, 165), light),
              (sx, sy + 4, CELL, 2),
          )
        elif val == 5 and x % 3 == 0:
          g_tip = lerp_col((20, 35, 18), (92, 168, 72), light)
          pygame.draw.line(screen, g_tip, (sx + 2, sy), (sx + 1, sy - 4), 2)
          pygame.draw.line(screen, g_tip, (sx + 6, sy), (sx + 8, sy - 3), 2)
        elif val == 9:
          sway = int(2.5 * math.sin(day_time * 3.2 + x * 0.55))
          stalk = lerp_col((68, 54, 16), (242, 198, 56), light)
          ear_col = lerp_col((92, 72, 20), (255, 224, 92), light)
          pygame.draw.line(
              screen, stalk, (sx + 3, sy + CELL), (sx + 3 + sway, sy + 1), 2
          )
          pygame.draw.line(
              screen, stalk, (sx + 7, sy + CELL), (sx + 7 + sway, sy + 2), 2
          )
          pygame.draw.ellipse(screen, ear_col, (sx + 1 + sway, sy, 5, 6))
          pygame.draw.ellipse(screen, ear_col, (sx + 5 + sway, sy + 1, 5, 5))
        elif val == 10 and (x % 3 == 0):
          pygame.draw.rect(
              screen,
              lerp_col((55, 50, 30), (245, 220, 120), light),
              (sx + 1, sy + 4, CELL - 2, 2),
          )
        elif val == 14:
          pygame.draw.rect(
              screen,
              lerp_col((22, 26, 34), (145, 152, 164), light),
              (sx, sy, CELL, 2),
          )
  for trk in mg_trucks:
    sx = int(trk["x"] - cam_x)
    if -52 <= sx <= W + 52:
      sy = int(trk["y"])
      g_face = trk.get("gunner_face", 1 if shahed.x >= trk["x"] else -1)
      facing_right = g_face == 1
      body_col = lerp_col((22, 26, 32), (228, 232, 238), light)
      cab_shade = lerp_col((16, 20, 26), (185, 192, 202), light)
      glass_col = lerp_col((24, 40, 62), (95, 145, 195), light)
      tire_col = lerp_col((10, 10, 12), (26, 28, 32), light)
      rim_col = lerp_col((45, 48, 54), (165, 172, 182), light)
      camo_col = lerp_col((18, 28, 18), (74, 96, 58), light)
      skin_col = lerp_col((55, 42, 34), (235, 195, 165), light)
      gun_col = lerp_col((18, 20, 24), (58, 62, 70), light)

      pygame.draw.rect(
          screen, cab_shade, (sx - 20, sy - 11, 18, 7), border_radius=2
      )
      pygame.draw.rect(
          screen, body_col, (sx - 2, sy - 17, 13, 13), border_radius=2
      )
      pygame.draw.rect(
          screen, body_col, (sx + 11, sy - 12, 9, 8), border_radius=2
      )
      pygame.draw.rect(
          screen, glass_col, (sx + 1, sy - 15, 8, 5), border_radius=1
      )
      pygame.draw.line(
          screen, cab_shade, (sx - 20, sy - 14), (sx - 20, sy - 10), 3
      )

      for wx_off in (-12, 11):
        pygame.draw.circle(screen, tire_col, (sx + wx_off, sy - 3), 5)
        pygame.draw.circle(screen, rim_col, (sx + wx_off, sy - 3), 2)

      tur_x = sx - 10 if facing_right else sx - 8
      tur_y = sy - 11
      pygame.draw.line(screen, gun_col, (tur_x, tur_y), (tur_x, tur_y - 6), 3)

      g_x = sx - 15 if facing_right else sx - 3
      g_sway = (
          int(2.0 * math.sin(day_time * 10.0)) if trk["burst_left"] > 0 else 0
      )
      pygame.draw.line(
          screen, camo_col, (g_x, sy - 11), (g_x + g_sway, sy - 18), 3
      )
      pygame.draw.rect(
          screen,
          camo_col,
          (g_x - 3 + g_sway, sy - 23, 6, 7),
          border_radius=2,
      )
      pygame.draw.circle(screen, skin_col, (g_x + g_sway, sy - 26), 3)
      pygame.draw.arc(
          screen, camo_col, (g_x - 3 + g_sway, sy - 29, 6, 5), 0.0, math.pi, 2
      )

      ang_m = trk.get(
          "gunner_ang",
          math.atan2(trk["aim_y"] - (tur_y - 6), trk["aim_x"] - tur_x),
      )
      mx1, my1 = tur_x, tur_y - 6
      mx2 = mx1 + int(math.cos(ang_m) * 15)
      my2 = my1 + int(math.sin(ang_m) * 15)
      pygame.draw.line(screen, gun_col, (mx1, my1), (mx2, my2), 3)
      if trk["burst_left"] > 0:
        pygame.draw.circle(screen, (255, 225, 110), (mx2, my2), 5)
        pygame.draw.circle(screen, (255, 250, 210), (mx2, my2), 2)

  for st in stations:
    sx = int(st[0] - cam_x)
    sy = int(st[1])
    sw_px, sh_px = int(st[2]), int(st[3])
    if -sw_px <= sx <= W + sw_px:
      if st[4]:
        roof_col = lerp_col((35, 45, 70), (225, 185, 45), light)
        trim_col = lerp_col((55, 18, 18), (195, 45, 45), light)
        pump_col = lerp_col((40, 42, 48), (235, 238, 245), light)
        pygame.draw.rect(
            screen, pump_col, (sx - 16, sy - 14, 8, 14), border_radius=2
        )
        pygame.draw.rect(
            screen, pump_col, (sx + 8, sy - 14, 8, 14), border_radius=2
        )
        pygame.draw.rect(screen, trim_col, (sx - 14, sy - 20, 4, 20))
        pygame.draw.rect(screen, trim_col, (sx + 10, sy - 20, 4, 20))
        pygame.draw.rect(
            screen,
            roof_col,
            (sx - sw_px // 2, sy - sh_px, sw_px, 7),
            border_radius=3,
        )
        pygame.draw.rect(
            screen,
            trim_col,
            (sx - sw_px // 2, sy - sh_px, sw_px, 7),
            2,
            border_radius=3,
        )
      else:
        ruin_col = lerp_col((14, 14, 16), (52, 48, 46), light)
        pygame.draw.rect(
            screen, ruin_col, (sx - 18, sy - 6, 36, 6), border_radius=2
        )

  sy_ground = int(GROUND_Y * CELL)
  conc = lerp_col((28, 30, 36), (125, 130, 138), light)
  conc_dark = lerp_col((16, 18, 22), (72, 76, 84), light)
  pit_col = lerp_col((8, 10, 14), (24, 28, 36), light)
  for sx_w in shelters:
    sx = int(sx_w - cam_x)
    if -45 <= sx <= W + 45:
      pygame.draw.rect(screen, pit_col, (sx - 10, sy_ground, 20, 16))
      pygame.draw.rect(screen, conc_dark, (sx - 12, sy_ground, 24, 17), 2)
      for st in range(3):
        pygame.draw.rect(
            screen,
            conc,
            (sx - 8 + st * 2, sy_ground + 2 + st * 4, 16 - st * 4, 2),
        )
      pygame.draw.rect(screen, conc_dark, (sx - 14, sy_ground - 14, 28, 14))
      pygame.draw.rect(screen, conc, (sx - 16, sy_ground - 17, 32, 4))
      pygame.draw.rect(
          screen, (38, 88, 155), (sx - 7, sy_ground - 12, 14, 9), border_radius=2
      )
      pygame.draw.line(
          screen, (235, 245, 255), (sx, sy_ground - 10), (sx, sy_ground - 5), 2
      )
      pygame.draw.line(
          screen,
          (235, 245, 255),
          (sx - 3, sy_ground - 7.5),
          (sx + 3, sy_ground - 7.5),
          2,
      )

  for bs in blood_stains:
    bsx = int(bs[0] - cam_x)
    if -20 <= bsx <= W + 20:
      pygame.draw.ellipse(
          screen,
          lerp_col((30, 6, 8), bs[3], light),
          (bsx - int(bs[2]), int(bs[1]) - 2, int(bs[2] * 2), 4),
      )

  for p in people:
    if p[8] > 0.0:
      continue
    sx = int(p[0] - cam_x)
    if -24 <= sx <= W + 24:
      sy = int(p[1])
      sw = int(4.5 * math.sin(p[6]))
      arm_sw = int(3.5 * math.sin(p[6] + math.pi))
      p_col = lerp_col((14, 16, 22), p[5], light)
      s_col = lerp_col((18, 20, 28), p[4], light)
      s_dark = (
          max(10, s_col[0] - 28),
          max(10, s_col[1] - 28),
          max(10, s_col[2] - 28),
      )
      h_col = lerp_col((10, 10, 14), p[9], light)
      skin_col = lerp_col((55, 42, 34), (235, 195, 165), light)

      pygame.draw.line(screen, p_col, (sx - 2, sy - 8), (sx - 2 + sw, sy), 3)
      pygame.draw.line(screen, p_col, (sx + 2, sy - 8), (sx + 2 - sw, sy), 3)
      pygame.draw.rect(screen, (30, 32, 38), (sx - 4 + sw, sy - 2, 4, 2))
      pygame.draw.rect(screen, (30, 32, 38), (sx + 1 - sw, sy - 2, 4, 2))

      pygame.draw.line(screen, s_dark, (sx, sy - 15), (sx + arm_sw, sy - 9), 2)
      pygame.draw.rect(
          screen, s_col, (sx - 4, sy - 17, 8, 9), border_radius=2
      )
      pygame.draw.rect(
          screen, s_dark, (sx + 1, sy - 17, 3, 9), border_radius=1
      )

      pygame.draw.circle(screen, skin_col, (sx, sy - 21), 4)
      pygame.draw.arc(
          screen, h_col, (sx - 4, sy - 25, 8, 6), 0.0, math.pi, 3
      )

  for g in guards:
    sx = int(g["x"] - cam_x)
    if -28 <= sx <= W + 28:
      sy = int(g["y"])
      sw = int(4.5 * math.sin(g["phase"]))
      camo_col = lerp_col((18, 28, 18), (68, 92, 56), light)
      pants_g = lerp_col((14, 18, 14), (42, 52, 38), light)
      gun_col = lerp_col((18, 18, 20), (46, 48, 54), light)
      skin_col = lerp_col((55, 42, 34), (235, 195, 165), light)
      helm_col = lerp_col((16, 24, 16), (56, 76, 46), light)

      pygame.draw.line(screen, pants_g, (sx - 2, sy - 8), (sx - 2 + sw, sy), 3)
      pygame.draw.line(screen, pants_g, (sx + 2, sy - 8), (sx + 2 - sw, sy), 3)
      pygame.draw.rect(
          screen, camo_col, (sx - 4, sy - 17, 8, 9), border_radius=2
      )
      pygame.draw.circle(screen, skin_col, (sx, sy - 21), 4)
      pygame.draw.arc(
          screen, helm_col, (sx - 4, sy - 25, 8, 6), 0.0, math.pi, 3
      )

      dir_x = (
          1.0
          if (shahed.alive and shahed.x >= g["x"])
          else (1.0 if g["vx"] >= 0 else -1.0)
      )
      aim_ang = (
          math.atan2(g["aim_y"] - (sy - 15), g["aim_x"] - sx)
          if shahed.alive
          else (0.0 if dir_x >= 0 else math.pi)
      )
      gx1, gy1 = sx + int(dir_x * 3), sy - 14
      gx2, gy2 = gx1 + int(math.cos(aim_ang) * 11), gy1 + int(
          math.sin(aim_ang) * 11
      )
      pygame.draw.line(screen, gun_col, (gx1, gy1), (gx2, gy2), 3)

  for tr in tracers:
    tx1, ty1 = int(tr["x"] - cam_x), int(tr["y"])
    tx2, ty2 = int(tr["x"] - tr["vx"] * 0.025 - cam_x), int(
        tr["y"] - tr["vy"] * 0.025
    )
    if -40 <= tx1 <= W + 40:
      pygame.draw.line(screen, (255, 225, 90), (tx2, ty2), (tx1, ty1), 2)

  for bd in blood_drops:
    pygame.draw.circle(
        screen,
        lerp_col((30, 6, 8), bd[6], light),
        (int(bd[0] - cam_x), int(bd[1])),
        max(2, int(bd[4])),
    )

  for b in blocks:
    pygame.draw.rect(
        screen,
        lerp_col((16, 18, 24), b[5], light),
        (
            int(b[0] - cam_x) - b[4] // 2,
            int(b[1]) - b[4] // 2,
            b[4],
            b[4],
        ),
    )

  for d in dust:
    ratio = max(0.0, d[5] / max(0.01, d[6]))
    r, sh = max(3, int(d[4] * (1.2 - 0.4 * ratio))), int(145 + 45 * ratio)
    pygame.draw.circle(
        screen,
        lerp_col((32, 36, 44), (sh, sh - 6, sh - 14), light),
        (int(d[0] - cam_x), int(d[1])),
        r,
    )

  for f in fires:
    rem = max(0.0, f[5])
    fade = min(1.0, rem / 6.0)
    if fade <= 0.0:
      continue
    fx, fy = int(f[0] - cam_x), int(f[1])
    r = max(2, int(f[4] * fade * random.uniform(0.88, 1.15)))
    fcol = (
        (255, 230, 95)
        if fade > 0.65
        else ((255, 125, 25) if fade > 0.3 else (205, 55, 18))
    )
    pygame.draw.circle(screen, fcol, (fx, fy), r)

  for sw in shockwaves:
    sw_col = lerp_col(
        (55, 50, 46), (245, 235, 215), max(0.0, min(1.0, sw[4]))
    )
    ring_w = max(1, int(4 * sw[4]))
    pygame.draw.circle(
        screen, sw_col, (int(sw[0] - cam_x), int(sw[1])), max(2, int(sw[2])), ring_w
    )

  if in_menu:
    pygame.draw.rect(
        screen, (20, 30, 48), (W // 2 - 190, 120, 380, 72), border_radius=12
    )
    t = big_font.render("2D VOXEL SHAHED", True, (245, 248, 252))
    screen.blit(t, t.get_rect(center=(W // 2, 156)))
    btn_play.draw(screen)
  else:
    shahed.draw(screen, int(cam_x))
    btn_new_map.draw(screen)
    btn_respawn.draw(screen)
    joystick.draw(screen)
    if console_active:
      pygame.draw.rect(
          screen, (16, 20, 28), (20, 68, W - 40, 88), border_radius=8
      )
      pygame.draw.rect(
          screen, (95, 185, 130), (20, 68, W - 40, 88), 2, border_radius=8
      )
      screen.blit(
          font.render(console_log, True, (185, 220, 195)), (32, 78)
      )
      screen.blit(
          font.render(f"$ {console_input}_", True, (255, 255, 255)), (32, 114)
      )

  pygame.display.flip()

update_flight_sound(False)
update_siren_sound(False)
pygame.quit()
