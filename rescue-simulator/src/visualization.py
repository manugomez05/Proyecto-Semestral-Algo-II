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

#from map_graph import MapGraph

class Visualization:
    def __init__(self, screen, engine):
        self.screen = screen
        self.engine = engine
        self.buttons = []
        # Cache de imágenes para evitar cargar desde disco en cada frame
        self.image_cache = {}
        #self.font = pygame.font.Font('paraIntegrar/assets/PressStart2P-Regular.ttf', 12)
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
                # Si hay error al cargar, devolver None
                return None
        
        return self.image_cache[cache_key]

    def create_buttons(self):

        # 📁 Ruta base del archivo actual (src/visualization.py)
        base_path = Path(__file__).resolve().parent

        # 📁 Ruta absoluta a la carpeta assets (un nivel arriba de src)
        assets_path = base_path.parent / 'assets'

        from functools import partial
        
        # Crear botón INIT por separado para controlar su visibilidad
        self.init_button = Button(str(assets_path / 'initBtn.png'), 'bottom', (-220,0), partial(self.engine.init_game))
        
        # Botones principales con dos posiciones: con INIT y sin INIT (centrados)
        # Cuando INIT está visible: posiciones originales
        # Cuando INIT no está visible: posiciones centradas (desplazadas -85px a la izquierda)
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
        
        # Lista de botones para manejar eventos (se actualizará dinámicamente)
        self.buttons = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            
            # Determinar qué botones mostrar según el estado
            show_init = self.engine.state in ("stopped", "game_over")
            
            # Manejar botón INIT solo si debe ser visible
            if show_init:
                self.init_button.handle_event(event)
                # Usar botones en posiciones normales (con INIT visible)
                self.play_button.handle_event(event)
                self.backward_button.handle_event(event)
                self.forward_button.handle_event(event)
                self.stop_button.handle_event(event)
            else:
                # Usar botones centrados (sin INIT)
                self.play_button_centered.handle_event(event)
                self.backward_button_centered.handle_event(event)
                self.forward_button_centered.handle_event(event)
                self.stop_button_centered.handle_event(event)
            
            # Botón save siempre disponible
            self.save_button.handle_event(event)

    def render(self):
        self.screen.fill(BLACK)
        
        # Actualizar animaciones en cada frame (para fluidez incluso en pausa)
        self.engine.update_collision_animations()
        
        # Determinar si mostrar botón INIT
        show_init = self.engine.state in ("stopped", "game_over")
        
        # Si el juego terminó, mostrar pantalla de game over
        if self.engine.state == "game_over":
            self.drawGameOverScreen()
        else:
            self.drawMap()
            self.drawCollisionAnimations()  # Dibujar animaciones de colisiones
            #self.drawDebugPanel()  # Mostrar panel de debug (DESACTIVADO)
            #self.drawTickInfo()  # Mostrar información del tick
            
            # Dibujar botones según visibilidad de INIT
            if show_init:
                # Dibujar INIT y botones en posición normal
                self.init_button.draw(self.screen)
                self.play_button.draw(self.screen)
                self.backward_button.draw(self.screen)
                self.forward_button.draw(self.screen)
                self.stop_button.draw(self.screen)
            else:
                # Dibujar botones centrados (sin INIT)
                self.play_button_centered.draw(self.screen)
                self.backward_button_centered.draw(self.screen)
                self.forward_button_centered.draw(self.screen)
                self.stop_button_centered.draw(self.screen)
            
            # Botón save siempre visible
            self.save_button.draw(self.screen)
        
        pygame.display.flip()

    def drawMap(self):
        graph = self.engine.map.graph
        
        # Dibujar las minas con radio completo (TEMPORAL para verificación)
        from src.mines_manager import drawMines
        drawMines(self.screen, self.engine.map.mine_manager, graph.rows, graph.cols, CELL_SIZE, 390, 20)
        
        #Dibuja bases de los jugadores
        self.engine.player1.drawPlayerBase(self.screen, 49,190)
        self.engine.player2.drawPlayerBase(self.screen, 1270,190)

        # Dibujar recursos y otros elementos
        for row in range(graph.rows):
            for col in range(graph.cols):
                node = graph.get_node(row, col)
                x, y = col * CELL_SIZE + 390, row * CELL_SIZE + 20
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                
                # Dibujar bases con color diferente (gris oscuro/azul oscuro)
                # Dibujar la base primero para que esté debajo de los vehículos
                if node.state in ("base_p1", "base_p2"):
                    # Color para las bases: un gris/azul más oscuro que el fondo
                    BASE_COLOR = (30, 40, 60)  # Color oscuro para las bases
                    pygame.draw.rect(self.screen, BASE_COLOR, rect, 0)  # Relleno sólido
                
                if node.state == 'resource' and node.content:
                    img = self.get_cached_image(node.content.img_path, (CELL_SIZE, CELL_SIZE))
                    if img:
                        self.screen.blit(img, (x, y))
                # Ya no dibujamos las minas aquí porque drawMines se encarga
                # Dibujar vehículos (pueden estar en estado "vehicle" o en bases con contenido)
                if (node.state == "vehicle" or node.state in ("base_p1", "base_p2")) and node.content:
                    v = node.content
                    
                    # Manejar listas de vehículos (mismo equipo en misma celda)
                    vehicles_to_draw = []
                    if isinstance(v, list):
                        vehicles_to_draw = v
                    else:
                        vehicles_to_draw = [v]
                    
                    # Dibujar cada vehículo en la celda
                    for idx, vehicle_data in enumerate(vehicles_to_draw):
                        # Obtener el objeto vehículo real para verificar status
                        vehicle_obj = None
                        if isinstance(vehicle_data, dict):
                            vehicle_obj = vehicle_data.get("object")
                        else:
                            vehicle_obj = vehicle_data
                        
                        # Verificar que el vehículo no esté destruido
                        if vehicle_obj:
                            status = getattr(vehicle_obj, "status", None)
                            if status == "destroyed":
                                continue  # No dibujar vehículos destruidos
                            
                            # Obtener la ruta de imagen del vehículo
                            img_path = getattr(vehicle_obj, "img_path", None)
                            if img_path:
                                # Cargar y renderizar la imagen del vehículo con tamaño aumentado
                                VEHICLE_SCALE = 2.5  # Factor de escala para hacer vehículos más grandes
                                vehicle_size = int(CELL_SIZE * VEHICLE_SCALE)
                                img = self.get_cached_image(img_path, (vehicle_size, vehicle_size))
                                
                                if img:
                                    # Cada jugador ya tiene sus propias imágenes que apuntan hacia el centro
                                    # Jugador_1: usa *1.png (apuntan a la derecha →)
                                    # Jugador_2: usa *2.png (apuntan a la izquierda ←)
                                    # No es necesario voltear las imágenes
                                    
                                    # Si hay múltiples vehículos, desplazarlos ligeramente para que se vean
                                    displacement = 0
                                    if len(vehicles_to_draw) > 1:
                                        # Desplazar cada vehículo adicional ligeramente
                                        displacement = idx * 3  # 3 píxeles de desplazamiento por vehículo
                                    
                                    # Centrar la imagen más grande en la celda
                                    offset_x = x - (vehicle_size - CELL_SIZE) // 2 + displacement
                                    offset_y = y - (vehicle_size - CELL_SIZE) // 2 + displacement
                                    self.screen.blit(img, (offset_x, offset_y))
                            else:
                                # Fallback: dibujar círculo si no hay imagen
                                color = getattr(vehicle_obj, "color", (255, 255, 255))
                                # Desplazar círculos si hay múltiples vehículos
                                displacement = idx * 3 if len(vehicles_to_draw) > 1 else 0
                                circle_center = (rect.center[0] + displacement, rect.center[1] + displacement)
                                pygame.draw.circle(self.screen, color, circle_center, 6)

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
            
            # Calcular progreso de la animación (0.0 a 1.0)
            progress = frame / max_frames
            
            # Efecto de expansión y desvanecimiento
            if anim_type == "vehicle":
                # Colisión entre vehículos: explosión roja/naranja
                self._draw_explosion_effect(center_x, center_y, progress, 
                                            colors=[(255, 0, 0), (255, 100, 0), (255, 200, 0)])
            elif anim_type == "mine":
                # Colisión con mina: explosión amarilla/naranja
                self._draw_explosion_effect(center_x, center_y, progress,
                                            colors=[(255, 200, 0), (255, 150, 0), (200, 100, 0)])
    
    def _draw_explosion_effect(self, center_x, center_y, progress, colors):
        """Dibuja un efecto de explosión con círculos concéntricos
        
        Args:
            center_x, center_y: Coordenadas del centro de la explosión
            progress: Progreso de la animación (0.0 a 1.0)
            colors: Lista de colores para los círculos concéntricos
        """
        # Fase 1 (0-0.4): Expansión rápida
        # Fase 2 (0.4-1.0): Desvanecimiento
        
        if progress < 0.4:
            # Fase de expansión
            scale = progress / 0.4  # 0 a 1
            alpha = 255
        else:
            # Fase de desvanecimiento
            scale = 1.0
            alpha = int(255 * (1.0 - (progress - 0.4) / 0.6))
        
        # Dibujar múltiples círculos concéntricos
        max_radius = int(CELL_SIZE * 2 * scale)
        
        for i, color in enumerate(colors):
            radius = max(1, max_radius - i * 8)
            if radius > 0:
                # Crear superficie temporal con alpha
                temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                # Aplicar alpha al color
                color_with_alpha = (*color, alpha)
                pygame.draw.circle(temp_surface, color_with_alpha, (radius, radius), radius)
                # Dibujar en pantalla
                self.screen.blit(temp_surface, (center_x - radius, center_y - radius))
        
        # Agregar partículas dispersas en la fase de expansión
        if progress < 0.5:
            import random
            random.seed(int(center_x * center_y))  # Seed para consistencia
            num_particles = 8
            for i in range(num_particles):
                angle = (i / num_particles) * 2 * 3.14159
                distance = int(max_radius * 1.5 * progress)
                particle_x = int(center_x + distance * pygame.math.Vector2(1, 0).rotate_rad(angle).x)
                particle_y = int(center_y + distance * pygame.math.Vector2(1, 0).rotate_rad(angle).y)
                particle_radius = max(1, int(4 * (1 - progress)))
                particle_color = (*colors[0], alpha)
                
                # Crear superficie temporal para la partícula
                particle_surface = pygame.Surface((particle_radius * 2, particle_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, particle_color, (particle_radius, particle_radius), particle_radius)
                self.screen.blit(particle_surface, (particle_x - particle_radius, particle_y - particle_radius))

    def drawDebugPanel(self):
        """Dibuja el panel de debug con eventos de colisiones y destrucciones"""
        try:
            # Cargar fuente
            import pygame
            font = pygame.font.Font(None, 20)  # Fuente más pequeña para debug
            font_large = pygame.font.Font(None, 28)  # Fuente más grande para tick
            
            # Posición del panel (esquina superior central)
            panel_x = 440
            panel_y = 10
            line_height = 20
            
            # Mostrar tick actual
            tick_text = font_large.render(f"TICK: {self.engine.tick}", True, (255, 255, 0))
            self.screen.blit(tick_text, (panel_x, panel_y))
            
            # Título del panel
            title = font.render("=== DEBUG LOG ===", True, (0, 255, 255))
            self.screen.blit(title, (panel_x, panel_y + 30))
            
            # Dibujar eventos recientes (del más reciente al más antiguo)
            y_offset = panel_y + 55
            
            if hasattr(self.engine, 'debug_events') and self.engine.debug_events:
                # Mostrar eventos en orden inverso (más reciente arriba)
                for event in reversed(self.engine.debug_events[-10:]):  # Últimos 10 eventos
                    tick = event.get('tick', 0)
                    event_type = event.get('type', 'unknown')
                    message = event.get('message', '')
                    color = event.get('color', (255, 255, 255))
                    
                    # Formatear el mensaje
                    text = f"[T{tick:3d}] {message}"
                    text_surface = font.render(text, True, color)
                    self.screen.blit(text_surface, (panel_x, y_offset))
                    y_offset += line_height
            else:
                # Sin eventos
                no_events = font.render("Sin eventos recientes", True, (150, 150, 150))
                self.screen.blit(no_events, (panel_x, y_offset))
        
        except Exception as e:
            # Si hay error, no mostrar nada para no romper la visualización
            pass



    def drawTickInfo(self):
        """Dibuja información del tick y estado de minas dinámicas"""
        try:
            font = pygame.font.Font('Proyecto-Semestral-Algo-II/rescue-simulator/assets/Press_Start_2P/PressStart2P-Regular.ttf', 14)
            
            # Mostrar tick actual y tiempo transcurrido
            elapsed_time = time.time() - self.engine.start_time
            tick_text = font.render(f"Tick: {self.engine.tick}", True, (255, 255, 255))
            time_text = font.render(f"Tiempo: {elapsed_time:.1f}s", True, (255, 255, 255))
            self.screen.blit(tick_text, (10, 10))
            self.screen.blit(time_text, (10, 25))
            
            # Mostrar estado de minas G1
            g1_mines = [mine for mine in self.engine.map.mine_manager.all() if mine.type.name == 'G1']
            if g1_mines:
                g1_mine = g1_mines[0]  # Primera mina G1
                status = "ACTIVA" if g1_mine.active else "INACTIVA"
                color = (0, 255, 0) if g1_mine.active else (255, 0, 0)
                status_text = font.render(f"G1: {status}", True, color)
                self.screen.blit(status_text, (10, 50))
                
                # Mostrar posición de la mina G1
                row, col = g1_mine.center
                pos_text = font.render(f"Posición: ({row}, {col})", True, (255, 255, 255))
                self.screen.blit(pos_text, (10, 75))
                
                # Mostrar próximo cambio en segundos
                next_change = g1_mine.next_activation - elapsed_time
                if next_change > 0:
                    change_text = font.render(f"Próximo cambio en: {next_change:.1f}s", True, (255, 255, 255))
                    self.screen.blit(change_text, (10, 100))
        except:
            pass  # Si hay error, no mostrar información

    def drawGameOverScreen(self):
        """Dibuja la pantalla de fin de juego:
        - EMPATE: muestra ambos jugadores lado a lado.
        - GANADOR único: muestra solo la info del ganador, centrada.
        """
        if not self.engine.game_over_info:
            return

        info = self.engine.game_over_info
        screen_width, screen_height = self.screen.get_size()

        # Fondo semi-transparente oscuro
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(220)
        overlay.fill((15, 20, 35))
        self.screen.blit(overlay, (0, 0))

        # Intentar cargar la fuente Press_Start_2P desde assets; fallback a fuente por defecto
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

        # Título "FIN DEL JUEGO"
        title = title_font.render("FIN DEL JUEGO", True, (255, 255, 100))
        title_rect = title.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(title, title_rect)
        y_offset += 100

        # Razón del fin del juego
        reason_text = small_font.render(info.get("reason", ""), True, PALETTE_3)
        reason_rect = reason_text.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(reason_text, reason_rect)
        y_offset += 60

        # Anuncio del ganador
        winner_colors = {
            "blue": (100, 150, 255),
            "red": (255, 100, 100),
            "gray": (150, 150, 150)
        }
        winner_color = winner_colors.get(info.get("winner_color"), (255, 255, 255))

        if info.get("winner") == "Empate":
            winner_text = header_font.render("¡EMPATE!", True, winner_color)
        else:
            winner_text = header_font.render(f"¡GANADOR: {str(info.get('winner','')).upper()}!", True, winner_color)

        winner_rect = winner_text.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(winner_text, winner_rect)
        y_offset += 80

        # ancho estimado para el bloque de estadísticas
        stats_width = min(460, max(300, screen_width // 3))

        if info.get("winner") == "Empate":
            # Mostrar ambos jugadores lado a lado
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
            # Mostrar sólo la info del ganador, centrada
            winner_name = info.get("winner")
            p1 = info.get("player1", {})
            p2 = info.get("player2", {})

            if p1.get("name") == winner_name:
                winner_info = p1
            elif p2.get("name") == winner_name:
                winner_info = p2
            else:
                # Si no coincide el nombre, intentar inferir por puntaje mayor
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

        # Instrucción para reiniciar
        y_offset = screen_height - 100
        restart_text = small_font.render("Presiona el botón INIT para jugar de nuevo", True, PALETTE_3)
        restart_rect = restart_text.get_rect(center=(screen_width // 2, y_offset))
        self.screen.blit(restart_text, restart_rect)

        # Dibujar botones en la pantalla de game over (con INIT visible)
        self.init_button.draw(self.screen)
        self.play_button.draw(self.screen)
        self.backward_button.draw(self.screen)
        self.forward_button.draw(self.screen)
        self.stop_button.draw(self.screen)
        self.save_button.draw(self.screen)
    
    def _draw_player_stats(self, player_info, x, y, width, info_font, small_font, color):
        """Dibuja las estadísticas de un jugador"""
        y_offset = y
        
        # Nombre del jugador
        name_text = info_font.render(player_info["name"], True, color)
        self.screen.blit(name_text, (x, y_offset))
        y_offset += 50
        
        # Puntuación
        score_text = info_font.render(f"Puntos: {player_info['score']}", True, PALETTE_1)
        self.screen.blit(score_text, (x, y_offset))
        y_offset += 60
        
        # Estado de vehículos
        vehicles_title = small_font.render("Estado de Vehículos:", True, (200, 200, 200))
        self.screen.blit(vehicles_title, (x, y_offset))
        y_offset += 40
        
        vehicles = player_info["vehicles"]
        status_labels = {
            "in_base": "En base",
            "in_mission": "En misión",
            "returning": "Regresando",
            "job_done": "Trabajo hecho",
            "destroyed": "Destruidos"
        }
        
        status_colors = {
            "in_base": (100, 255, 100),
            "in_mission": (255, 200, 100),
            "returning": (100, 200, 255),
            "job_done": (150, 255, 150),
            "destroyed": (255, 100, 100)
        }
        
        for status, label in status_labels.items():
            count = vehicles.get(status, 0)
            color = status_colors.get(status, (255, 255, 255))
            status_text = small_font.render(f"  {label}: {count}", True, color)
            self.screen.blit(status_text, (x + 20, y_offset))
            y_offset += 30

class Button:
    # Cache compartido de imágenes para todos los botones
    _image_cache = {}
    
    def __init__(self, image_path, position, offset=(0,0), action=None):
        # Usar caché para cargar imagen solo una vez
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
    
    rect.move_ip(offset)
    return rect