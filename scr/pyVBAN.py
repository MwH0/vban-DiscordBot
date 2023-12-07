import socket
import struct
import pyaudio


class VBAN_Recv(object):
    """docstring for VBAN_Recv"""

    def __init__(self, ip, streamName, port, deviceIndex, verbose=False):
        super(VBAN_Recv, self).__init__()
        self.streamName = streamName
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sampRate = 48000
        self.channels = 2
        self.deviceIndex = deviceIndex
        self.stream_magicString = ""
        self.stream_sampRate = 0
        self.stream_sampNum = 0
        self.stream_chanNum = 0
        self.stream_dataFormat = 0
        self.stream_streamName = ""
        self.stream_frameCounter = 0
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.p.get_format_from_width(2),
            channels=self.channels,
            rate=self.sampRate,
            output=True,
            output_device_index=self.deviceIndex,
        )
        self.rawPcm = None
        self.running = True
        self.verbose = verbose
        self.rawData = None
        self.subprotocol = 0
        self.const_VBAN_SRList = []
        for i in range(0, 7):
            self.const_VBAN_SRList.append(6000 * 2**i)
            self.const_VBAN_SRList.append(8000 * 2**i)
            self.const_VBAN_SRList.append(11025 * 2**i)
        print("pyVBAN-Recv Started")

    def _correctPyAudioStream(self):
        self.channels = self.stream_chanNum
        self.sampRate = self.stream_sampRate
        self.stream.close()
        self.stream = self.p.open(
            format=self.p.get_format_from_width(2),
            channels=self.channels,
            rate=self.sampRate,
            output=True,
            output_device_index=self.deviceIndex,
        )

    def _cutAtNullByte(self, stri):
        return stri.decode("utf-8").split("\x00")[0]

    def _parseHeader(self, data):
        self.stream_magicString = data[0:4].decode("utf-8")
        sampRateIndex = data[4] & 0x1F
        self.subprotocol = (data[4] & 0xE0) >> 5
        self.stream_sampRate = self.const_VBAN_SRList[sampRateIndex]
        self.stream_sampNum = data[5] + 1
        self.stream_chanNum = data[6] + 1
        self.stream_dataFormat = data[7]
        self.stream_streamName = self._cutAtNullByte(
            b"".join(struct.unpack("cccccccccccccccc", data[8:24]))
        )
        self.stream_frameCounter = struct.unpack("<L", data[24:28])[0]

    def runonce(self):
        if self.stream == None:
            print("Quit has been called")
            return
        self.sock.bind(("0.0.0.0", self.port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        data, addr = self.sock.recvfrom(
            2048
        )  # buffer size is normally 1436 bytes Max size for vban
        self.rawData = data
        self._parseHeader(data)
        if self.verbose:
            print(
                "R"
                + self.stream_magicString
                + " "
                + str(self.stream_sampRate)
                + "Hz "
                + str(self.stream_sampNum)
                + "samp "
                + str(self.stream_chanNum)
                + "chan Format:"
                + str(self.stream_dataFormat)
                + " Name:"
                + self.stream_streamName
                + " Frame:"
                + str(self.stream_frameCounter)
            )
        self.rawPcm = data[28:]  # Header stops a 28
        if self.stream_magicString == "VBAN" and self.subprotocol == 0:
            if not self.stream_streamName == self.streamName:
                return
            if not addr[0] == self.ip:
                return
            if (
                self.channels != self.stream_chanNum
                or self.sampRate != self.stream_sampRate
            ):
                self._correctPyAudioStream()
            self.stream.write(self.rawPcm)

    def quit(self):
        self.running = False
        self.stream.close()
        self.stream = None


class VBAN_Emit(object):
    """docstring for VBAN_Emit"""

    def __init__(self, ip, port, streamName, sampRate, deviceIndex, verbose=False):
        super(VBAN_Emit, self).__init__()
        self.ip = ip
        self.port = port
        self.streamName = streamName
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.connect((self.ip, self.port))
        self.p = pyaudio.PyAudio()
        self.channels = min(
            [
                self.p.get_device_info_by_host_api_device_index(0, deviceIndex).get(
                    "maxInputChannels"
                ),
                2,
            ]
        )
        self.samprate = 48000
        self.deviceIndex = deviceIndex
        self.chunkSize = 256
        self.stream = self.p.open(
            format=self.p.get_format_from_width(2),
            channels=self.channels,
            rate=self.samprate,
            input=True,
            input_device_index=self.deviceIndex,
            frames_per_buffer=self.chunkSize,
        )

        self.framecounter = 0
        self.running = True
        self.verbose = verbose
        self.rawPcm = None
        self.rawData = None
        self.const_VBAN_SRList = []
        for i in range(0, 7):
            self.const_VBAN_SRList.append(6000 * 2**i)
            self.const_VBAN_SRList.append(8000 * 2**i)
            self.const_VBAN_SRList.append(11025 * 2**i)

    def _constructFrame(self, pcmData):
        header = b"VBAN"
        header += bytes([self.const_VBAN_SR.index(self.samprate)])
        header += bytes([self.chunkSize - 1])
        header += bytes([self.channels - 1])
        header += b"\x01"  # VBAN_CODEC_PCM
        header += bytes(self.streamName + "\x00" * (16 - len(self.streamName)), "utf-8")
        header += struct.pack("<L", self.framecounter)
        if self.verbose:
            print(
                "SVBAN "
                + str(self.samprate)
                + "Hz "
                + str(self.chunkSize)
                + "samp "
                + str(self.channels)
                + "chan Format:1 Name:"
                + self.streamName
                + " Frame:"
                + str(self.framecounter)
            )
        return header + pcmData

    def runonce(self):
        try:
            self.framecounter += 1
            self.rawPcm = self.stream.read(self.chunkSize)
            self.rawData = self._constructFrame(self.rawPcm)
            self.sock.sendto(self.rawData, (self.ip, self.port))
        except Exception as e:
            print(e)

    def quit(self):
        self.running = False
        self.stream.close()
        self.stream = None


class VBAN_Text(object):
    """docstring for VBAN_Text"""

    def __init__(self, ip, port, baudRate, streamName):
        super(VBAN_Text, self).__init__()
        self.ip = ip
        self.port = port
        self.streamName = streamName
        self.baudRate = baudRate
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.connect((self.ip, self.port))
        self.VBAN_BPSList = [
            0,
            110,
            150,
            300,
            600,
            1200,
            2400,
            4800,
            9600,
            14400,
            19200,
            31250,
            38400,
            57600,
            115200,
            128000,
            230400,
            250000,
            256000,
            460800,
            921600,
            1000000,
            1500000,
            2000000,
            3000000,
        ]
        self.framecounter = 0

    def _constructFrame(self, text):
        header = b"VBAN"
        header += bytes([int("0b01000000", 2) + self.VBAN_BPSList.index(self.baudRate)])
        header += b"\x00"
        header += b"\x00"  # Channel indent 0 by default
        header += bytes([int("0b00010000", 2)])  # UTF8
        header += bytes(self.streamName + "\x00" * (16 - len(self.streamName)), "utf-8")
        header += struct.pack("<L", self.framecounter)
        return header + bytes(text, "utf-8")

    def send(self, text):
        try:
            self.framecounter += 1
            self.rawData = self._constructFrame(text)
            self.sock.sendto(self.rawData, (self.ip, self.port))
        except Exception as e:
            print(e)
