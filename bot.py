from scr.pyVBAN import *
import pyaudio
import socket
import discord
import threading
from discord.ext import commands

help_command = commands.DefaultHelpCommand(no_category="Commands")
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=help_command)
streams = []


def run(index):
    while streams[index].running:
        streams[index].runonce()
    streams[index].quit()


@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    else:
        await bot.process_commands(message)


@bot.command(help="list all streams")
async def list(ctx):
    for index, stream in enumerate(streams):
        stream = (
            "Index:"
            + str(index)
            + " Stream: "
            + stream.streamName
            + " IP: "
            + stream.ip
            + " Port: "
            + str(stream.port)
        )
        if type(stream) == VBAN_Recv:
            stream += (
                " DeviceIndex: "
                + str(stream.deviceIndex)
                + " Running: "
                + str(stream.running)
            )
        elif type(stream) == VBAN_Emit:
            stream += (
                " DeviceIndex: "
                + str(stream.deviceIndex)
                + " Sample Rate: "
                + str(stream.samprate)
                + " Running: "
                + str(stream.running)
            )
        elif type(stream) == VBAN_Text:
            stream += " BaudRate: " + str(stream.baudRate)
        else:
            await ctx.send("Error: Unknown stream type")
    if len(streams) == 0:
        stream = "No streams found. Use !recv or !send to add"
    await ctx.send(stream)


@bot.command(help="list bot ip address")
async def netls(ctx):
    netInfo = socket.gethostbyname_ex(socket.gethostname())
    netls = str(len(netInfo[2])) + " Network information - " + str(netInfo[0]) + "\n"
    for ip in netInfo[2]:
        if ip.split(".")[-1] == "1":
            netls += "Default Gateway - " + str(ip) + "\n"
        else:
            local_ip = str(ip)
            netls += "Local IP address - " + local_ip + "\n"
    await ctx.send(netls)


@bot.command(
    help="[*streamName] [*ip] [port] [deviceIndex] [verbose]: create a VBAN receiver"
)
async def recv(ctx, streamName, ip, port=6980, deviceIndex=0, verbose=False):
    receiver = VBAN_Recv(ip, int(port), streamName, deviceIndex, verbose)
    streams.append(receiver)
    recvThread = threading.Thread(target=run(len(streams) - 1))
    recvThread.start()
    await ctx.send("Added a VBAN receiver to index " + str(len(streams) - 1))


@bot.command(
    help="[*streamName] [*ip] [port] [deviceIndex] [verbose]: create a VBAN receiver"
)
async def emit(ctx, streamName, ip, port=6980, deviceIndex=0, verbose=False):
    emitter = VBAN_Emit(ip, port, streamName, sampRate, deviceIndex, verbose)
    streams.append(emitter)
    emitThread = threading.Thread(target=run(len(streams) - 1))
    emitThread.start()
    await ctx.send("Added a VBAN emitter to index " + str(len(streams) - 1))


@bot.command(help="[*streamName] [*ip] [port] [baudRate]: create a VBAN text sender")
async def text(ctx, streamName, ip, port=6980, baudRate=9600):
    textSender = VBAN_Text(ip, port, streamName, baudRate)
    await ctx.send("Added a VBAN textSender to index " + str(len(streams) - 1))
    VBAN_Text(ip, port, streamName, baudRate)


@bot.command(help="[*index] [*text]: sent a text with VBAN text sender")
async def sent(ctx, index, text):
    streams[int(index)].send(text)
    await ctx.send("Sent text to stream " + index)


@bot.command(help="[*index] [*streamName] [*ip] [*port] [DeviceIndex]: edit a stream")
async def edit(ctx, index, streamName, ip, port, DeviceIndex=0):
    if port == None and int(ip.split(":")[1]) != None:
        DeviceIndex = port
        port = int(ip.split(":")[1])
    elif port == None and int(ip.split(":")[1]) == None:
        port = streams[int(index)].port
    streams[int(index)].ip = ip
    streams[int(index)].port = port
    streams[int(index)].streamName = streamName
    if (
        type(streams[int(index)]) == VBAN_Recv or type(streams[int(index)]) == VBAN_Emit
    ) and (DeviceIndex != 0 and DeviceIndex != None):
        streams[int(index)].deviceIndex = DeviceIndex
    elif (
        type(streams[int(index)]) == VBAN_Emit
        and DeviceIndex != 0
        and DeviceIndex != None
    ):
        streams[int(index)].deviceIndex = DeviceIndex
    elif DeviceIndex != 0 and DeviceIndex != None:
        await ctx.send("Error: DeviceIndex only works on VBAN_Recv and VBAN_Emit")
    await ctx.send("Edited stream " + index)


