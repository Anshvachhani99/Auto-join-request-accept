# @ChannelActionsBot
# (c) @xditya.

import contextlib
import re
import logging

from aioredis import Redis
from decouple import config
from telethon import TelegramClient, events, Button, types, functions, errors

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s"
)
log = logging.getLogger("ChannelActions")
log.info("\n\nStarting...\n")

log_grp = -1001759679892 #Add your id
try:
    bot_token = config("BOT_TOKEN")
    REDIS_URI = config("REDIS_URI")
    REDIS_PASSWORD = config("REDIS_PASSWORD")
    AUTH = [int(i) for i in config("OWNERS").split(" ")]
except Exception as e:
    log.exception(e)
    exit(1)

# connecting the client
try:
    bot = TelegramClient(None, 6, "eb06d4abfb49dc3eeb1aeb98ae0f581e").start(
        bot_token=bot_token
    )
except Exception as e:
    log.exception(e)
    exit(1)

REDIS_URI = REDIS_URI.split(":")
db = Redis(
    host=REDIS_URI[0],
    port=REDIS_URI[1],
    password=REDIS_PASSWORD,
    decode_responses=True,
)

# users to db
def str_to_list(text):  # Returns List
    return text.split(" ")


def list_to_str(list):  # Returns String  # sourcery skip: avoid-builtin-shadow
    str = "".join(f"{x} " for x in list)
    return str.strip()


async def is_added(var, id):  # Take int or str with numbers only , Returns Boolean
    if not str(id).isdigit():
        return False
    users = await get_all(var)
    return str(id) in users


async def add_to_db(var, id):  # Take int or str with numbers only , Returns Boolean
    # sourcery skip: avoid-builtin-shadow
    id = str(id)
    if not id.isdigit():
        return False
    try:
        users = await get_all(var)
        users.append(id)
        await db.set(var, list_to_str(users))
        return True
    except Exception as e:
        return False

async def is_user_exist(self, id):
    user = await self.col.find_one({'id':int(id)})
    return bool(user)


async def get_all(var):  # Returns List
    users = await db.get(var)
    return [""] if users is None or users == "" else str_to_list(users)


async def get_me():
    me = await bot.get_me()
    myname = me.username
    return f"@{myname}"


bot_username = bot.loop.run_until_complete(get_me())
start_msg = """**👾 Welcome to the bot**

**Add This Bot To Your Channel To Accept Join Requests Automatically 😊**"""


start_buttons = [
     [Button.url(" 💜 Add Me To Your Channel 💜", "t.me/Accept_Request_Joinbot?startgroup=true")],
     [Button.url("💝 Join support Channel", "https://t.me/+S6z5Tuj8TTM4N2Jl")],
]
start_buttons = [[
      Button.url("💝 Join support Channel", "https://t.me/+S6z5Tuj8TTM4N2Jl")
 ], [
      Button.inline("💚 Help 💚", data="helper"),
      Button.inline("🌀 About 🌀", data="Ansh")
], ]

@bot.on(events.NewMessage(incoming=True, pattern=f"^/start({bot_username})?$"))
async def starters(event):
    from_ = await bot.get_entity(event.sender_id)
    await event.reply(
        start_msg.format(user=from_.first_name), 
       
        buttons=start_buttons,
        link_preview=False,
    )
    
    if not (await is_added("BOTUSERS", event.sender_id)):
        await add_to_db("BOTUSERS", event.sender_id)
        await bot.send_message(log_grp,f"#**NewUser 🔻**\n\n**ID-->{from_.first_name}**\**Name-->{from_.id}**"), 


@bot.on(events.CallbackQuery(data="start"))
async def start_in(event):
    from_ = await bot.get_entity(event.sender_id)
    with contextlib.suppress(errors.rpcerrorlist.MessageNotModifiedError):
        await event.edit(
            start_msg.format(
                user=from_.first_name,
                user_id=event.from_.id,
                id=event.from_.id),
            buttons=start_buttons,
            link_preview=False,
        )


