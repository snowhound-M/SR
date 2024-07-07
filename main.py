from telethon import events, Button
import os, datetime, sys, time, asyncio, json, math, cv2, logging, subprocess, re
from pyrogram import Client, filters, errors
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid
from pyrogram.errors import PeerIdInvalid, UserNotParticipant, FloodWait
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from telethon.tl.types import DocumentAttributeVideo
from pyrogram.types import Message
from decouple import config
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest


logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

# variables
API_ID = config("API_ID", cast=int)
API_HASH = config("API_HASH")
BOT_TOKEN = config("BOT_TOKEN")
SESSION = config("SESSION")
FORCESUB = config("FORCESUB")
AUTHS = config("AUTH")

TDrone = TelegramClient('TDrone', API_ID, API_HASH).start(bot_token=BOT_TOKEN) 

userbot = Client("saverestricted", session_string=SESSION, api_hash=API_HASH, api_id=API_ID) 

try:
    userbot.start()
except BaseException:
    print("Userbot Error ! Have you added SESSION while deploying??")
    sys.exit(1)

PBot = Client(
    "SaveRestricted",
    bot_token=BOT_TOKEN,
    api_id=int(API_ID),
    api_hash=API_HASH
)    

try:
    PBot.start()
except Exception as e:
    print(e)
    sys.exit(1)


S = '/' + 's' + 't' + 'a' + 'r' + 't'
B = '/' + 'b' + 'a' + 't' + 'c' + 'h'
batch = []
fs = FORCESUB
ft = f"To use this bot you've to join @{fs}."
FINISHED_PROGRESS_STR = "🟩"
UN_FINISHED_PROGRESS_STR = "⬜"
DOWNLOAD_LOCATION = "/app"

@PBot.on_callback_query()
async def c_back(pbot, query):
   data = query.data
   if data == "set":
      await pbot.delete_messages(query.message.chat.id, query.message.id)
      async with TDrone.conversation(query.from_user.id) as conv: 
        xx = await conv.send_message("Send me any image for thumbnail as a reply to this message.")
        try:
            x = await conv.get_reply()
        except Exception as e:
            await xx.delete()
            await conv.send_message("Cannot wait more longer for your response!")
            return conv.cancel()
        if not x.media:
            xx.edit("No media found.")
        mime = x.file.mime_type
        if not 'png' in mime:
            if not 'jpg' in mime:
                if not 'jpeg' in mime:
                    return await xx.edit("No image found.")
        await xx.delete()
        t = await pbot.send_message(query.from_user.id, 'Trying.')
        
        path = await TDrone.download_media(x.media)
        if os.path.exists(f'{query.from_user.id}.jpg'):
            os.remove(f'{query.from_user.id}.jpg')
        os.rename(path, f'./{query.from_user.id}.jpg')
        await t.edit("Temporary thumbnail saved!")

   elif data == "rem":
      try:
        os.remove(f'{query.from_user.id}.jpg')
        await query.message.edit('Removed!')
      except Exception:
        await query.message.edit("No thumbnail saved.")
                                
  
@PBot.on_message(filters.incoming & filters.regex(f"{S}"))
async def start(pbot, cmd):
       user_nam = cmd.from_user.mention
       text = f"Hello {user_nam}\n\nSend me Link of any message to clone it here. If asked, send invite link.\n\nPublic Channels, Private Channels and Private Groups are allowed only."
       await start_srb(cmd, text)

def thumbnail(sender):
    if os.path.exists(f'{sender}.jpg'):
        return f'{sender}.jpg'
    else:
         return None

