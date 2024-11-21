import can

class CanSender:
    def __init__(self):
        self.bus = can.interface.Bus(interface='virtual')

    def send_message(self, arbitration_id, data):
        msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=True)
        try:
            self.bus.send(msg)
        except can.CanError as e:
            print(f"Error al enviar el mensaje: {e}")
        finally:
            self.bus.shutdown()

    def door_command(self, status: bool):
        spn_1744 = 0b01 if status else 0b00
        self.send_message(arbitration_id=0x18FEE200, data=[spn_1744, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    def lights_command(self, exterior: bool, interior: bool):
        byte_0 = (0b01 if exterior else 0b00) | ((0b01 if interior else 0b00) << 2)
        self.send_message(arbitration_id=0x18FEF157, data=[byte_0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    def fuel_level_request(self):
        self.send_message(arbitration_id=0x18EAFF00, data=[0xEC, 0xFF, 0xFE, 0x00, 0x00, 0x00, 0x00, 0x00])

    def engine_control(self, start: bool):
        spn_engine = 0b01 if start else 0b00
        self.send_message(arbitration_id=0x18FEEF00, data=[spn_engine, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
