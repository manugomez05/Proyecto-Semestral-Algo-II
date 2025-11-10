"""
Ejemplo de Integración del Sistema de Persistencia con UI
=========================================================

Este archivo muestra cómo agregar botones y funcionalidades
del sistema de persistencia a la interfaz de usuario.

NO ES NECESARIO EJECUTAR ESTE ARCHIVO - Es solo referencia
para implementar funcionalidades en visualization.py
"""

import pygame
from src.game_engine import GameEngine

class VisualizationConPersistencia:
    """
    Ejemplo de cómo extender la clase Visualization
    para agregar funcionalidades de persistencia
    """
    
    def __init__(self, screen, engine):
        self.screen = screen
        self.engine = engine
        
        # Botones adicionales para persistencia
        self.create_persistence_buttons()
        
        # Estado de diálogos
        self.show_save_dialog = False
        self.show_load_dialog = False
        self.show_stats_dialog = False
        
    def create_persistence_buttons(self):
        """Crear botones para funcionalidades de persistencia"""
        
        # Posiciones para nuevos botones (ajustar según tu UI)
        x_base = 1100
        y_base = 100
        button_height = 50
        spacing = 10
        
        self.buttons = {
            # Botón para guardar manualmente
            "save_manual": pygame.Rect(
                x_base, y_base, 200, button_height
            ),
            
            # Botón para cargar guardado
            "load_manual": pygame.Rect(
                x_base, y_base + (button_height + spacing) * 1, 200, button_height
            ),
            
            # Botón para exportar estadísticas
            "export_stats": pygame.Rect(
                x_base, y_base + (button_height + spacing) * 2, 200, button_height
            ),
            
            # Botón para ver historial
            "view_history": pygame.Rect(
                x_base, y_base + (button_height + spacing) * 3, 200, button_height
            ),
            
            # Botón para recuperar simulación
            "resume_sim": pygame.Rect(
                x_base, y_base + (button_height + spacing) * 4, 200, button_height
            )
        }
    
    def handle_events(self):
        """Manejo de eventos incluyendo los nuevos botones"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.handle_button_clicks(mouse_pos)
    
    def handle_button_clicks(self, mouse_pos):
        """Procesar clicks en los botones de persistencia"""
        
        # Guardar manualmente
        if self.buttons["save_manual"].collidepoint(mouse_pos):
            self.show_save_dialog = True
        
        # Cargar guardado
        elif self.buttons["load_manual"].collidepoint(mouse_pos):
            self.show_load_dialog = True
        
        # Exportar estadísticas
        elif self.buttons["export_stats"].collidepoint(mouse_pos):
            self.export_statistics()
        
        # Ver historial
        elif self.buttons["view_history"].collidepoint(mouse_pos):
            self.show_stats_dialog = True
        
        # Recuperar simulación
        elif self.buttons["resume_sim"].collidepoint(mouse_pos):
            self.resume_simulation()
    
    def render(self):
        """Renderizar la interfaz incluyendo elementos de persistencia"""
        self.screen.fill((30, 30, 30))  # Fondo oscuro
        
        # Renderizar botones
        self.render_buttons()
        
        # Renderizar diálogos si están activos
        if self.show_save_dialog:
            self.render_save_dialog()
        
        if self.show_load_dialog:
            self.render_load_dialog()
        
        if self.show_stats_dialog:
            self.render_stats_dialog()
        
        pygame.display.flip()
    
    def render_buttons(self):
        """Renderizar los botones de persistencia"""
        font = pygame.font.Font(None, 24)
        
        button_texts = {
            "save_manual": "💾 Guardar",
            "load_manual": "📂 Cargar",
            "export_stats": "📊 Exportar CSV",
            "view_history": "📈 Historial",
            "resume_sim": "🔄 Recuperar"
        }
        
        for button_name, rect in self.buttons.items():
            # Detectar hover
            mouse_pos = pygame.mouse.get_pos()
            is_hover = rect.collidepoint(mouse_pos)
            
            # Color según estado
            color = (80, 150, 80) if is_hover else (60, 60, 60)
            
            # Dibujar botón
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            pygame.draw.rect(self.screen, (150, 150, 150), rect, 2, border_radius=5)
            
            # Texto del botón
            text = font.render(button_texts[button_name], True, (255, 255, 255))
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)
    
    def render_save_dialog(self):
        """Renderizar diálogo para guardar"""
        # Crear fondo semi-transparente
        overlay = pygame.Surface((800, 600))
        overlay.set_alpha(200)
        overlay.fill((20, 20, 20))
        self.screen.blit(overlay, (200, 100))
        
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        # Título
        title = font.render("Guardar Simulación", True, (255, 255, 255))
        self.screen.blit(title, (400, 150))
        
        # Instrucciones
        instruction = small_font.render("Ingrese nombre para el guardado:", True, (200, 200, 200))
        self.screen.blit(instruction, (250, 250))
        
        # Aquí iría un input box para el nombre
        # Por simplicidad, este ejemplo usa un nombre automático
        
        # Botones del diálogo
        save_button = pygame.Rect(350, 500, 150, 50)
        cancel_button = pygame.Rect(550, 500, 150, 50)
        
        pygame.draw.rect(self.screen, (60, 150, 60), save_button, border_radius=5)
        pygame.draw.rect(self.screen, (150, 60, 60), cancel_button, border_radius=5)
        
        save_text = small_font.render("Guardar", True, (255, 255, 255))
        cancel_text = small_font.render("Cancelar", True, (255, 255, 255))
        
        self.screen.blit(save_text, (save_button.centerx - 40, save_button.centery - 10))
        self.screen.blit(cancel_text, (cancel_button.centerx - 40, cancel_button.centery - 10))
        
        # Manejar clicks en botones del diálogo
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:
            if save_button.collidepoint(mouse_pos):
                self.save_manual()
                self.show_save_dialog = False
            elif cancel_button.collidepoint(mouse_pos):
                self.show_save_dialog = False
    
    def render_load_dialog(self):
        """Renderizar diálogo para cargar"""
        # Crear fondo
        overlay = pygame.Surface((800, 600))
        overlay.set_alpha(200)
        overlay.fill((20, 20, 20))
        self.screen.blit(overlay, (200, 100))
        
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 20)
        
        # Título
        title = font.render("Cargar Simulación", True, (255, 255, 255))
        self.screen.blit(title, (400, 150))
        
        # Listar guardados disponibles
        saves = self.engine.persistence.list_manual_saves()
        
        y_offset = 220
        for i, save in enumerate(saves[:8]):  # Mostrar primeros 8
            save_name = save['name']
            save_date = save['saved_at'][:10]  # Solo fecha
            
            text = f"{i+1}. {save_name} ({save_date})"
            save_text = small_font.render(text, True, (200, 200, 200))
            
            # Crear rectángulo clickeable
            save_rect = pygame.Rect(250, y_offset, 500, 30)
            
            # Highlight si está hover
            if save_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.screen, (60, 60, 80), save_rect)
                
                # Si se hace click, cargar ese guardado
                if pygame.mouse.get_pressed()[0]:
                    self.load_manual(save['filename'])
                    self.show_load_dialog = False
            
            self.screen.blit(save_text, (260, y_offset + 5))
            y_offset += 35
        
        # Botón cerrar
        close_button = pygame.Rect(450, 650, 100, 40)
        pygame.draw.rect(self.screen, (100, 100, 100), close_button, border_radius=5)
        close_text = small_font.render("Cerrar", True, (255, 255, 255))
        self.screen.blit(close_text, (close_button.centerx - 25, close_button.centery - 10))
        
        if close_button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            self.show_load_dialog = False
    
    def render_stats_dialog(self):
        """Renderizar diálogo de estadísticas"""
        # Crear fondo
        overlay = pygame.Surface((800, 600))
        overlay.set_alpha(200)
        overlay.fill((20, 20, 20))
        self.screen.blit(overlay, (200, 100))
        
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 22)
        
        # Título
        title = font.render("Historial de Simulaciones", True, (255, 255, 255))
        self.screen.blit(title, (350, 150))
        
        # Obtener resumen estadístico
        summary = self.engine.persistence.get_statistics_summary()
        
        # Mostrar estadísticas
        y_offset = 220
        stats_text = [
            f"Total de simulaciones: {summary.get('total_simulations', 0)}",
            f"Completadas: {summary.get('completed_simulations', 0)}",
            "",
            "Victorias:",
        ]
        
        # Agregar victorias por jugador
        wins = summary.get('wins_by_player', {})
        for player, count in wins.items():
            stats_text.append(f"  {player}: {count}")
        
        stats_text.extend([
            "",
            f"Duración promedio: {summary.get('average_duration_seconds', 0):.1f}s",
            f"Puntaje promedio P1: {summary.get('average_score_p1', 0):.0f}",
            f"Puntaje promedio P2: {summary.get('average_score_p2', 0):.0f}",
        ])
        
        for line in stats_text:
            text_surface = small_font.render(line, True, (200, 200, 200))
            self.screen.blit(text_surface, (300, y_offset))
            y_offset += 30
        
        # Botón cerrar
        close_button = pygame.Rect(450, 650, 100, 40)
        pygame.draw.rect(self.screen, (100, 100, 100), close_button, border_radius=5)
        close_text = small_font.render("Cerrar", True, (255, 255, 255))
        self.screen.blit(close_text, (close_button.centerx - 25, close_button.centery - 10))
        
        if close_button.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            self.show_stats_dialog = False
    
    # ====================================================================
    # Funciones de acción
    # ====================================================================
    
    def save_manual(self):
        """Guardar estado manualmente"""
        import datetime
        name = f"guardado_{datetime.datetime.now().strftime('%H%M%S')}"
        filepath = self.engine.save_manual_state(name, "Guardado desde UI")
        
        if filepath:
            print(f"✅ Guardado exitoso: {name}")
        else:
            print("❌ Error al guardar")
    
    def load_manual(self, filename):
        """Cargar guardado manual"""
        success = self.engine.load_manual_state(filename)
        
        if success:
            print(f"✅ Cargado exitoso: {filename}")
        else:
            print(f"❌ Error al cargar: {filename}")
    
    def export_statistics(self):
        """Exportar estadísticas a CSV"""
        if self.engine.state == "game_over":
            files = self.engine.export_statistics_csv()
            
            if files:
                print("✅ Estadísticas exportadas:")
                for key, filepath in files.items():
                    print(f"   {key}: {filepath}")
            else:
                print("❌ Error al exportar")
        else:
            # Exportar historial general
            filepath = self.engine.persistence.export_all_simulations_csv(limit=50)
            print(f"✅ Historial exportado: {filepath}")
    
    def resume_simulation(self):
        """Recuperar última simulación interrumpida"""
        state = self.engine.persistence.resume_last_simulation()
        
        if state:
            print("✅ Simulación recuperada exitosamente")
        else:
            print("ℹ️  No hay simulaciones para recuperar")


# ====================================================================
# Ejemplo de uso en rescue_simulator.py
# ====================================================================

def ejemplo_uso_en_main():
    """
    Ejemplo de cómo integrar en tu archivo rescue_simulator.py
    """
    
    pygame.init()
    screen = pygame.display.set_mode((1400, 800))
    pygame.display.set_caption("Rescue Simulator - Con Persistencia")
    
    engine = GameEngine()
    
    # Intentar recuperar simulación interrumpida
    state = engine.persistence.resume_last_simulation()
    if state:
        print("✅ Simulación anterior recuperada")
    else:
        # Si no hay nada que recuperar, iniciar nueva
        engine.init_game()
    
    # Usar la visualización extendida (o adaptar tu Visualization existente)
    view = VisualizationConPersistencia(screen, engine)
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        view.handle_events()
        engine.update()
        view.render()
        clock.tick(60)  # 60 FPS
    
    pygame.quit()


# ====================================================================
# Atajos de teclado sugeridos
# ====================================================================

def handle_keyboard_shortcuts(event, engine):
    """
    Ejemplo de atajos de teclado para funcionalidades de persistencia
    
    Agregar esto en el handle_events de tu Visualization
    """
    
    if event.type == pygame.KEYDOWN:
        # Ctrl+S: Guardar rápido
        if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            import datetime
            name = f"quick_save_{datetime.datetime.now().strftime('%H%M%S')}"
            engine.save_manual_state(name, "Guardado rápido")
            print(f"💾 Guardado rápido: {name}")
        
        # Ctrl+E: Exportar estadísticas
        elif event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
            if engine.state == "game_over":
                engine.export_statistics_csv()
                print("📊 Estadísticas exportadas")
        
        # Ctrl+H: Ver historial
        elif event.key == pygame.K_h and pygame.key.get_mods() & pygame.KMOD_CTRL:
            history = engine.persistence.get_simulation_history(limit=5)
            print("\n📈 ÚLTIMAS 5 SIMULACIONES:")
            for i, sim in enumerate(history, 1):
                print(f"{i}. {sim['winner']} - "
                      f"{sim['final_score_p1']} vs {sim['final_score_p2']}")
        
        # Ctrl+R: Recuperar simulación
        elif event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
            state = engine.persistence.resume_last_simulation()
            if state:
                print("✅ Simulación recuperada")
            else:
                print("ℹ️  No hay simulaciones para recuperar")


# ====================================================================
# NOTA IMPORTANTE
# ====================================================================
"""
Este archivo es solo un EJEMPLO de cómo integrar las funcionalidades
de persistencia en tu interfaz de usuario.

NO ES NECESARIO usar este código tal cual. Puedes:

1. Adaptar los botones a tu UI existente en visualization.py
2. Usar solo los atajos de teclado
3. Crear tu propia implementación

El sistema de persistencia ya está funcionando automáticamente en
GameEngine. Esta interfaz es solo para acceder a funcionalidades
adicionales como:
- Guardado manual
- Carga de guardados
- Exportación de estadísticas
- Ver historial

Para uso básico, el sistema funciona automáticamente sin necesidad
de modificar la UI.
"""

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "="*60)
    print("Este es un archivo de EJEMPLO - No ejecutar directamente")
    print("Ver código fuente para ejemplos de integración")
    print("="*60)

