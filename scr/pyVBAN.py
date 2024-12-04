import logging
import time
import pyaudio
import pyvban
import threading

logging.basicConfig(level=logging.DEBUG)
class ReceiverStream(threading.Thread):
    def __init__(self, ip, name, port, device):
        super().__init__()
        self.running = True
        self.ip = ip
        self.name = name
        self.port = port
        self.device = device
        
    def run(self):
        stream = pyvban.utils.VBAN_Receiver(
            sender_ip=self.ip,
            stream_name=self.name,
            port=self.port,
            device_index=self.device
        )
        stream.run
        
    def stop(self):
        self.running = False
class SenderStream(threading.Thread):
    def __init__(self, ip, name, port, device, rate=48000, channels=2):
        super().__init__()
        self.running = True
        self.ip = ip
        self.name = name
        self.port = port
        self.device = device
        self.rate = rate
        self.channels = channels
        
    def run(self):
        stream = pyvban.utils.VBAN_Sender(
            sender_ip=self.ip,
            port=self.port,
            stream_name=self.name,
            sample_rate=self.rate,
            channels=self.channels,
            device_index=self.device
        )
        stream.run
        
    def stop(self):
        self.running = False
        
def list_audio_devices(type="all"):
    p = pyaudio.PyAudio()
    devices = []
    info = p.get_host_api_info_by_index(0)

    for i in range(info.get('deviceCount')):
        dev = p.get_device_info_by_host_api_device_index(0, i)
        max_input_channels = dev.get("maxInputChannels", 0)
        max_output_channels = dev.get("maxOutputChannels", 0)

        if type == "all" or (type == "input" and max_input_channels > 0) or (type == "output" and max_output_channels > 0):
            devices.append({
                "index": i,
                "name": dev.get("name")
            })
    return devices
