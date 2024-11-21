import can
import logging

class CanSender:
    def __init__(self):
        self.bus = can.interface.Bus(interface='virtual')

    def send_message(self, arbitration_id, data):
        msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=True)
        try:
            self.bus.send(msg)
            logging.info(f"Mensaje enviado: ID={hex(arbitration_id)}, Datos={data}")
        except can.CanError as e:
            logging.error(f"Error al enviar el mensaje: {e}")
        finally:
            self.bus.shutdown()

    def door_command(self, status: bool):
        spn_1744 = 0b01 if status else 0b00
        data = [spn_1744] + [0x00] * 7  # Rellenar el resto con ceros
        self.send_message(arbitration_id=0x18FEE200, data=data)

    def lights_command(self, exterior: bool, interior: bool):
        byte_0 = (0b01 if exterior else 0b00) | ((0b01 if interior else 0b00) << 2)
        data = [byte_0] + [0x00] * 7  # Rellenar el resto con ceros
        self.send_message(arbitration_id=0x18FEF157, data=data)

    def fuel_level_request(self):
        data = [0xEC, 0xFF, 0xFE, 0x00, 0x00, 0x00, 0x00, 0x00]  # Solicitud para PGN 65276
        self.send_message(arbitration_id=0x18EAFF00, data=data)

    def engine_control(self, start: bool):
        spn_engine = 0b01 if start else 0b00
        data = [spn_engine] + [0x00] * 7  # Rellenar el resto con ceros
        self.send_message(arbitration_id=0x18FEF200, data=data)  # Ejemplo de ID para control del motor