@bot.on(events.CallbackQuery(data="helper"))
async def helper(event):
    await event.edit(
        '**For add channel, follow this instruction:**\n\n\n\n**⍟ Add bot to your channel and make him administrator permissions**\n\n**⍟ Forward any message from channel to bot**\n\n**⍟ Customize Welcome message and work this bot.**',
        buttons = [
            [Button.url('💜 Add Me To Your Channel 💜', url='t.me/Accept_Request_Joinbot?startgroup=true')],
            [Button.inline('Back to Home 🏠', data='start')]
        ]
    )

@bot.on(events.CallbackQuery(data="Ansh"))
async def Ansh(event):
    await event.edit(
        '**╭─────────ᴀʙᴏᴜᴛ────────〄**\n│\n**├✯ My Name : [Accept Join Requests](https://t.me/Accept_Request_Joinbot)**\n**│**\n**├ ✯ Owner : [『Lêɠêɳ̃dẞογ࿐』 ꯭[🇮🇳]꯭](https://t.me/Legend_BoyCC)**\n**│**\n**├✯ Library : [Pyrogram](github.com/pyrogram)**\n**│**\n**├ ✯ Language : [Python](www.python.org/)**\n**│**\n**├✯ Build Status : V3.0.1**\n**│\n**├✯ Support Channel 💜 : [Supprot Channel](https://t.me/+S6z5Tuj8TTM4N2Jl)**\n**│\n**╰─────────ᴄʟᴏsᴇ─────────〄**', 
        buttons=Button.inline("Back to Home 🏠", data="start"),
    ) 
        
        
@bot.on(events.NewMessage(incoming=True, func=lambda e: e.is_private and e.fwd_from))
async def settings_selctor(event):  # sourcery skip: avoid-builtin-shadow
    id = event.fwd_from.from_id
    if not isinstance(id, types.PeerChannel):
        await event.reply("Looks like this isn't from a channel!")
        return
    try:
        chat = await bot.get_entity(id)
        if chat.admin_rights is None:
            await event.reply("**Seems like I'm not admin in this channel!**")
            return
    except ValueError:
        await event.reply("Seems like you haven't added me to your channel!")
        return

    # check if the guy trying to change settings is an admin

    try:
        who_u = (
            await bot(
                functions.channels.GetParticipantRequest(
                    channel=chat.id,
                    participant=event.sender_id,
                )
            )
        ).participant
    except errors.rpcerrorlist.UserNotParticipantError:
        await event.reply(
            "**You are not in the channel, or an admin, to perform this action.**"
        )
        return
    if not (
        isinstance(
            who_u, (types.ChannelParticipantCreator, types.ChannelParticipantAdmin)
        )
    ):
        await event.reply(
            "**You are not an admin of this channel and cannot change it's settings!**"
        )
        return

    added_chats = await db.get("CHAT_SETTINGS") or "{}"
    added_chats = eval(added_chats)
    welcome_msg = eval(await db.get("WELCOME_MSG") or "{}")
    is_modded = bool(welcome_msg.get(chat.id))
    setting = added_chats.get(str(chat.id)) or "Auto-Approve"
    await event.reply(
        "**Settings for {title}**\n\n__Select what to do on new join requests:__\n**Current setting** - __{set}__\n\n__Set your welcome message:__\nCurrently modified: {is_modded}".format(
            title=chat.title, set=setting, is_modded=is_modded
        ),
        buttons=[
            [Button.inline("Auto-Approve", data=f"set_ap_{chat.id}")],
            [Button.inline("Auto-Disapprove", data=f"set_disap_{chat.id}")],
            [Button.inline("Set Welcome Message", data=f"mod_{chat.id}")],
        ],
    )


@bot.on(events.CallbackQuery(data=re.compile("set_(.*)")))
async def settings(event):
    args = event.pattern_match.group(1).decode("utf-8")
    setting, chat = args.split("_")
    added_chats = await db.get("CHAT_SETTINGS") or "{}"
    added_chats = eval(added_chats)
    if setting == "ap":
        op = "Auto-Approve"
        added_chats.update({chat: op})
    elif setting == "disap":
        op = "Auto-Disapprove"
        added_chats.update({chat: op})
    await db.set("CHAT_SETTINGS", str(added_chats))
    await event.edit(
        f"**Settings updated! New members in the channel `{chat}` will be {op}d!**"
    )


