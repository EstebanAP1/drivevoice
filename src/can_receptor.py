import can

class CanReceptor:
  def __init__(self):
    self.bus = can.interface.Bus(channel='vcan0', interface='socketcan')
    self.can_data = None

    try:
      while True:
        self.receive()
    except:
      pass

  def parse_arbitration_id(self, arbitration_id):
    priority = (arbitration_id >> 26) & 0x07
    pgn = (arbitration_id >> 8) & 0xFFF
    sa = arbitration_id & 0xFF
    return priority, pgn, sa
  
  def receive(self):
    message = self.bus.recv()

    if message is not None and message.arbitration_id:
      resposne = self.get_can_data()
      print(f"Data received: {resposne}")
  

  def get_can_data(self):
    if self.can_data is None:
      return None

    priority, pgn, sa = self.parse_arbitration_id(self.can_data['arbitration_id'])

    return {
      'timestamp': self.can_data['timestamp'],
      'priority': priority,
      'pgn': pgn,
      'sa': sa,
      'data': self.can_data['data']
    }
  
  def close(self):
    self.bus.shutdown()