async def get_msg(userbot, client, tdrone, sender, edit_id, msg_link, i):
    
    """ userbot: PyrogramUserBot
    client: PyrogramBotClient
    tdrone: TelethonBotClient """
    
    edit = ""
    chat = ""
    round_message = False
    has_single_param = "?single" in msg_link
    if "?single" in msg_link:
        msg_link = msg_link.split("?single")[0]
    msg_id = int(msg_link.split("/")[-1]) + int(i)
    height, width, duration, thumb_path = 90, 90, 0, None
    if 't.me/c/' in msg_link:
        d = str(msg_link.split("/")[-2])
        chat = int('-100' + str(msg_link.split("/")[-2]))

        file = ""
        try:
            msg = await userbot.get_messages(chat, msg_id)
            if msg.media:
                if msg.media==MessageMediaType.WEB_PAGE:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await edit.delete()
                    await client.send_message(sender, msg.text.markdown)
                    return
            if not msg.media:
                if msg.text:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await edit.delete()
                    await client.send_message(sender, msg.text.markdown)
                    return
            edit = await client.edit_message_text(sender, edit_id, "Trying to Download.")
            file = await userbot.download_media(
                msg,
                progress=progress_for_pyrogram,
                progress_args=(
                    client,
                    "DOWNLOADING:\n",
                    edit,
                    time.time())
                )
            print(file)
            await edit.edit('Preparing to Upload!')
            caption = None
            if msg.caption is not None:
                caption = msg.caption.markdown
            if msg.media==MessageMediaType.VIDEO_NOTE:
                round_message = True
                data = video_metadata(file)
                height, width, duration = data["height"], data["width"], data["duration"]
                try:
                    thumb_path = await screenshot(file, duration, sender)
                except Exception:
                    thumb_path = None
                    
                await client.send_video_note(
                    chat_id=sender,
                    video_note=file,
                    length=height, duration=duration, 
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        'UPLOADING:\n',
                        edit,
                        time.time()
                    )
                )
            elif msg.media==MessageMediaType.VIDEO and msg.video.mime_type in ["video/mp4", "video/x-matroska"]:
                data = video_metadata(file)
                height, width, duration = data["height"], data["width"], msg.video.duration
                try:
                    thumb_path = await screenshot(file, duration, sender)
                except Exception:
                    thumb_path = None
                await client.send_video(
                    chat_id=sender,
                    video=file,
                    caption=caption,
                    supports_streaming=True,
                    height=height, width=width, duration=duration, 
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        'UPLOADING:\n',
                        edit,
                        time.time()
                    )
                )
            elif msg.media==MessageMediaType.PHOTO:
                await edit.edit("Uploading photo.")
                await client.send_photo(chat_id=sender, photo=file, caption=caption)
            else:
                thumb_path=thumbnail(sender)
                await client.send_document(
                    sender,
                    file, 
                    caption=caption,
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        'UPLOADING:\n',
                        edit,
                        time.time()
                    )
                )
            # try:
            # os.remove(file)
            # if os.path.isfile(file) == True:
            # os.remove(file)
            # except Exception:
            # pass
            # await edit.delete()
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await client.edit_message_text(sender, edit_id, "Have you joined the channel?\nSend me the invite link first.")
            return
        except PeerIdInvalid:
            print("PeerIdInvalid issue occurred.")
            return
        except Exception as e:
            print(e)
            pass 
        try:
            os.remove(file)
            if os.path.isfile(file) == True:
                os.remove(file)
        except Exception:
            pass
        await edit.delete()
    else:
        edit = await client.edit_message_text(sender, edit_id, "Cloning.")
        chat =  msg_link.split("/")[-2]
        msg = await userbot.get_messages(chat, msg_id)
        if type(sender) == str:
            var = True  # 'sender' is a string
        else:
            var = False  # 'sender' is not a string
        if msg.caption:
            mt_text = msg.caption.markdown
            await client.copy_message(sender, chat, msg_id, mt_text)
        else:
            mt_text = msg.text.markdown
            await client.send_message(sender, mt_text)
        await edit.delete()
        
async def get_bulk_msg(userbot, client, sender, msg_link, i):
    x = await client.send_message(sender, "Processing!")
    await get_msg(userbot, client, TDrone, sender, x.id, msg_link, i)


async def progress_for_pyrogram(
    current,
    total,
    client,
    ud_type,
    message,
    start
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        status = DOWNLOAD_LOCATION + "/status.json"
        if os.path.exists(status):
            with open(status, "r+") as f:
                statusMsg = json.load(f)
                if not statusMsg["running"]:
                    client.stop_transmission()
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] | {2}%\n\n".format(
            ''.join([FINISHED_PROGRESS_STR for i in range(math.floor(percentage / 10))]),
            ''.join([UN_FINISHED_PROGRESS_STR for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2))

        tmp = progress + "**GROSS:** `{0} of {1}`\n\n**Speed:** `{2}/s`\n\n**ETA:** `{3}`\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            if not message.photo:
                await message.edit_text(
                    text="{}\n {}".format(
                        ud_type,
                        tmp
                    )
                )
            else:
                await message.edit_caption(
                    caption="{}\n {}".format(
                        ud_type,
                        tmp
                    )
                )
        except:
            pass

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2]