@bot.on(events.CallbackQuery(data=re.compile("mod_(.*)")))
async def mod_welcome(event):
    args = int(event.pattern_match.group(1).decode("utf-8"))
    welcome_msg = eval(await db.get("WELCOME_MSG") or "{}")
    await event.delete()
    async with bot.conversation(event.sender_id) as conv:
        await conv.send_message(
            "**Send the new welcome message you want to be sent to a user when he is approved into your channel.\nAvailable formattings:\n- {name} - users name.\n- {chat} - chat title.**",
            buttons=Button.force_reply(),
        )
        msg = await conv.get_reply()
        if not msg.text:
            await event.reply("**You can only set a text message!**")
            return
        msg = msg.text
        welcome_msg.update({args: msg})
        await db.set("WELCOME_MSG", str(welcome_msg))
        chat = await bot.get_entity(args)
        await conv.send_message(
            f"**Welcome message for {chat.title} has been successfully set!✅**"
        )


@bot.on(events.Raw(types.UpdateBotChatInviteRequester))
async def approver(event):
    chat = event.peer.channel_id
    chat_settings = await db.get("CHAT_SETTINGS") or "{}"
    chat_settings = eval(chat_settings)
    welcome_msg = eval(await db.get("WELCOME_MSG") or "{}")
    chat_welcome = (
        welcome_msg.get(chat)
        or "**🌀 Power By --> @All_Hindi_TV_Serials_2**"
    )
    chat_welcome += "\n**How To Use This Bot Check Channel🔻**"  # \n\n__**Powered by 💝 Join Request Accept 💝**__"
    who = await bot.get_entity(event.user_id)
    chat_ = await bot.get_entity(chat)
    dn = "approved!"
    appr = True
    if chat_settings.get(str(chat)) == "Auto-Approve":
        appr = True
        dn = "approved!"
    elif chat_settings.get(str(chat)) == "Auto-Disapprove":
        appr = False
        dn = "disapproved :("
    with contextlib.suppress(
        errors.rpcerrorlist.UserIsBlockedError, errors.rpcerrorlist.PeerIdInvalidError
    ):
        await bot.send_message(
            event.user_id,
            chat_welcome.format(name=who.first_name, chat=chat_.title, dn=dn),
            buttons=Button.url("💝 Join Request Accept Support  💝", url="https://t.me/+S6z5Tuj8TTM4N2Jl"),
        )
    with contextlib.suppress(errors.rpcerrorlist.UserAlreadyParticipantError):
        await bot(
            functions.messages.HideChatJoinRequestRequest(
                approved=appr, peer=chat, user_id=event.user_id
            )
        )


@bot.on(events.NewMessage(incoming=True, from_users=AUTH, pattern="^/stats$"))
async def auth_(event):
    xx = await event.reply("Calculating...")
    t = await db.get("CHAT_SETTINGS") or "{}"
    t = eval(t)
    await xx.edit(
        "**💝 Join Request Accept 💝 Stats**\n\n**Users: {}\nGroups added (with modified settings): {}**".format(
            len(await get_all("BOTUSERS")), len(t.keys())
        )
    )


@bot.on(events.NewMessage(incoming=True, from_users=AUTH, pattern="^/broadcast$"))
async def broad(e):
    if not e.reply_to_msg_id:
        return await e.reply(
            "Please use `/broadcast` as reply to the message you want to broadcast."
        )
    msg = await e.get_reply_message()
    xx = await e.reply("In progress...")
    users = await get_all("BOTUSERS")
    done = error = 0
    for i in users:
        try:
            await bot.send_message(
                int(i),
                msg.text,
                file=msg.media,
                buttons=msg.buttons,
                link_preview=False,
            )
            done += 1
        except Exception:
            error += 1
    await xx.edit("Broadcast completed.\nSuccess: {}\nFailed: {}".format(done, error))


log.info("Started Bot - %s", bot_username)
log.info("\n@BotzHub\n\nBy - Ansh Vachhani.")

bot.run_until_disconnected()
