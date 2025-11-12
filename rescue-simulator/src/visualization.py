"""
Módulo: visualization
-------------------------------------------------
Maneja todo lo relacionado con la visualización y la interfaz 
gráfica del simulador usando Pygame.

Responsabilidades:
- Dibujar el mapa, recursos, minas y bases en pantalla.
- Definir y manejar los botones de la interfaz.
- Capturar los eventos de usuario (clics, cierre de ventana).
- Coordinarse con el `GameEngine` para mostrar el estado actual.
"""
import pygame
import time
from pathlib import Path

from src import PALETTE_6, PALETTE_1, PALETTE_2, PALETTE_3, PALETTE_4, PALETTE_5

# Definir las constantes directamente para evitar problemas de importación
BLACK = (22, 33, 60)
PALETTE = (46, 68, 96)
CELL_SIZE = 17

class Visualization:
    def __init__(self, screen, engine):
        self.screen = screen
        self.engine = engine
        self.buttons = []
        self.image_cache = {}
        self.create_buttons()

    def get_cached_image(self, img_path, size):
        """
        Obtiene una imagen del caché. Si no existe, la carga, escala y guarda en caché.
        
        Args:
            img_path: Ruta de la imagen
            size: Tupla (ancho, alto) para escalar
        
        Returns:
            Superficie pygame con la imagen escalada
        """
        cache_key = (img_path, size)
        
        if cache_key not in self.image_cache:
            try:
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, size)
                self.image_cache[cache_key] = img
            except Exception as e:
                return None
        
        return self.image_cache[cache_key]

    def create_buttons(self):

        base_path = Path(__file__).resolve().parent

        assets_path = base_path.parent / 'assets'

        from functools import partial
        
        # Crear botón INIT por separado para controlar su visibilidad
        self.init_button = Button(str(assets_path / 'initBtn.png'), 'bottom', (-220,0), partial(self.engine.init_game))
        
        self.play_button = Button(str(assets_path / 'playBtn.png'), 'bottom', (-50,0), partial(self.engine.start_game))
        self.backward_button = Button(str(assets_path / 'backwardsBtn.png'), 'bottom', (80,0), partial(self.engine.step_backward))
        self.forward_button = Button(str(assets_path / 'forwardsBtn.png'), 'bottom', (170,0), partial(self.engine.step_forward))
        self.stop_button = Button(str(assets_path / 'stopBtn.png'), 'bottom', (270,0), partial(self.engine.stop_game))
        
        # Posiciones alternativas (centradas) cuando INIT no está visible
        self.play_button_centered = Button(str(assets_path / 'playBtn.png'), 'bottom', (-135,0), partial(self.engine.start_game))
        self.backward_button_centered = Button(str(assets_path / 'backwardsBtn.png'), 'bottom', (-5,0), partial(self.engine.step_backward))
        self.forward_button_centered = Button(str(assets_path / 'forwardsBtn.png'), 'bottom', (85,0), partial(self.engine.step_forward))
        self.stop_button_centered = Button(str(assets_path / 'stopBtn.png'), 'bottom', (185,0), partial(self.engine.stop_game))
        
        # Botón save siempre en la misma posición
        self.save_button = Button(str(assets_path / 'saveBtn.png'), 'bottomLeft', (40,0), """partial(self.engine.save_game)""")
        
        self.exit_button = TextButton('X', 'topRight', (-40, 0), exit, font_size=32, color=(255, 80, 80), hover_color=(255, 120, 120))
        
        self.buttons = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            
            # Determinar qué botones mostrar según el estado
            show_init = self.engine.state in ("stopped", "game_over")
            
            if show_init:
                self.init_button.handle_event(event)
                self.play_button.handle_event(event)
                self.backward_button.handle_event(event)
                self.forward_button.handle_event(event)
                self.stop_button.handle_event(event)
            else:
                self.play_button_centered.handle_event(event)
                self.backward_button_centered.handle_event(event)
                self.forward_button_centered.handle_event(event)
                self.stop_button_centered.handle_event(event)
            
            self.save_button.handle_event(event)
            
            self.exit_button.handle_event(event)

    def render(self):
        self.screen.fill(BLACK)
        
        self.engine.update_collision_animations()
        
        show_init = self.engine.state in ("stopped", "game_over")
        
        if self.engine.state == "game_over":
            self.drawGameOverScreen()
        else:
            self.drawMap()
            self.drawCollisionAnimations() 
            
            # Dibujar botones según visibilidad de INIT
            if show_init:
                self.init_button.draw(self.screen)
                self.play_button.draw(self.screen)
                self.backward_button.draw(self.screen)
                self.forward_button.draw(self.screen)
                self.stop_button.draw(self.screen)
            else:
                self.play_button_centered.draw(self.screen)
                self.backward_button_centered.draw(self.screen)
                self.forward_button_centered.draw(self.screen)
                self.stop_button_centered.draw(self.screen)
            
            self.save_button.draw(self.screen)
        
        self.exit_button.draw(self.screen)
        
        pygame.display.flip()

    def drawMap(self):
        graph = self.engine.map.graph
        
        from src.mines_manager import drawMines
        drawMines(self.screen, self.engine.map.mine_manager, graph.rows, graph.cols, CELL_SIZE, 390, 20)
        
        self.engine.player1.drawPlayerBase(self.screen, 49,190)
        self.engine.player2.drawPlayerBase(self.screen, 1270,190)

        for row in range(graph.rows):
            for col in range(graph.cols):
                node = graph.get_node(row, col)
                x, y = col * CELL_SIZE + 390, row * CELL_SIZE + 20
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                
                if node.state in ("base_p1", "base_p2"):
                    if node.state == "base_p1":
                        BASE_COLOR = (40, 60, 90) 
                        BORDER_COLOR = (70, 110, 180)
                    else:
                        BASE_COLOR = (90, 40, 40) 
                        BORDER_COLOR = (180, 70, 70)  
                    
                    pygame.draw.rect(self.screen, BASE_COLOR, rect, 0)  
                    pygame.draw.rect(self.screen, BORDER_COLOR, rect, 1) 
                
                if node.state == 'resource' and node.content:
                    img = self.get_cached_image(node.content.img_path, (CELL_SIZE, CELL_SIZE))
                    if img:
                        self.screen.blit(img, (x, y))
                # Dibujar vehículos (pueden estar en estado "vehicle" o en bases con contenido)
                if (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
                    v = node.content
                    
                    vehicles_to_draw = []
                    if isinstance(v, list):
                        vehicles_to_draw = v
                    else:
                        vehicles_to_draw = [v]
                    
                    for idx, vehicle_data in enumerate(vehicles_to_draw):
                        vehicle_obj = None
                        if isinstance(vehicle_data, dict):
                            vehicle_obj = vehicle_data.get("object")
                        else:
                            vehicle_obj = vehicle_data
                        
                        if vehicle_obj:
                            status = getattr(vehicle_obj, "status", None)
                            if status == "destroyed":
                                continue
                            
                            img_path = getattr(vehicle_obj, "img_path", None)
                            if img_path:
                                VEHICLE_SCALE = 2.5
                                vehicle_size = int(CELL_SIZE * VEHICLE_SCALE)
                                img = self.get_cached_image(img_path, (vehicle_size, vehicle_size))
                                
                                if img:
                                    displacement = 0
                                    if len(vehicles_to_draw) > 1:
                                        displacement = idx * 3 
                                    
                                    offset_x = x - (vehicle_size - CELL_SIZE) // 2 + displacement
                                    offset_y = y - (vehicle_size - CELL_SIZE) // 2 + displacement
                                    self.screen.blit(img, (offset_x, offset_y))
                            else:
                                color = getattr(vehicle_obj, "color", (255, 255, 255))
                                displacement = idx * 3 if len(vehicles_to_draw) > 1 else 0
                                circle_center = (rect.center[0] + displacement, rect.center[1] + displacement)
                                pygame.draw.circle(self.screen, color, circle_center, 6)

                if node.state not in ("base_p1", "base_p2"): 
                    pygame.draw.rect(self.screen, PALETTE_6, rect, 1)

    def drawCollisionAnimations(self):
        """Dibuja las animaciones de colisiones activas"""
        for anim in self.engine.collision_animations:
            pos = anim['position']
            frame = anim['frame']
            max_frames = anim['max_frames']
            anim_type = anim['type']
            
            # Convertir posición de celda a píxeles
            row, col = pos
            x = col * CELL_SIZE + 390
            y = row * CELL_SIZE + 20
            center_x = x + CELL_SIZE // 2
            center_y = y + CELL_SIZE // 2
            
            progress = frame / max_frames
            
            # Efecto de expansión
            if anim_type == "vehicle":
                self._draw_explosion_effect(center_x, center_y, progress, 
                                            colors=[(255, 0, 0), (255, 100, 0), (255, 200, 0)])
            elif anim_type == "mine":
                self._draw_explosion_effect(center_x, center_y, progress,
                                            colors=[(255, 200, 0), (255, 150, 0), (200, 100, 0)])
    
    def _draw_explosion_effect(self, center_x, center_y, progress, colors):
        """Dibuja un efecto de explosión simple con círculos concéntricos
        
        Args:
            center_x, center_y: Coordenadas del centro de la explosión
            progress: Progreso de la animación (0.0 a 1.0)
            colors: Lista de colores para los círculos concéntricos
        """

        if progress < 0.4:
            scale = progress / 0.4  
            alpha = 255
        else:
            scale = 1.0
            alpha = int(255 * (1.0 - (progress - 0.4) / 0.6))
        
        max_radius = int(CELL_SIZE * 2 * scale)
        
        for i, color in enumerate(colors):
            radius = max(1, max_radius - i * 8)
            if radius > 0:
                temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                color_with_alpha = (*color, alpha)
                pygame.draw.circle(temp_surface, color_with_alpha, (radius, radius), radius)
                self.screen.blit(temp_surface, (center_x - radius, center_y - radius))

    def drawDebugPanel(self):
        """Dibuja el panel de debug con eventos de colisiones y destrucciones"""
        try:
            import pygame
            font = pygame.font.Font(None, 20) 
            font_large = pygame.font.Font(None, 28) 
            
            panel_x = 440
            panel_y = 10
            line_height = 20
            
            tick_text = font_large.render(f"TICK: {self.engine.tick}", True, (255, 255, 0))
            self.screen.blit(tick_text, (panel_x, panel_y))
            
            title = font.render("=== DEBUG LOG ===", True, (0, 255, 255))
            self.screen.blit(title, (panel_x, panel_y + 30))
            
            y_offset = panel_y + 55
            
            if hasattr(self.engine, 'debug_events') and self.engine.debug_events:
                for event in reversed(self.engine.debug_events[-10:]): 
                    tick = event.get('tick', 0)
                    event_type = event.get('type', 'unknown')
                    message = event.get('message', '')
                    color = event.get('color', (255, 255, 255))
                    
                    text = f"[T{tick:3d}] {message}"
                    text_surface = font.render(text, True, color)
                    self.screen.blit(text_surface, (panel_x, y_offset))
                    y_offset += line_height
            else:
                no_events = font.render("Sin eventos recientes", True, (150, 150, 150))
                self.screen.blit(no_events, (panel_x, y_offset))
        
        except Exception as e:
            pass



    def drawTickInfo(self):
        """Dibuja información del tick y estado de minas dinámicas"""
        try:
            font = pygame.font.Font('Proyecto-Semestral-Algo-II/rescue-simulator/assets/Press_Start_2P/PressStart2P-Regular.ttf', 14)
            
            elapsed_time = time.time() - self.engine.start_time
            tick_text = font.render(f"Tick: {self.engine.tick}", True, (255, 255, 255))
            time_text = font.render(f"Tiempo: {elapsed_time:.1f}s", True, (255, 255, 255))
            self.screen.blit(tick_text, (10, 10))
            self.screen.blit(time_text, (10, 25))
            
            g1_mines = [mine for mine in self.engine.map.mine_manager.all() if mine.type.name == 'G1']
            if g1_mines:
                g1_mine = g1_mines[0] 
                status = "ACTIVA" if g1_mine.active else "INACTIVA"
                color = (0, 255, 0) if g1_mine.active else (255, 0, 0)
                status_text = font.render(f"G1: {status}", True, color)
                self.screen.blit(status_text, (10, 50))
                
                row, col = g1_mine.center
                pos_text = font.render(f"Posición: ({row}, {col})", True, (255, 255, 255))
                self.screen.blit(pos_text, (10, 75))
                
                next_change = g1_mine.next_activation - elapsed_time
                if next_change > 0:
                    change_text = font.render(f"Próximo cambio en: {next_change:.1f}s", True, (255, 255, 255))
                    self.screen.blit(change_text, (10, 100))
        except:
            pass 

    def drawGameOverScreen(self):
        """Dibuja la pantalla de fin de juego:
        - EMPATE: muestra ambos jugadores lado a lado.
        - GANADOR único: muestra solo la info del ganador, centrada.
        """
        if not self.engine.game_over_info:
            return

        info = self.engine.game_over_info
        screen_width, screen_height = self.screen.get_size()

        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(230)
        overlay.fill((10, 15, 25)) 
        self.screen.blit(overlay, (0, 0))

        try:
            root_path = Path(__file__).resolve().parents[1]
            font_path = root_path / "assets" / "Press_Start_2P" / "PressStart2P-Regular.ttf"
            title_font = pygame.font.Font(str(font_path), 50)
            header_font = pygame.font.Font(str(font_path), 38)
            info_font = pygame.font.Font(str(font_path), 24)
            small_font = pygame.font.Font(str(font_path), 14)
        except Exception:
            title_font = pygame.font.Font(None, 50)
            header_font = pygame.font.Font(None, 38)
            info_font = pygame.font.Font(None, 24)
            small_font = pygame.font.Font(None, 14)

        y_offset = 50

        title_text = "FIN DEL JUEGO"
        title_color = (255, 255, 120) 
        shadow_color = (80, 80, 0)    
        
        title_shadow = title_font.render(title_text, True, shadow_color)
        shadow_rect = title_shadow.get_rect(center=(screen_width // 2 + 3, y_offset + 3))
        self.screen.blit(title_shadow, shadow_rect)
        
        title = title_font.render(title_text, True, title_color)
        title_rect = title.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(title, title_rect)
        y_offset += 100

        reason_text = small_font.render(info.get("reason", ""), True, PALETTE_3)
        reason_rect = reason_text.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(reason_text, reason_rect)
        y_offset += 60

        winner_colors = {
            "blue": (100, 180, 255),  
            "red": (255, 120, 120),   
            "gray": (180, 180, 190) 
        }
        winner_color = winner_colors.get(info.get("winner_color"), (255, 255, 255))

        if info.get("winner") == "Empate":
            winner_text = header_font.render("¡EMPATE!", True, winner_color)
        else:
            winner_text = header_font.render(f"¡GANADOR: {str(info.get('winner','')).upper()}!", True, winner_color)

        winner_rect = winner_text.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(winner_text, winner_rect)
        y_offset += 80

        stats_width = min(460, max(300, screen_width // 3))

        if info.get("winner") == "Empate":
            left_x = screen_width // 4 - stats_width // 2
            right_x = 3 * screen_width // 4 - stats_width // 2

            self._draw_player_stats(
                info.get("player1", {}),
                left_x,
                y_offset,
                stats_width,
                info_font,
                small_font,
                (100, 150, 255)
            )

            self._draw_player_stats(
                info.get("player2", {}),
                right_x,
                y_offset,
                stats_width,
                info_font,
                small_font,
                (255, 100, 100)
            )
        else:
            winner_name = info.get("winner")
            p1 = info.get("player1", {})
            p2 = info.get("player2", {})

            if p1.get("name") == winner_name:
                winner_info = p1
            elif p2.get("name") == winner_name:
                winner_info = p2
            else:
                winner_info = p1 if p1.get("score", 0) >= p2.get("score", 0) else p2

            center_x = screen_width // 2 - stats_width // 2 + 100
            if winner_info:
                self._draw_player_stats(
                    winner_info,
                    center_x,
                    y_offset,
                    stats_width,
                    info_font,
                    small_font,
                    winner_color
                )

        y_offset = screen_height - 100
        restart_text = small_font.render("Presiona el botón INIT para jugar de nuevo", True, PALETTE_3)
        restart_rect = restart_text.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(restart_text, restart_rect)

        self.init_button.draw(self.screen)
        self.play_button.draw(self.screen)
        self.backward_button.draw(self.screen)
        self.forward_button.draw(self.screen)
        self.stop_button.draw(self.screen)
        self.save_button.draw(self.screen)
        self.exit_button.draw(self.screen)
    
    def _draw_player_stats(self, player_info, x, y, width, info_font, small_font, color):
        """Dibuja las estadísticas de un jugador"""
        screen_width, _ = self.screen.get_size() 
        y_offset = y
        
        name_text = info_font.render(player_info["name"], True, color)
        name_rect = name_text.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(name_text, name_rect)
        y_offset += 50
        
        score_text = info_font.render(f"Puntos: {player_info['score']}", True, PALETTE_1)
        score_rect = score_text.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(score_text, score_rect)
        y_offset += 60
        
        vehicles_title = small_font.render("Estado de Vehículos:", True, (200, 200, 200))
        vehicles_title_rect = vehicles_title.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(vehicles_title, vehicles_title_rect)
        y_offset += 40
        
        vehicles = player_info["vehicles"]
        status_labels = {
            "job_done": "Trabajo hecho",
            "destroyed": "Destruidos"
        }
        
        status_colors = {
            "job_done": (180, 255, 180),    
            "destroyed": (255, 120, 120)  
        }
        
        for status, label in status_labels.items():
            count = vehicles.get(status, 0)
            status_color = status_colors.get(status, (255, 255, 255))
            status_text = small_font.render(f"{label}: {count}", True, status_color)
            status_rect = status_text.get_rect(center=(screen_width // 2, y_offset))
            self.screen.blit(status_text, status_rect)
            y_offset += 30

class Button:
    _image_cache = {}
    
    def __init__(self, image_path, position, offset=(0,0), action=None):
        if image_path not in Button._image_cache:
            Button._image_cache[image_path] = pygame.image.load(image_path).convert_alpha()
        
        self.image = Button._image_cache[image_path]
        self.position = position
        self.offset = offset
        self.rect = align(self.image, position, offset)
        self.action = action

    def draw(self, screen):
        self.rect = align(self.image, self.position, self.offset)
        screen.blit(self.image, self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()

def align(surface, position, offset=(0,0), margin=10):
    screen_rect = pygame.display.get_surface().get_rect()
    rect = surface.get_rect()
    if position == "bottom":
        rect.midbottom = screen_rect.midbottom
        rect.y -= margin
    elif position == "bottomLeft":
        rect.bottomleft = screen_rect.bottomleft
        rect.x += margin
        rect.y -= margin
    elif position == "topRight":
        rect.topright = screen_rect.topright
        rect.x -= margin
        rect.y += margin
    
    rect.move_ip(offset)
    return rect


class TextButton:
    """Botón de texto usando la misma tipografía del juego"""
    
    def __init__(self, text, position, offset=(0,0), action=None, font_size=24, color=(255, 255, 255), hover_color=(255, 200, 200)):
        self.text = text
        self.position = position
        self.offset = offset
        self.action = action
        self.font_size = font_size
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
        
        try:
            root_path = Path(__file__).resolve().parents[1]
            font_path = root_path / "assets" / "Press_Start_2P" / "PressStart2P-Regular.ttf"
            self.font = pygame.font.Font(str(font_path), font_size)
        except Exception:
            self.font = pygame.font.Font(None, font_size)
        
        self._update_surface()
        self.rect = align(self.surface, position, offset)
    
    def _update_surface(self):
        """Actualiza la superficie del texto"""
        color = self.hover_color if self.hovered else self.color
        self.surface = self.font.render(self.text, True, color)
    
    def draw(self, screen):
        """Dibuja el botón en la pantalla"""
        mouse_pos = pygame.mouse.get_pos()
        was_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        if was_hovered != self.hovered:
            self._update_surface()
            self.rect = align(self.surface, self.position, self.offset)
        
        screen.blit(self.surface, self.rect)
    
    def handle_event(self, event):
        """Maneja eventos del botón"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()