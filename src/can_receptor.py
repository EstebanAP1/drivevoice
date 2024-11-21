import can
import logging

class CanReceptor:
    def __init__(self):
        self.bus = can.interface.Bus(interface='virtual')

    def decode_message(self, message):
        if message.arbitration_id == 0x18FEE200:  
            spn_1744 = message.data[0] & 0b00000011
            status = {
                0b00: "Puertas cerradas",
                0b01: "Puertas abiertas",
                0b10: "Error en el sistema de puertas",
                0b11: "Estado de puertas no disponible"
            }.get(spn_1744, "Estado desconocido")
            return status

        elif message.arbitration_id == 0x18FEF157:  
            exterior = "Luces exteriores encendidas" if message.data[0] & 0b01 else "Luces exteriores apagadas"
            interior = "Luces interiores encendidas" if (message.data[0] & 0b100) >> 2 else "Luces interiores apagadas"
            return f"{exterior}, {interior}"

        elif message.arbitration_id == 0x18EAFF00:  
            fuel_level = message.data[0] * 0.4  
            return f"Nivel de combustible: {fuel_level:.2f}%"

        elif message.arbitration_id == 0x18FEF200:  
            engine_status = "Motor encendido" if message.data[0] & 0b01 else "Motor apagado"
            return engine_status

        return f"Mensaje no reconocido (ID: {hex(message.arbitration_id)})"

    def receive(self):
        print("Esperando mensajes en el bus CAN...")
        while True:
            try:
                message = self.bus.recv(timeout=1.0)
                if message:
                    decoded_message = self.decode_message(message)
                    logging.info(f"Decodificación CAN: {decoded_message}")
            except can.CanError as e:
                logging.error(f"Error al recibir mensaje: {e}")
            except KeyboardInterrupt:
                print("Recepción interrumpida manualmente.")
                break
