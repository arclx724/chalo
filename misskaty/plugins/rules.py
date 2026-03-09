from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.rules_db import (
    get_private_rules,
    get_rules,
    get_rules_button,
    reset_rules,
    reset_rules_button,
    set_private_rules,
    set_rules,
    set_rules_button,
)
from misskaty import BOT_USERNAME, app
from misskaty.core.decorator.permissions import adminsOnly
from misskaty.vars import COMMAND_HANDLER

__MODULE__ = "Rules"
__HELP__ = """Rules

Every chat works with different rules; this module will help make those rules clearer!

User commands:
- /rules: Check the current chat rules.

Admin commands:
- /setrules <text>: Set the rules for this chat. Supports markdown, buttons, fillings, etc.
- /privaterules <yes/no/on/off>: Enable/disable whether the rules should be sent in private.
- /resetrules: Reset the chat rules to default.
- /setrulesbutton: Set the rules button name when using {rules}.
- /resetrulesbutton: Reset the rules button name from {rules} to default.

Examples:
- Get the unformatted rules text, to make them easier to edit.
-> /rules noformat

- Set the name of the button to use when using the {rules} filling.
-> /setrulesbutton Press me for the chat rules"""


def _to_bool(text: str):
    t = text.lower().strip()
    if t in {"yes", "on", "true", "enable", "enabled"}:
        return True
    if t in {"no", "off", "false", "disable", "disabled"}:
        return False
    return None


@app.on_message(filters.command("rules", COMMAND_HANDLER))
async def rules_cmd(_, message):
    if message.chat.type.value == "private" and len(message.command) > 1 and message.command[1].startswith("btnrules_"):
        chat_id = int(message.command[1].split("_", 1)[1])
    else:
        chat_id = message.chat.id

    rules_text = await get_rules(chat_id)

    if len(message.command) > 1 and message.command[1].lower() == "noformat":
        return await message.reply(rules_text)

    if message.chat.type.value != "private" and await get_private_rules(chat_id):
        btn_name = await get_rules_button(chat_id)
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton(btn_name, url=f"https://t.me/{BOT_USERNAME}?start=btnrules_{chat_id}")]]
        )
        return await message.reply("Tap button below to read rules in private.", reply_markup=btn)

    await message.reply(rules_text)


@app.on_message(filters.private & filters.command("start") & filters.regex(r"^/start btnrules_"))
async def rules_start(_, message):
    if len(message.command) < 2:
        return
    payload = message.command[1]
    if not payload.startswith("btnrules_"):
        return
    chat_id = int(payload.split("_", 1)[1])
    rules_text = await get_rules(chat_id)
    await message.reply(rules_text)


@app.on_message(filters.command("setrules", COMMAND_HANDLER) & ~filters.private)
@adminsOnly("can_change_info")
async def setrules_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /setrules <text>")
    text = message.text.split(None, 1)[1]
    await set_rules(message.chat.id, text)
    await message.reply("Rules updated.")


@app.on_message(filters.command("resetrules", COMMAND_HANDLER) & ~filters.private)
@adminsOnly("can_change_info")
async def resetrules_cmd(_, message):
    await reset_rules(message.chat.id)
    await message.reply("Rules reset to default.")


@app.on_message(filters.command("privaterules", COMMAND_HANDLER) & ~filters.private)
@adminsOnly("can_change_info")
async def privaterules_cmd(_, message):
    if len(message.command) < 2:
        state = await get_private_rules(message.chat.id)
        return await message.reply(f"Private rules is {'enabled' if state else 'disabled'}.")
    enabled = _to_bool(message.command[1])
    if enabled is None:
        return await message.reply("Usage: /privaterules <yes/no/on/off>")
    await set_private_rules(message.chat.id, enabled)
    await message.reply(f"Private rules {'enabled' if enabled else 'disabled'}.")


@app.on_message(filters.command("setrulesbutton", COMMAND_HANDLER) & ~filters.private)
@adminsOnly("can_change_info")
async def setrulesbutton_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /setrulesbutton <text>")
    text = message.text.split(None, 1)[1].strip()
    await set_rules_button(message.chat.id, text)
    await message.reply(f"Rules button updated to: {text}")


@app.on_message(filters.command("resetrulesbutton", COMMAND_HANDLER) & ~filters.private)
@adminsOnly("can_change_info")
async def resetrulesbutton_cmd(_, message):
    await reset_rules_button(message.chat.id)
    await message.reply("Rules button reset to default.")
