import pygame
import random
import os
import sys

# 游戏配置
BLOCK_SIZE = 30
COLS = 10  # 300/30
ROWS = 20  # 600/30
FPS = 60

class TetrisGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()  # 初始化音频混音器
        self.error_log = open('error.log', 'a', encoding='utf-8')

        # 保存原始游戏区域尺寸
        self.original_width = 300
        self.original_height = 600
        
        # 初始化窗口和游戏区域
        self.screen = pygame.display.set_mode((self.original_width, self.original_height), pygame.RESIZABLE)
        self.game_area_rect = pygame.Rect(0, 0, self.original_width, self.original_height)
        self.game_surface = pygame.Surface((self.original_width, self.original_height), pygame.SRCALPHA)
        pygame.display.set_caption('马娘消消乐')
        self.clock = pygame.time.Clock()
        
        # 游戏状态
        self.drop_speed = 2.5  # 修改默认下落速度
        self.score = 0
        self.paused = False
        self.running = True
        
        # 加载资源
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        try:
            self.background = pygame.image.load(os.path.join(base_path, 'background.jpg'))
            self.bg_music = pygame.mixer.Sound(os.path.join(base_path, 'bg_music.mp3'))
            self.bg_music.play(-1)  # 添加循环播放
        except Exception as e:
            full_path_bg = os.path.join(base_path, 'background.jpg')
            full_path_music = os.path.join(base_path, 'bg_music.mp3')
            error_msg = f'[INIT ERROR] {e}\n尝试加载文件:\n背景: {full_path_bg}\n音乐: {full_path_music}\n文件存在: {os.path.exists(full_path_bg)}/{os.path.exists(full_path_music)}\n'
            print(error_msg)
            self.error_log.write(error_msg)
            self.running = False
        self.bg_volume = 0.5
        self.music_playing = True  # 新增音乐播放状态
        
        # 方块形状和颜色
        self.SHAPES = [
            [[1,1,1,1]],
            [[1,1],[1,1]],
            [[1,1,1],[0,1,0]],
            [[1,1,1],[1,0,0]],
            [[1,1,1],[0,0,1]],
            [[1,1,0],[0,1,1]],
            [[0,1,1],[1,1,0]],
            [[1,1,1],[1,0,1]]
        ]
        self.COLORS = [
            (255, 0, 0),    # 红色
            (0, 255, 0),    # 绿色
            (0, 0, 255),    # 蓝色
            (255, 255, 0),  # 黄色
            (255, 0, 255),  # 紫色
            (0, 255, 255),  # 青色
            (255, 165, 0)   # 橙色
        ]
        
        self.current_piece = None
        self.current_x = 0
        self.current_y = 0
        # 新增游戏状态管理
        self.game_state = 'start_menu'  # start_menu/playing/paused/settings
        self.volume_rect = pygame.Rect(50, self.game_area_rect.height-30, 200, 20)
        self.continue_btn = pygame.Rect(0, 0, 160, 60)
        self.restart_btn = pygame.Rect(0, 0, 160, 60)
        self.main_menu_btn = pygame.Rect(0, 0, 160, 60)
        self.quit_btn = pygame.Rect(0, 0, 160, 60)
        self.dragging_volume = False
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.font = pygame.font.SysFont('simhei', 24)

    def spawn_new_piece(self):
        if self.game_state != 'playing':
            return
        self.current_piece = random.choice(self.SHAPES)
        self.current_color = random.choice(self.COLORS)
        self.current_x = COLS//2 - len(self.current_piece[0])//2
        self.current_y = 0
        if self.check_collision():
            self.game_state = 'game_over'
            self.current_piece = None

    def update(self):
        if self.game_state != 'playing':
            return
        delta_time = self.clock.get_time() / 1000.0
        if not self.check_collision():
            self.current_y += self.drop_speed * delta_time
        else:
            self.merge_to_grid()
            self.clear_lines()
            self.spawn_new_piece()

    def merge_to_grid(self):
        current_y_int = int(self.current_y)
        # 添加越界保护检查
        game_over_flag = False
        for y, row in enumerate(self.current_piece):
            for x, val in enumerate(row):
                if val:
                    if (current_y_int + y >= ROWS or
                        self.current_x + x < 0 or self.current_x + x >= COLS):
                        game_over_flag = True
        
        if game_over_flag:
            self.game_state = 'game_over'
            return
        
        # 合并到网格时再次检查边界
        for y, row in enumerate(self.current_piece):
            for x, val in enumerate(row):
                if val and 0 <= current_y_int + y < ROWS and 0 <= self.current_x + x < COLS:
                    self.grid[current_y_int + y][self.current_x + x] = self.current_color
                elif val:
                    self.game_state = 'game_over'

    def draw_block(self, x, y):
        # 在game_surface上绘制方块
        pygame.draw.rect(self.game_surface, (30,144,255), 
                        (x*BLOCK_SIZE, y*BLOCK_SIZE, BLOCK_SIZE-1, BLOCK_SIZE-1))

    def game_loop(self):
        try:
            while self.running:
                self.clock.tick(FPS)
                self.handle_events()
                if not self.paused:
                    self.update()
                    self.render()
        except Exception as e:
            error_msg = f'[ERROR] {e}\n当前游戏状态: {self.game_state}\n暂停状态: {self.paused}\n'
            self.error_log.write(error_msg)
            self.error_log.flush()
            pygame.quit()
            sys.exit(1)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # 统一处理所有事件类型
            if self.game_state == 'start_menu':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_start_menu_click(event)
            if self.game_state == 'game_over':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_game_over_click(event)
            elif event.type == pygame.VIDEORESIZE:
                # 计算保持宽高比的缩放
                original_ratio = 300 / 600  # 原始宽高比
                new_ratio = event.w / event.h
                
                if new_ratio > original_ratio:
                    # 以高度为基准缩放
                    scaled_height = event.h
                    scaled_width = int(scaled_height * original_ratio)
                else:
                    # 以宽度为基准缩放
                    scaled_width = event.w
                    scaled_height = int(scaled_width / original_ratio)
                
                # 更新游戏区域尺寸和位置
                self.game_area_rect = pygame.Rect(
                    (event.w - scaled_width) // 2,
                    (event.h - scaled_height) // 2,
                    scaled_width,
                    scaled_height
                )
                self.game_surface = pygame.transform.scale(
                    self.game_surface,
                    (scaled_width, scaled_height)
                )

            if self.game_state == 'playing':
                # 处理暂停按钮点击
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    relative_pos = (mouse_pos[0] - self.game_area_rect.x, mouse_pos[1] - self.game_area_rect.y)
                    if pygame.Rect(self.game_area_rect.width - 80, 10, 70, 30).collidepoint(relative_pos):
                        self.game_state = 'paused'

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.move_piece(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.move_piece(1)
                    elif event.key == pygame.K_UP:
                        self.rotate_piece()
                    elif event.key == pygame.K_DOWN:
                        self.drop_speed = 15.0
                elif event.type == pygame.KEYUP and self.game_state == 'playing':
                    if event.key == pygame.K_DOWN:
                        self.drop_speed = 2.5  # 始终恢复初始速度
            elif self.game_state in ['start_menu', 'paused']:
                self.handle_start_menu_paused_events(event)

            if self.game_state == 'paused':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    relative_pos = (mouse_pos[0] - self.game_area_rect.x, mouse_pos[1] - self.game_area_rect.y)
                    if hasattr(self, 'continue_btn') and self.continue_btn.collidepoint(relative_pos):
                        self.game_state = 'playing'
                    elif hasattr(self, 'restart_btn') and self.restart_btn.collidepoint(relative_pos):
                        self.score = 0
                        self.grid = [[0] * COLS for _ in range(ROWS)]
                        self.game_state = 'playing'
                        self.spawn_new_piece()
                    elif hasattr(self, 'main_menu_btn') and self.main_menu_btn.collidepoint(relative_pos):
                        self.game_state = 'start_menu'
                    elif hasattr(self, 'quit_btn') and self.quit_btn.collidepoint(relative_pos):
                        self.running = False
                    elif hasattr(self, 'volume_btn') and self.volume_btn.collidepoint(relative_pos):
                        self.game_state = 'settings'

    def handle_click_event(self, event, state):
        if state == 'playing':
            mouse_pos = pygame.mouse.get_pos()
            relative_pos = (mouse_pos[0] - self.game_area_rect.x, mouse_pos[1] - self.game_area_rect.y)
            if pygame.Rect(self.game_area_rect.width - 90, 10, 80, 30).collidepoint(relative_pos):
                self.game_state = 'paused'
        elif state == 'start_menu':
            mouse_pos = pygame.mouse.get_pos()
            # 根据游戏区域计算按钮位置
            start_btn = pygame.Rect(self.game_area_rect.centerx - 50, self.game_area_rect.centery - 30, 100, 60)
            # 将屏幕坐标转换为游戏区域内的相对坐标
            relative_pos = (mouse_pos[0] - self.game_area_rect.x, mouse_pos[1] - self.game_area_rect.y)
            if start_btn.collidepoint(relative_pos):
                self.game_state = 'playing'
                self.spawn_new_piece()

    def handle_start_menu_paused_events(self, event):
        self.handle_volume_drag(event)

        # 处理音乐按钮点击
        if event.type == pygame.MOUSEBUTTONDOWN:
            music_btn = pygame.Rect(self.game_area_rect.centerx - 80, self.game_area_rect.centery + 20, 160, 60)
            relative_pos = (event.pos[0] - self.game_area_rect.x, event.pos[1] - self.game_area_rect.y)
            if music_btn.collidepoint(relative_pos):
                self.music_playing = not self.music_playing
                if self.music_playing:
                    self.bg_music.play(-1)
                else:
                    self.bg_music.stop()

    def handle_volume_drag(self, event):
        # 处理音量拖动
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.volume_rect.collidepoint(event.pos):
                self.dragging_volume = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_volume = False

        # 处理音量拖动
        if self.dragging_volume and event.type == pygame.MOUSEMOTION:
            self.bg_volume = max(0, min(1, (event.pos[0]-self.volume_rect.x)/self.volume_rect.width))
            self.bg_music.set_volume(self.bg_volume)

    def handle_game_over_click(self, event):
        # 转换鼠标坐标到游戏区域坐标系
        mouse_pos = pygame.mouse.get_pos()
        relative_x = mouse_pos[0] - self.game_area_rect.x
        relative_y = mouse_pos[1] - self.game_area_rect.y
        
        # 初始化按钮位置（基于游戏区域坐标系）
        btn_width, btn_height = 160, 60
        self.restart_btn = pygame.Rect(
            self.game_area_rect.width//2 - btn_width//2,
            self.game_area_rect.height//2 - 40,
            btn_width,
            btn_height
        )
        self.main_menu_btn = pygame.Rect(
            self.game_area_rect.width//2 - btn_width//2,
            self.game_area_rect.height//2 + 40,
            btn_width,
            btn_height
        )
        
        # 处理按钮点击
        if self.restart_btn.collidepoint(relative_x, relative_y):
            # 重置游戏状态但不重新初始化
            self.bg_music.stop()
            self.score = 0
            self.grid = [[0] * COLS for _ in range(ROWS)]
            self.game_state = 'playing'
            self.spawn_new_piece()
            if self.music_playing:
                self.bg_music.play(-1)
            return True
        elif self.main_menu_btn.collidepoint(relative_x, relative_y):
            self.bg_music.stop()
            self.score = 0
            self.grid = [[0] * COLS for _ in range(ROWS)]
            self.game_state = 'start_menu'
            if self.music_playing:
                self.bg_music.play(-1)
            return True
        return False
    def handle_start_menu_click(self, event):
        mouse_pos = pygame.mouse.get_pos()
        # 根据游戏区域计算按钮位置
        start_btn = pygame.Rect(self.game_area_rect.centerx - 50, self.game_area_rect.centery - 30, 100, 60)
        # 将屏幕坐标转换为游戏区域内的相对坐标
        relative_pos = (mouse_pos[0] - self.game_area_rect.x, mouse_pos[1] - self.game_area_rect.y)
        if start_btn.collidepoint(relative_pos):
            self.game_state = 'playing'
            self.spawn_new_piece()

    def check_collision(self):
        current_y_int = int(self.current_y)
        for y, row in enumerate(self.current_piece):
            for x, val in enumerate(row):
                if val:
                    if (int(self.current_y) + y >= ROWS -1 or
                        self.current_x + x < 0 or self.current_x + x >= COLS or
                        self.grid[current_y_int + y + 1][self.current_x + x]):
                        return True
        return False

    def clear_lines(self):
        lines_cleared = 0
        for y in range(ROWS):
            if all(cell is not None for cell in self.grid[y]):
                del self.grid[y]
                self.grid.insert(0, [None]*COLS)
                lines_cleared += 1
        self.score += lines_cleared * 100

    def render(self):
        # 计算等比例缩放后的背景尺寸
        screen_width, screen_height = self.screen.get_size()
        bg_width, bg_height = self.background.get_size()
        
        # 计算缩放比例
        width_ratio = screen_width / bg_width
        height_ratio = screen_height / bg_height
        scale_ratio = min(width_ratio, height_ratio)
        
        # 生成缩放后的背景
        scaled_bg = pygame.transform.scale(self.background, 
            (int(bg_width * scale_ratio), int(bg_height * scale_ratio)))
        
        # 更新游戏区域位置
        self.game_area_rect.center = (screen_width//2, screen_height//2)
        
        # 绘制纯色背景
        self.screen.fill((0,0,0))
        # 在游戏区域绘制内容
        self.game_surface.fill((0,0,0,0))
        
        # 先绘制背景
        x_offset = (self.game_area_rect.width - scaled_bg.get_width()) // 2
        y_offset = (self.game_area_rect.height - scaled_bg.get_height()) // 2
        self.game_surface.blit(scaled_bg, (x_offset, y_offset))
        
        # 添加半透明遮罩层（调整到背景之后）
        overlay = pygame.Surface((self.game_area_rect.width, self.game_area_rect.height), pygame.SRCALPHA)
        overlay.fill((30, 30, 30, 120))
        self.game_surface.blit(overlay, (0, 0))
        
        # 绘制红色发光边框
        border_surface = pygame.Surface((self.game_area_rect.width, self.game_area_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(border_surface, (255,0,0,200), (0,0,self.game_area_rect.width,self.game_area_rect.height), 8)
        self.game_surface.blit(border_surface, (0,0))

        # 绘制已固定的方块（使用更醒目的颜色）
        for y in range(ROWS):
            for x in range(COLS):
                if self.grid[y][x]:
                    pygame.draw.rect(self.game_surface, self.grid[y][x],
                                   (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE-2, BLOCK_SIZE-2))

        # 绘制当前下落方块（在遮罩层之后）
        if self.game_state == 'playing' and self.current_piece:
            for y, row in enumerate(self.current_piece):
                for x, val in enumerate(row):
                    if val:
                        # 计算相对于游戏区域的坐标偏移
                        block_x = (self.current_x + x) * BLOCK_SIZE + 1
                        block_y = (int(self.current_y) + y) * BLOCK_SIZE + 1
                        pygame.draw.rect(self.game_surface, self.current_color,
                            (block_x, block_y, BLOCK_SIZE-1, BLOCK_SIZE-1))

        # 显示当前分数
        if self.game_state == 'playing':
            # 添加暂停按钮
            scale_factor = self.game_area_rect.width / self.original_width
            pause_btn = pygame.Rect(self.game_area_rect.width - 100 * scale_factor, 10 * scale_factor, 80 * scale_factor, 35 * scale_factor)
            gradient_surface = pygame.Surface((pause_btn.width, pause_btn.height), pygame.SRCALPHA)
            color_start = (255, 105, 180)
            color_end = (147, 112, 219)
            for i in range(pause_btn.height):
                r = color_start[0] + int((color_end[0] - color_start[0]) * (i / pause_btn.height))
                g = color_start[1] + int((color_end[1] - color_start[1]) * (i / pause_btn.height))
                b = color_start[2] + int((color_end[2] - color_start[2]) * (i / pause_btn.height))
                pygame.draw.line(gradient_surface, (r, g, b, 128), (0, i), (pause_btn.width, i))
            self.game_surface.blit(gradient_surface, pause_btn.topleft)
            pygame.draw.rect(self.game_surface, (255, 255, 255, 128), pause_btn, 2, border_radius=8)
            pause_font = pygame.font.SysFont('kaiti', 24) if pygame.font.match_font('kaiti') else pygame.font.SysFont('simhei', 24)
            pause_text = pause_font.render('暂停', True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=pause_btn.center)
            self.game_surface.blit(pause_text, text_rect)
            
            score_text = self.font.render(f'分数: {self.score}', True, (255, 255, 255))
            scaled_score_text = pygame.transform.scale(score_text, (int(score_text.get_width() * scale_factor), int(score_text.get_height() * scale_factor)))
            self.game_surface.blit(scaled_score_text, (10 * scale_factor, 10 * scale_factor))

        # 绘制暂停菜单
        if self.game_state == 'paused':
            overlay = pygame.Surface((self.game_area_rect.width, self.game_area_rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.game_surface.blit(overlay, (0, 0))
            
            try:
                title_font = pygame.font.SysFont('kaiti', 32)  # 更换字体大小
            except:
                title_font = pygame.font.SysFont('simhei', 32)  # 更换字体大小
            # 绘制暂停标题
            pause_title = title_font.render('游戏暂停', True, (255, 255, 255))
            title_rect = pause_title.get_rect(center=(self.game_area_rect.width//2, self.game_area_rect.height//2 - 120))
            self.game_surface.blit(pause_title, title_rect)
            
            # 绘制按钮
            btn_width, btn_height = 160, 60
            btn_x = self.game_area_rect.width//2 - btn_width//2
            btn_y_offsets = [-100, -20, 60, 140]  # 调整按钮位置
            btn_texts = ['继续游戏', '重新开始', '返回主菜单', '退出游戏']
            btn_colors = [((0, 255, 100), (0, 180, 80)), ((255, 200, 0), (200, 160, 0)), ((180, 120, 255), (120, 80, 200)), ((255, 80, 80), (200, 50, 50))]
            for i, (text, colors) in enumerate(zip(btn_texts, btn_colors)):
                btn_rect = pygame.Rect(btn_x, self.game_area_rect.height//2 + btn_y_offsets[i], btn_width, btn_height)
                gradient_surface = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
                for y in range(btn_height):
                    ratio = y / btn_height
                    color = (int(colors[0][0] + ratio * (colors[1][0] - colors[0][0])),
                             int(colors[0][1] + ratio * (colors[1][1] - colors[0][1])),
                             int(colors[0][2] + ratio * (colors[1][2] - colors[0][2])))
                    pygame.draw.line(gradient_surface, color + (128,), (0, y), (btn_width, y))  # 设置半透明
                self.game_surface.blit(gradient_surface, btn_rect.topleft)
                pygame.draw.rect(self.game_surface, (255, 255, 255, 200), btn_rect, 2, border_radius=15)
                btn_font = title_font
                btn_text = btn_font.render(text, True, (255, 255, 255))
                text_rect = btn_text.get_rect(center=btn_rect.center)
                self.game_surface.blit(btn_text, text_rect)
                
                if i == 0:
                    self.continue_btn = btn_rect
                elif i == 1:
                    self.restart_btn = btn_rect
                elif i == 2:
                    self.main_menu_btn = btn_rect
                elif i == 3:
                    self.quit_btn = btn_rect
            
            # 优化音量控制条
            volume_font = pygame.font.SysFont('simhei', 20)
            self.volume_rect = pygame.Rect(btn_x, self.game_area_rect.height//2 + 220, btn_width, 25)
            pygame.draw.rect(self.game_surface, (50, 50, 50, 180), self.volume_rect, border_radius=12)
            fill_width = int(self.bg_volume * self.volume_rect.width)
            pygame.draw.rect(self.game_surface, (0, 255, 100, 180), (self.volume_rect.x, self.volume_rect.y, fill_width, 25), border_radius=12)
            pygame.draw.rect(self.game_surface, (255, 255, 255, 200), self.volume_rect, 2, border_radius=12)
            volume_text = volume_font.render(f'音量: {int(self.bg_volume*100)}%', True, (255, 255, 255))
            self.game_surface.blit(volume_text, (self.volume_rect.x, self.volume_rect.y - 30))


        if self.game_state == 'game_over':
            overlay = pygame.Surface((self.game_area_rect.width, self.game_area_rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.game_surface.blit(overlay, (0, 0))
            
            # 添加返回主界面按钮
            # 游戏结束按钮
            btn_width, btn_height = 160, 60
            btn_x = self.game_area_rect.width//2 - btn_width//2
            
            # 重新开始按钮
            restart_btn = pygame.Rect(btn_x, self.game_area_rect.height//2 + 40, btn_width, btn_height)
            gradient_surface = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
            color_start = (0, 255, 100)
            color_end = (0, 180, 80)
            for y in range(btn_height):
                ratio = y / btn_height
                r = int(color_start[0] + ratio * (color_end[0] - color_start[0]))
                g = int(color_start[1] + ratio * (color_end[1] - color_start[1]))
                b = int(color_start[2] + ratio * (color_end[2] - color_start[2]))
                pygame.draw.line(gradient_surface, (r, g, b, 128), (0, y), (btn_width, y))
            self.game_surface.blit(gradient_surface, restart_btn.topleft)
            pygame.draw.rect(self.game_surface, (255, 255, 255, 200), restart_btn, 2, border_radius=15)
            restart_text = self.font.render('返回主菜单', True, (255, 255, 255))
            text_rect = restart_text.get_rect(center=restart_btn.center)
            self.game_surface.blit(restart_text, text_rect)
            
            # 游戏结束文本
            game_over_text = self.font.render('游戏结束！', True, (255, 0, 0))
            score_text = self.font.render(f'最终分数: {self.score}', True, (255, 255, 255))
            text_rect = game_over_text.get_rect(center=(self.game_area_rect.width//2, self.game_area_rect.height//2 - 30))
            self.game_surface.blit(game_over_text, text_rect)
            score_rect = score_text.get_rect(center=(self.game_area_rect.width//2, self.game_area_rect.height//2 + 10))
            self.game_surface.blit(score_text, score_rect)

        # 新增开始菜单按钮绘制
        if self.game_state == 'start_menu':
            # 绘制游戏标题
            try:
                title_font = pygame.font.SysFont('kaiti', 40)
            except:
                title_font = pygame.font.SysFont('simhei', 40)
            # 绘制下方阴影
            shadow_text = title_font.render('马娘消消乐', True, (60, 60, 60))  # 深灰色阴影
            shadow_y = 55  # 调整阴影垂直偏移量
            shadow_rect = shadow_text.get_rect(center=(self.game_area_rect.width//2, shadow_y))
            self.game_surface.blit(shadow_text, shadow_rect)
            # 绘制主体文字
            title_text = title_font.render('马娘消消乐', True, (255,192,203))
            title_rect = title_text.get_rect(center=(self.game_area_rect.width//2, 50))
            self.game_surface.blit(title_text, title_rect)
            
            # 调整开始按钮位置
            start_btn = pygame.Rect(self.game_area_rect.width//2 - 80, self.game_area_rect.height//2 - 30, 160, 60)
            # 确保按钮位置基于游戏区域中心点动态计算
            music_btn = pygame.Rect(self.game_area_rect.width//2 - 80, start_btn.bottom + 20, 160, 60)
            # 绘制粉紫渐变开始按钮
            gradient_surface = pygame.Surface((start_btn.width, start_btn.height), pygame.SRCALPHA)
            color_start = (255, 105, 180)
            color_end = (147, 112, 219)
            for i in range(start_btn.height):
                r = color_start[0] + int((color_end[0] - color_start[0]) * (i / start_btn.height))
                g = color_start[1] + int((color_end[1] - color_start[1]) * (i / start_btn.height))
                b = color_start[2] + int((color_end[2] - color_start[2]) * (i / start_btn.height))
                pygame.draw.line(gradient_surface, (r, g, b, 128), (0, i), (start_btn.width, i))
            self.game_surface.blit(gradient_surface, start_btn.topleft)
            pygame.draw.rect(self.game_surface, (255,255,255, 128), start_btn, 3, border_radius=10)
            start_font = pygame.font.SysFont('kaiti', 28) if pygame.font.match_font('kaiti') else pygame.font.SysFont('simhei', 28)
            start_text = start_font.render('开始游戏', True, (255,255,255))
            start_text_rect = start_text.get_rect(center=start_btn.center)
            self.game_surface.blit(start_text, start_text_rect)
            # 确保按钮位置基于游戏区域中心点动态计算
            start_btn = pygame.Rect(self.game_area_rect.width//2 - 80, self.game_area_rect.height//2 - 30, 160, 60)
            music_btn = pygame.Rect(self.game_area_rect.width//2 - 80, start_btn.bottom + 20, 160, 60)
            btn_color_start = (0, 100, 0) if self.music_playing else (100, 0, 0)
            btn_color_end = (0, 200, 0) if self.music_playing else (200, 0, 0)
            gradient_surface = pygame.Surface((music_btn.width, music_btn.height), pygame.SRCALPHA)
            for i in range(music_btn.height):
                r = btn_color_start[0] + int((btn_color_end[0] - btn_color_start[0]) * (i / music_btn.height))
                g = btn_color_start[1] + int((btn_color_end[1] - btn_color_start[1]) * (i / music_btn.height))
                b = btn_color_start[2] + int((btn_color_end[2] - btn_color_start[2]) * (i / music_btn.height))
                pygame.draw.line(gradient_surface, (r, g, b, 128), (0, i), (music_btn.width, i))
            self.game_surface.blit(gradient_surface, music_btn.topleft)
            pygame.draw.rect(self.game_surface, (255,255,255, 128), music_btn, 3, border_radius=10)
            music_font = pygame.font.SysFont('kaiti', 28) if pygame.font.match_font('kaiti') else pygame.font.SysFont('simhei', 28)
            music_text = music_font.render('音乐: 开' if self.music_playing else '音乐: 关', True, (255,255,255))
            music_text_rect = music_text.get_rect(center=music_btn.center)
            self.game_surface.blit(music_text, music_text_rect)
            self.volume_rect = pygame.Rect(self.game_area_rect.width//2 - 100, music_btn.bottom + 20, 200, 20)
            pygame.draw.rect(self.game_surface, (50, 50, 50), self.volume_rect, border_radius=10)
            fill_width = int(self.bg_volume * self.volume_rect.width)
            pygame.draw.rect(self.game_surface, (0, 200, 0), (self.volume_rect.x, self.volume_rect.y, fill_width, 20), border_radius=10)
            pygame.draw.rect(self.game_surface, (255, 255, 255), self.volume_rect, 2, border_radius=10)
            volume_font = pygame.font.SysFont('kaiti', 20) if pygame.font.match_font('kaiti') else pygame.font.SysFont('simhei', 20)
            volume_text = volume_font.render(f'音量: {int(self.bg_volume*100)}%', True, (255,255,255))
            self.game_surface.blit(volume_text, (self.volume_rect.x, self.volume_rect.y - 25))
            music_font = pygame.font.SysFont('simhei', 17)
            music_name_line1 = music_font.render('当前正在播放的音乐为：', True, (255,255,255))
            music_name_line2 = music_font.render('winning the soul--Machico', True, (255,255,255))
            line1_rect = music_name_line1.get_rect(centerx=self.game_area_rect.width//2, top=self.volume_rect.bottom + 20)
            line2_rect = music_name_line2.get_rect(centerx=self.game_area_rect.width//2, top=line1_rect.bottom + 10)
            self.game_surface.blit(music_name_line1, line1_rect)
            self.game_surface.blit(music_name_line2, line2_rect)

        version_font = pygame.font.SysFont('simhei', 17)
        version_text = version_font.render('版本：1.0          作者：721K(皓)', True, (255, 255, 255))
        self.game_surface.blit(version_text, (10, self.game_area_rect.height - 20))

        self.screen.blit(self.game_surface, self.game_area_rect)
        pygame.display.flip()

    def move_piece(self, dx):
        self.current_x += dx
        if self.check_collision():
            self.current_x -= dx

    def rotate_piece(self):
        original_piece = self.current_piece
        # 顺时针旋转矩阵
        self.current_piece = [list(row) for row in zip(*self.current_piece[::-1])]
        # 检查旋转后是否越界
        if self.check_collision():
            # 尝试横向偏移
            offsets = [0, 1, -1, 2, -2]
            for offset in offsets:
                self.current_x += offset
                if not self.check_collision():
                    return
                self.current_x -= offset
            # 恢复原始形状
            self.current_piece = original_piece

if __name__ == '__main__':
    game = TetrisGame()
    game.spawn_new_piece()
    game.game_loop()
    pygame.quit()
    sys.exit()