#Join private chat-------------------------------------------------------------------------------------------------------------

async def join(client, invite_link):
    try:
        await client.join_chat(invite_link)
        return "Successfully joined the Channel"
    except UserAlreadyParticipant:
        return "User is already a participant."
    except (InviteHashInvalid, InviteHashExpired):
        return "Could not join. Maybe your link is expired or Invalid."
    except FloodWait:
        return "Too many requests, try again later."
    except Exception as e:
        print(e)
        return "Could not join, try joining manually."
    
#Regex---------------------------------------------------------------------------------------------------------------
#to get the url from event

def get_link(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex,string)   
    try:
        link = [x[0] for x in url][0]
        if link:
            return link
        else:
            return False
    except Exception:
        return False
    
#Screenshot---------------------------------------------------------------------------------------------------------------

def hhmmss(seconds):
    x = time.strftime('%H:%M:%S',time.gmtime(seconds))
    return x

async def screenshot(video, duration, sender):
    if os.path.exists(f'{sender}.jpg'):
        return f'{sender}.jpg'
    time_stamp = hhmmss(int(duration)/2)
    out = dt.now().isoformat("_", "seconds") + ".jpg"
    cmd = ["ffmpeg",
           "-ss",
           f"{time_stamp}", 
           "-i",
           f"{video}",
           "-frames:v",
           "1", 
           f"{out}",
           "-y"
          ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    x = stderr.decode().strip()
    y = stdout.decode().strip()
    if os.path.isfile(out):
        return out
    else:
        None
    
@PBot.on_message(filters.incoming & filters.regex(f"{B}"))
async def _batch(pbot, cmd):
    if str(cmd.chat.type) == "ChatType.PRIVATE":
        pass
    else:
        return
    s, r = await force_sub(TDrone, fs, cmd.from_user.id, ft)
    if s == True:
        await cmd.reply(r)
        return       
    if cmd.from_user.id in batch:
        return await cmd.reply("You've already started one batch, wait for it to complete you dumbfuck owner!")
    async with TDrone.conversation(cmd.from_user.id) as conv: 
        if s != True:
            await conv.send_message("Send me the message link you want to start saving from, as a reply to this message.", buttons=Button.force_reply())
            try:
                link = await conv.get_reply()
                try:
                    _link = get_link(link.text)
                except Exception:
                    await conv.send_message("No link found.")
                    return conv.cancel()
            except Exception as e:
                print(e)
                await conv.send_message("Cannot wait more longer for your response!")
                return conv.cancel()
            await conv.send_message("Send me the number of files/range you want to save from the given message, as a reply to this message.", buttons=Button.force_reply())
            try:
                _range = await conv.get_reply()
            except Exception as e:
                print(e)
                await conv.send_message("Cannot wait more longer for your response!")
                return conv.cancel()
            try:
                value = int(_range.text)
                if value > 700:
                    await conv.send_message("You can only get upto 700 files in a single batch.")
                    return conv.cancel()
            except ValueError:
                await conv.send_message("Range must be an integer!")
                return conv.cancel()
            batch.append(cmd.from_user.id)
            await run_batch(userbot, pbot, cmd.from_user.id, _link, value)
            conv.cancel()
            batch.clear()

@PBot.on_message(filters.incoming & filters.private & ~filters.photo)
async def clone(pbot, cmd):
    if cmd.reply_to_message:
        reply = cmd.reply_to_message
        if reply.text in ["Send me the message link you want to start saving from, as a reply to this message.", "Send me the number of files/range you want to save from the given message, as a reply to this message."]:
            return
    try:
        link = get_link(cmd.text)
        if not link:
            return
    except TypeError:
        return
    s, r = await force_sub(TDrone, fs, cmd.from_user.id, ft)
    if s == True:
        await cmd.reply(r)
        return
    edit = await cmd.reply("Processing!")
    try:
        if 't.me/+' in link:
            q = await join(userbot, link)
            await edit.edit(q)
            return
        if 't.me/' in link:
            await get_msg(userbot, pbot, TDrone, cmd.from_user.id, edit.id, link, 0)
    except FloodWait as fw:
        return await pbot.send_message(cmd.from_user.id, f'Try again after {fw.value} seconds due to floodwait from telegram.')
    except Exception as e:
        print(e)
        await pbot.send_message(cmd.from_user.id, f"An error occurred during cloning of {link}\n\nError: {str(e)}")


async def run_batch(userbot, client, sender, link, _range):
    for i in range(_range):    
        timer = 6
        if i < 2.5:
            timer = 0.5
        if i < 5 and i >= 2.5:
            timer = 10
        if i < 10 and i >= 5:
            timer = 1.5
        if not 't.me/c/' in link:
            if i < 2.5:
                timer = 0.2
            else:
                timer = 0.3   
        
        try:
            await get_bulk_msg(userbot, client, sender, link, i) 
        except FloodWait as fw:
            if int(fw.value) > 299:
                print("Cancelling batch due to floodwait.")
                await client.send_message(sender, "Cancelling batch since you have floodwait > 5 minutes.")
                break
            await asyncio.sleep(fw.value + 5)
            await get_bulk_msg(userbot, client, sender, link, i)
    
    await client.send_message(sender, "Batch completed.")

async def start_srb(cmd, st):
    buttons=[
               [InlineKeyboardButton("SET THUMBNAIL", callback_data="set")],
               [InlineKeyboardButton("REM THUMBNAIL", callback_data="rem")],
               [InlineKeyboardButton("DEVELOPER", url="t.me/ASinghhhhh")]
            ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await cmd.reply(st, reply_markup=reply_markup)


#Forcesub
async def force_sub(tdrone, channel, id, ft):
    s, r = False, None
    print(tdrone, channel, id, ft)
    try:
        x = await tdrone(GetParticipantRequest(channel=channel, participant=int(id)))
        left = x.stringify()
        if 'left' in left:
            s, r = True, f"{ft}\n\nAlso join @DromBots"
        else:
            s, r = False, None
    except UserNotParticipantError:
        s, r = True, f"To use this bot @{channel}."
    except Exception:
        s, r = True, "ERROR: Add in ForceSub channel, or check your channel id."
    return s, r


#fastest way to get total number of frames in a video
def total_frames(video_path):
    cap = cv2.VideoCapture(f"{video_path}")
    tf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) 
    return tf        

#makes a subprocess handy
def bash(cmd):    
    bashCommand = f"{cmd}"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE) 
    output, error = process.communicate()
    return output, error

