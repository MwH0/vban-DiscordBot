import discord
from discord import ui
from discord.ext import commands
from scr.pyVBAN import *

help_command = commands.DefaultHelpCommand(no_category="Commands")
intents = discord.Intents.default()
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=help_command)
streams = []
port = 6980

@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))

class Select(ui.Select):
    def __init__(self, devices):
        self.devices = devices
        options = [
            discord.SelectOption(label=device['name'], emoji=f"{i}\uFE0F\u20E3") 
            for i, device in enumerate(devices)  # Limit to the first 10 devices for emoji response
        ]
        super().__init__(placeholder="Select a device", max_values=1, min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_label = self.values[0]
        device_index = next(i for i, device in enumerate(self.devices) if device['name'] == selected_label)
        await interaction.response.send_message(f"Selected device: {selected_label} ", ephemeral=True)
        self.view.device_index = device_index
        self.view.stop()

class SelectView(ui.View):
    def __init__(self, devices, *, timeout=180):
        super().__init__(timeout=timeout)
        self.device_index = None
        self.add_item(Select(devices))

@bot.command()
async def recv(ctx, name, ip):
    """Creates an audio receiver stream."""
    devices = list_audio_devices(type="output")
    view = SelectView(devices)
    await ctx.send("Select an output device:", view=view)
    await view.wait()
    if view.device_index is not None:
        device = devices[view.device_index]['index']
        stream = ReceiverStream(ip, name, port, device)
        stream.start
        streams.append(stream)
        await ctx.send(f"VBAN Receiver created with device index {device}.")
    else:
        await ctx.send("No device was selected.")

@bot.command()
async def emit(ctx, name, ip):
    """Creates an audio emitter stream."""
    devices = list_audio_devices(type="input")
    view = SelectView(devices)
    await ctx.send("Select an output device:", view=view)
    await view.wait()  # Wait until the view interaction is finished
    if view.device_index is not None:
        device = devices[view.device_index]['index']
        stream = SenderStream(ip, name, port, device)
        stream.start
        streams.append(stream)
        await ctx.send(f"VBAN Receiver created with device index {device}.")
    else:
        await ctx.send("No device was selected.")


@bot.command()
async def list(ctx):
    """Lists all active streams."""
    if not streams:
        await ctx.send("No active streams.")
        return
    message = "Active Streams:\n"
    for stream in streams:
        # - Emitter: `Emitter1` (192.168.1.1:8080, running), Emitter2 (192.168.1.2:8081, stopped)
        message += f"- {'Receiver ' if stream == ReceiverStream else 'Emitter '}: `{stream.name}` ({stream.ip}:{stream.port} {'is running' if stream.running else 'has stopped'})\n"
    await ctx.send(message)

@bot.command()
async def txt(ctx, *, message: str):
    """Sends a text message to a selected stream."""
    if not streams:
        await ctx.send("No active streams to send a message to.")
        return

    message_text = "Select a stream:\n"
    for i, (name) in enumerate(streams.items()):
        if i < 10:
            message_text += f"{i}️⃣ `{name}`\n"
    msg = await ctx.send(message_text)
    for i in range(len(streams)):
        await msg.add_reaction(f"{i}️⃣")

    def check(reaction, user):
        return user == ctx.author and reaction.message.id == msg.id

    reaction, _ = await bot.wait_for("reaction_add", check=check)
    chosen_index = int(reaction.emoji[0])
    chosen_stream = list(streams.values())[chosen_index]

    chosen_stream.send(message.encode('utf-8'))
    await ctx.send(f"Message sent to stream `{list(streams.keys())[chosen_index]}`.")

@bot.command()
async def sys(ctx):
    """Shows a panel for system settings."""
    # This would involve creating a more complex UI or settings dialog.
    await ctx.send("System settings are not yet implemented.")
    
token = open("token.txt", "r").read()
bot.run(token)