@bot.command(help="[*index] [*streamName]: rename a stream")
async def rename(ctx, index, streamName):
    streams[int(index)].streamName = streamName
    await ctx.send("Renamed stream " + index)


@bot.command(help="[*index] [*ip] [port]: change the ip of a stream")
async def reip(ctx, index, ip, port):
    if port == None and int(ip.split(":")[1]) != None:
        port = int(ip.split(":")[1])
    elif port == None and int(ip.split(":")[1]) == None:
        port = streams[int(index)].port
    streams[int(index)].port = port
    streams[int(index)].ip = ip
    await ctx.send("Changed ip of stream " + index)


@bot.command(help="[*index]: toggle a stream")
async def toggle(ctx, index):
    if type(streams[int(index)]) == VBAN_Recv or type(streams[int(index)]) == VBAN_Emit:
        streams[int(index)].running = not streams[int(index)].running
    elif type(streams[int(index)]) == VBAN_Text:
        await ctx.send("Error: VBAN_Text does not support toggle")
    else:
        await ctx.send("Error: Unknown stream type")
    await ctx.send("Stopped stream " + index)


@bot.command(help="[*index]: delete a stream")
async def quit(ctx, index):
    streams[int(index)].quit()
    streams.pop(int(index))
    await ctx.send("Deleted stream " + index)


@bot.command(help="[*index]: toggle verbose mode")
async def verbose(ctx, index):
    if type(streams[int(index)]) == VBAN_Recv or type(streams[int(index)]) == VBAN_Emit:
        streams[int(index)].verbose = not streams[int(index)].verbose
    elif type(streams[int(index)]) == VBAN_Text:
        await ctx.send("Error: VBAN_Text does not support verbose mode")
    else:
        await ctx.send("Error: Unknown stream type")
    await ctx.send("Toggled verbose mode of stream " + index)


@bot.command(help="[*index] [*sampleRate]: change the sample rate of a stream")
async def sampRate(ctx, index, sampleRate):
    if type(streams[int(index)]) == VBAN_Recv or type(streams[int(index)]) == VBAN_Emit:
        streams[int(index)].samprate = sampleRate
    elif type(streams[int(index)]) == VBAN_Text:
        await ctx.send("Error: VBAN_Text does not support sample rate")
    else:
        await ctx.send("Error: Unknown stream type")
    await ctx.send("Changed sample rate of stream " + index)


@bot.command(help="list all output and input devices")
async def devls(ctx):
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get("deviceCount")
    devls = "--- INPUT DEVICES ---\n"
    for i in range(0, numdevices):
        if (
            p.get_device_info_by_host_api_device_index(0, i).get("maxInputChannels")
        ) > 0:
            devls += (
                "Input Device id "
                + str(i)
                + " - "
                + p.get_device_info_by_host_api_device_index(0, i).get("name")
                + "\n"
            )
    devls += "--- OUTPUT DEVICES ---\n"
    for i in range(0 + numdevices):
        if (
            p.get_device_info_by_host_api_device_index(0, i).get("maxOutputChannels")
        ) > 0:
            devls += (
                "Input Device id "
                + str(i)
                + " - "
                + p.get_device_info_by_host_api_device_index(0, i).get("name")
                + "\n"
            )
    await ctx.send(devls)


@bot.command(help="[*index] [*DeviceIndex]: change the output device of a stream")
async def outdev(ctx, index, DeviceIndex):
    if type(streams[int(index)]) == VBAN_Recv or type(streams[int(index)]) == VBAN_Emit:
        streams[int(index)].deviceIndex = DeviceIndex
    elif type(streams[int(index)]) == VBAN_Text:
        await ctx.send("Error: VBAN_Text does not support output device")
    else:
        await ctx.send("Error: Unknown stream type")
    await ctx.send("Changed output device of stream " + index)


@bot.command(help="[*index] [*DeviceIndex]: change the input device of a stream")
async def indev(ctx, index, DeviceIndex):
    if type(streams[int(index)]) == VBAN_Recv or type(streams[int(index)]) == VBAN_Emit:
        streams[int(index)].deviceIndex = DeviceIndex
    elif type(streams[int(index)]) == VBAN_Text:
        await ctx.send("Error: VBAN_Text does not support input device")
    else:
        await ctx.send("Error: Unknown stream type")
    await ctx.send("Changed input device of stream " + index)


@bot.command(help="[*ip] [port]: ping a stream")
async def ping(ctx, ip="0.0.0.0", port=6980):
    if port == None and int(ip.split(":")[1]) != None:
        port = int(ip.split(":")[1])
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((ip, port))
        await ctx.send(f"Ping {ip}:{port} successful")
        # Close the socket
        s.close()
    except:
        await ctx.send(f"Ping {ip}:{port} failed")


token = open("token.txt", "r").read()
bot.run(token)