#to get width, height and duration(in sec) of a video
def videometadata(file):
    vcap = cv2.VideoCapture(f'{file}')  
    width = round(vcap.get(cv2.CAP_PROP_FRAME_WIDTH ))
    height = round(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT ))
    fps = vcap.get(cv2.CAP_PROP_FPS)
    frame_count = vcap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = round(frame_count / fps)
    data = {'width' : width, 'height' : height, 'duration' : duration }
    return data

# function to find the resolution of the input video file

import subprocess
import shlex
import json

def findVideoResolution(pathToInputVideo):
    cmd = "ffprobe -v quiet -print_format json -show_streams"
    args = shlex.split(cmd)
    args.append(pathToInputVideo)
    # run the ffprobe process, decode stdout into utf-8 & convert to JSON
    ffprobeOutput = subprocess.check_output(args).decode('utf-8')
    ffprobeOutput = json.loads(ffprobeOutput)

    # find height and width
    height = ffprobeOutput['streams'][0]['height']
    width = ffprobeOutput['streams'][0]['width']

    # find duration
    out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_format", "-print_format", "json", pathToInputVideo])
    ffprobe_data = json.loads(out)
    duration_seconds = float(ffprobe_data["format"]["duration"])

    return int(height), int(width), int(duration_seconds)

def duration(pathToInputVideo):
    out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_format", "-print_format", "json", pathToInputVideo])
    ffprobe_data = json.loads(out)
    duration_seconds = float(ffprobe_data["format"]["duration"])
    return int(duration_seconds)
  
def video_metadata(file):
    height = 720
    width = 1280
    duration = 0
    try:
        height, width, duration = findVideoResolution(file)
        if duration == 0:
            data = videometadata(file)
            duration = data["duration"]
            if duration is None:
                duration = 0
    except Exception as e:
        try: 
            if 'height' in str(e):
                data = videometadata(file)
                height = data["height"]
                width = data["width"]
                duration = duration(file)
                if duration == 0:
                    data = videometadata(file)
                    duration = data["duration"]
                    if duration is None:
                        duration = 0
        except Exception as e:
            print(e)
            height, width, duration = 720, 1280, 0
    data = {'width' : width, 'height' : height, 'duration' : duration }
    return data



if __name__ == "__main__":
    TDrone.run_until_disconnected()
