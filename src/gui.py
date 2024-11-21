# gui.py
import pygame
import sys
from pygame.locals import *
from command_handler import CommandHandler

class GUI:
    def __init__(self):
        # Inicializar Pygame
        pygame.init()

        # Configuración de la pantalla
        self.screen = pygame.display.set_mode((1000, 700))
        pygame.display.set_caption("DriveVoice Control Panel")

        # Definir colores
        self.white = (246, 243, 236)  # Fondo blanco
        self.yellow = (252, 243, 0)   # Amarillo para indicar estado activo
        self.black = (0, 0, 0)

        # Obtener el estado inicial desde CommandHandler
        self.button_status = {
            "Luces de Cabina": CommandHandler.state["luces_cabina"],
            "Luces Exteriores": CommandHandler.state["luces_exteriores"],
            "Puerta": CommandHandler.state["puerta"],
            "Nivel de Combustible": CommandHandler.state["nivel_combustible"],
            "Motor": CommandHandler.state["motor"],
            # Añade otros estados si es necesario
        }

        heightBox = 250
        widthBox = 220
        # Definir las áreas de los botones
        self.buttons = {
            "Luces de Cabina": pygame.Rect(100, 50, widthBox, heightBox),
            "Luces Exteriores": pygame.Rect(400, 50, widthBox, heightBox),
            "Puerta": pygame.Rect(700, 50, widthBox, heightBox),
            "Nivel de Combustible": pygame.Rect(100, 350, widthBox, heightBox),
            "Motor": pygame.Rect(400, 350, widthBox, heightBox),
            # Añade otros botones si es necesario
        }

        # Cargar imágenes para los servicios
        self.images = {
            "Luces de Cabina": pygame.image.load('src/assets/luz_conductor.png'),
            "Luces Exteriores": pygame.image.load('src/assets/light_car.png'),
            "Puerta": pygame.image.load('src/assets/puerta-img.png'),
            "Nivel de Combustible": pygame.image.load('src/assets/level_fuel.png'),
            "Motor": pygame.image.load('src/assets/engine.png'),
            # Añade otras imágenes si es necesario
        }

        # Cargar imagen de fondo
        self.bg = pygame.image.load('src/assets/bg-interfaz-2.png')

        # Fuente para el texto
        self.fuente = pygame.font.Font(None, 25)

    # Dibujar los botones
    def draw_buttons(self):
        for boton, rect in self.buttons.items():
            color = self.yellow if self.button_status[boton] else self.white
            pygame.draw.rect(self.screen, color, rect)
            image = self.images[boton]
            self.screen.blit(image, (rect.x + 35, rect.y + 10))  # Dibujar la imagen del servicio
            if (boton == "Nivel de Combustible"):
                text_status = ""
            else:
                text_status = "Encendido" if self.button_status[boton] else "Apagado"
            text = self.fuente.render(f"{text_status}", True, self.black)
            self.screen.blit(text, (rect.x + 50, rect.y + 180))
            text_service = self.fuente.render(boton.replace('_', ' ').title(), True, self.black)
            self.screen.blit(text_service, (rect.x + 20, rect.y + 200))

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.screen.fill(self.white)
            self.screen.blit(self.bg, (0, 0))

            # Actualizar el estado de los botones desde CommandHandler
            self.update_button_status()

            # Dibujar botones
            self.draw_buttons()

            # Manejar eventos
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic izquierdo
                        for button, rect in self.buttons.items():
                            if rect.collidepoint(event.pos):
                                # Actualizar el estado y ejecutar el comando correspondiente
                                self.button_status[button] = not self.button_status[button]
                                self.execute_command_from_gui(button)

            pygame.display.update()
            clock.tick(60)  # Limitar a 60 FPS

    def update_button_status(self):
        # Actualizar el estado de los botones basándose en CommandHandler.state
        self.button_status["Luces de Cabina"] = CommandHandler.state["luces_cabina"]
        self.button_status["Luces Exteriores"] = CommandHandler.state["luces_exteriores"]
        self.button_status["Puerta"] = CommandHandler.state["puerta"]
        self.button_status["Nivel de Combustible"] = CommandHandler.state["nivel_combustible"]
        self.button_status["Motor"] = CommandHandler.state["motor"]
        # Actualiza otros estados si es necesario

    def execute_command_from_gui(self, button):
        # Mapear el botón a un comando de voz equivalente
        command_map = {
            "Luces de Cabina": "encender luces de cabina" if self.button_status[button] else "apagar luces de cabina",
            "Luces Exteriores": "encender luces exteriores" if self.button_status[button] else "apagar luces exteriores",
            "Puerta": "abrir puerta" if self.button_status[button] else "cerrar puerta",
            "Nivel de Combustible": "consultar nivel de combustible",
            "Motor": "encender motor" if self.button_status[button] else "apagar motor",
            # Añade otros mapeos si es necesario
        }
        command = command_map.get(button)
        if command:
            # Enviar el comando al CommandHandler
            CommandHandler.execute_command(command)
        else:
            print(f"No se encontró un comando para el botón {button}")
