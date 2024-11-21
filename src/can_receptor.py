import logging
import can

class CanReceptor:
    def __init__(self):
        self.bus = can.interface.Bus(interface='virtual')

    def decode_message(self, message):
        if message.arbitration_id == 0x18FEE200:  # PGN 65282 (Door Control)
            spn_1744 = message.data[0] & 0b00000011
            if spn_1744 == 0b00:
                return "Puertas cerradas"
            elif spn_1744 == 0b01:
                return "Puertas abiertas"
            elif spn_1744 == 0b10:
                return "Error en el sistema de puertas"
            elif spn_1744 == 0b11:
                return "Estado de puertas no disponible"
        elif message.arbitration_id == 0x18FEF157:  # PGN 65271 (Light Control)
            exterior = "Luces exteriores encendidas" if message.data[0] & 0b01 else "Luces exteriores apagadas"
            interior = "Luces interiores encendidas" if (message.data[0] & 0b10) >> 1 else "Luces interiores apagadas"
            return f"{exterior}, {interior}"
        elif message.arbitration_id == 0x18FEEF00:  # PGN 65263 (Fuel Level)
            fuel_level = message.data[0] * 0.4  # Ejemplo: factor de escala
            return f"Nivel de combustible: {fuel_level:.2f}%"
        elif message.arbitration_id == 0x18FEEF00:  # Motor Control (start/stop)
            engine_status = "Motor encendido" if message.data[0] & 0b01 else "Motor apagado"
            return engine_status
        else:
            return "Mensaje no reconocido"

    def receive(self):
        print("Esperando mensajes en el bus CAN...")
        while True:
            try:
                message = self.bus.recv(timeout=1.0)
                if message:
                    decoded_message = self.decode_message(message)
                    logging.info(f"Decodificación CAN: {decoded_message}")
            except can.CanError as e:
                print(f"Error al recibir mensaje: {e}")
            except KeyboardInterrupt:
                print("Recepción interrumpida manualmente.")
                break
