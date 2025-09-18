class script(object):

    START_TXT = """<b>​​​Hello {} , \nI am an AutoFilter Bot Made for Team KR PICTURE.\nJoin My Updates Channel For More Details.</b>"""

    MY_ABOUT_TXT = """★ Server: <a href=https://www.heroku.com>Heroku</a>
★ Database: <a href=https://www.mongodb.com>MongoDB</a>
★ Language: <a href=https://www.python.org>Python</a>
★ Library: <a href=https://t.me/HydrogramNews>Hydrogram</a>"""

    MY_OWNER_TXT = """★ Name: NIKHIL
★ Username: @Nikhil5757h 
★ Country: INDIA"""

    STATUS_TXT = """👤 Total Users: <code>{}</code>
👥 Total Chats: <code>{}</code>
🗳 Data database used: <code>{}</code>
🗂 1st database Files: <code>{}</code>
🗳 1st files database used: <code>{}</code>
🗂 2nd database Files: <code>{}</code>
🗳 2nd files database used: <code>{}</code>
🚀 Bot Uptime: <code>{}</code>"""

    NEW_GROUP_TXT = """#NewGroup
Title - {}
ID - <code>{}</code>
Username - {}
Total - <code>{}</code>"""

    NEW_USER_TXT = """#NewUser
★ Name: {}
★ ID: <code>{}</code>"""

    NOT_FILE_TXT = """<b>⚠️ Dᴏɴ'ᴛ Aꜱᴋ Lɪᴋᴇ Tʜɪꜱ. Aꜱᴋ Oɴʟʏ Mᴏᴠɪᴇ Nᴀᴍᴇ Wɪᴛʜ Yᴇᴀʀ. (Cʜᴇᴄᴋ Cᴏʀʀᴇᴄᴛ Sᴘᴇʟʟɪɴɢ Sᴀᴍᴇ Aꜱ Iɴ Gᴏᴏɢʟᴇ) Dᴏɴ'ᴛ Aᴅᴅ Aɴʏ Wᴏʀᴅꜱ Wʜɪʟᴇ RᴇQᴜᴇꜱᴛɪɴɢ. Oᴛʜᴇʀᴡɪꜱᴇ Yᴏᴜ Dᴏɴ'ᴛ Gᴇᴛ Tʜᴇ Mᴏᴠɪᴇ Cᴏʀʀᴇᴄᴛʟʏ🚫⚠️

Aᴅᴅ Mᴏᴠɪᴇ Nᴀᴍᴇ: 
Eg:
777 ᴄʜᴀʀʟɪᴇ ✅
777 ᴄʜᴀʀʟɪᴇ 2022 ✅
777 ᴄʜᴀʀʟɪᴇ ᴋᴀɴɴᴀᴅᴀ ✅ 
777ᴄʜᴀʀʟɪᴇ ❌ 
777 ᴄʜᴀʀʟɪᴇ ᴍᴏᴠɪᴇ ❌
777 ᴄʜᴀʀʟɪᴇ ʟɪɴᴋ ❌ ᴇᴛᴄ.</b>"""

    IMDB_TEMPLATE = """✅ I Found: <code>{query}</code>

🏷 Title: <a href={url}>{title}</a>
🎭 Genres: {genres}
📆 Year: <a href={url}/releaseinfo>{year}</a>
🌟 Rating: <a href={url}/ratings>{rating} / 10</a>
☀️ Languages: {languages}
📀 RunTime: {runtime} Minutes
🗣 Requested by: {message.from_user.mention}
©️ Powered by: <b>{message.chat.title}</b>"""

    FORCESUB_TEXT="""<b>
ನಮಸ್ಕಾರ  🙏  ,
 
ಚಲನಚಿತ್ರವನ್ನು ಪಡೆಯಲು "JOIN CHANNEL" ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ ಮತ್ತು ಚಾನಲ್‌ನಲ್ಲಿ ಸೇರಿಕೊಳ್ಳಿ.
 
─────── • ◆ • ──────

You Need to Join My Channel to Receive the Movie file. CLICK BUTTON 👇👇
    </b>"""

    FILE_CAPTION = """<strong><blockquote>Mᴏʀᴇ Mᴏᴠɪᴇꜱ Jᴏɪɴ @sandalwood_kannada_moviesz\n \nTᴇᴀᴍ : @KR_Picture\n \nUᴘʟᴏᴀᴅᴇᴅ Bʏ 👉\nhttps://t.me/+X5CwwZB-jV9iODc1\nhttps://t.me/+X5CwwZB-jV9iODc1</blockquote></strong>"""


    WELCOME_TEXT = """👋 Hello {mention}, Welcome to {title} group! 💞"""

    HELP_TXT = """👋 Hello {},
    
I can filter movies and series you want.
Just type your movie or series in PM or add me to your group.
I have more features, just try my commands."""

    ADMIN_COMMAND_TXT = """<b>Here are bot admin commands 👇

/index_channels - check added index channels
/stats - get bot status
/delete - delete files using query
/delete_all - delete all indexed files
/broadcast - send message to all users
/grp_broadcast - send message to all groups
/pin_broadcast - pin broadcast to users
/pin_grp_broadcast - pin broadcast to groups
/restart - restart bot
/leave - leave a group
/users - get all users
/chats - get all groups
/invite_link - generate invite link
/index - index accessible channels
/delreq - delete join request in db
/set_req_fsub - set request force subscribe channel
/set_fsub - set force subscribe channels</b>"""

    USER_COMMAND_TXT = """<b>Here are bot user commands 👇

/start - check bot alive
/img_2_link - upload image and get link
/settings - change group settings
/connect - connect group settings to PM
/id - check group or channel id</b>"""

    SOURCE_TXT = """<b>Bot GitHub Repository -

- This bot is private-source
- Source - <a href=https://t.me/Nikhil5757h>Here</a>
- Developer - @KR_PICTURE</b>"""