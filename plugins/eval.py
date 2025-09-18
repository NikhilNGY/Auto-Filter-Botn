import sys
import os
import traceback
from io import StringIO
from hydrogram import Client, filters
from hydrogram.errors import MessageTooLong
from info import ADMINS

@Client.on_message(filters.command("eval") & filters.user(ADMINS))
async def executor(client, message):
    # Get code
    try:
        code = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply("Command Incomplete!\nUsage: /eval your_python_code")

    # Redirect stdout and stderr
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = StringIO(), StringIO()
    exc = None

    try:
        # Run async code
        await aexec(code, client, message)
    except Exception:
        exc = traceback.format_exc()

    # Capture output
    stdout = sys.stdout.getvalue()
    stderr = sys.stderr.getvalue()
    sys.stdout, sys.stderr = old_stdout, old_stderr

    # Prepare final output
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success!"

    final_output = f"Output:\n\n<code>{evaluation}</code>"

    # Send output
    try:
        await message.reply(final_output)
    except MessageTooLong:
        with open("eval.txt", "w+", encoding="utf-8") as f:
            f.write(final_output)
        await message.reply_document("eval.txt")
        os.remove("eval.txt")


async def aexec(code, client, message):
    """Executes asynchronous Python code dynamically."""
    exec(
        f"async def __aexec(client, message):\n"
        + "".join(f"    {line}\n" for line in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)