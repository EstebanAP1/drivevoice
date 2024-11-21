import can

class CanSender:
    def __init__(self):
        self.bus = can.interface.Bus(channel='vcan0', bustype='socketcan')
        self.message = can.Message(arbitration_id=0x7de, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=False)
    
    @classmethod
    def send_message(self):
        self.bus.send(self.message)