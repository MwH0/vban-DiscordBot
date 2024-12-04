<div align="center">

# VBAN-DiscordBot

• [Overview](#overview)
• [Commands](#commands)
• [Installation](#installation)
• [License](#license)

</div>

# Overview

VBAN-Discord Bot is a discord interface for controlling VBAN (VB-Audio Network) Protocol, built on top of discord.py. This bot is generally self hosted on a dedicated server (like Windows, Mac, Linux).  
[Installation](#installation) is simple, requiring NO coding knowledge! Once installed and updated, every aspect of the bot can be managed directly within Discord.

## VBAN

- [x] Receive audio with VBAN protocol
- [x] Send audio with VBAN protocol
- [x] List all VBAN Receivers/Senders
- [ ] Send Text to a VBAN Receiver
- [ ] Send and Receive audio from multiple VBAN Receivers/Senders
- [ ] Set the sample rate, channels, chunk size and baud rate of the bot

## Discord

- [ ] Broadcast audio to Discord Voice Channels
- [ ] Receive audio from Discord Voice Channels
- [ ] Broadcast Text to Discord Text Channels
- [ ] Auto play voice messages from Discord Text Channels
- [ ] Auto play voice messages from VBAN Text Messages

# Commands

| Commands | Function                         | State      |
|--------- | -------------------------------- | ---------- |
| !recv    | Create a Receiver Streams        | working    |
| !emit    | Create a Emitter Streams         | working    |
| !list    | List all Created Channel         | working    |
| !devs    | List audio devices               | removed    |
| !help    | List all Available  Command      | working    |

# Installation

1. Clone the repo
2. Create a VBAN bot in [developer portal](https://discord.com/developers/applications)
3. Paste the token inside the token.txt
4. Install Requirements
5. run bot.py


# License

Released under the [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.
