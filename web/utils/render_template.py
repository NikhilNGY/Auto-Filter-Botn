from info import BIN_CHANNEL, URL
from utils import temp
import urllib.parse, html

# -------------------------
# HTML template for media watch page
# -------------------------
watch_tmplt = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta property="og:image" content="https://i.ibb.co/M8S0Zzj/live-streaming.png" itemprop="thumbnailUrl">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{heading}</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <style>
        :root {{
            --primary: #818cf8;
            --primary-hover: #6366f1;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --bg-color: #0f172a;
            --player-bg: #1e293b;
            --footer-bg: #1e293b;
            --border-color: #334155;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        header {{
            padding: 1rem;
            background-color: var(--player-bg);
            text-align: center;
        }}
        #file-name {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 80%;
        }}
        .container {{
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
            width: 100%;
        }}
        .player-container {{
            width: 100%;
            max-width: 1200px;
            background-color: var(--player-bg);
            border-radius: 0.5rem;
            overflow: hidden;
        }}
        .action-buttons {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 1rem;
        }}
        .action-btn {{
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .action-btn:hover {{
            background-color: var(--primary-hover);
        }}
        footer {{
            padding: 1rem;
            text-align: center;
            background-color: var(--footer-bg);
            color: var(--text-secondary);
            font-size: 0.875rem;
            border-top: 1px solid var(--border-color);
        }}
    </style>
</head>
<body class="dark">
    <header>
        <div id="file-name">{file_name}</div>
    </header>

    <div class="container">
        <div class="player-container">
            <video src="{src}" class="player" playsinline controls></video>
            <div class="action-buttons">
                <a href="{src}" class="action-btn" download>Download</a>
                <a href="vlc://{src}" class="action-btn">Play in VLC</a>
            </div>
        </div>
    </div>

    <footer>
        <p>Video not playing? Please try downloading the file or playing in VLC.</p>
    </footer>
</body>
</html>
"""

# -------------------------
# Generate watch HTML for a media message
# -------------------------
async def media_watch(message_id):
    media_msg = await temp.BOT.get_messages(BIN_CHANNEL, message_id)
    media = getattr(media_msg, media_msg.media.value, None)

    src = urllib.parse.urljoin(URL, f'download/{message_id}')
    mime_tag = media.mime_type.split('/')[0].strip()

    if mime_tag == 'video':
        heading = html.escape(f'Watch - {media.file_name}')
        html_content = watch_tmplt.format(
            heading=heading,
            file_name=media.file_name,
            src=src
        )
    else:
        html_content = '<h1>This file is not supported for playback</h1>'

    return html_content