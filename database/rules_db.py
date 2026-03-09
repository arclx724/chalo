from database import dbname

rulesdb = dbname["rules"]


def _default_rules(chat_id: int) -> dict:
    return {
        "chat_id": chat_id,
        "rules": "No rules have been set for this chat yet.",
        "private_rules": False,
        "button_name": "Rules",
    }


async def get_rules_config(chat_id: int) -> dict:
    data = await rulesdb.find_one({"chat_id": chat_id})
    if not data:
        data = _default_rules(chat_id)
        await rulesdb.insert_one(data)
    return data


async def get_rules(chat_id: int) -> str:
    return (await get_rules_config(chat_id)).get("rules") or _default_rules(chat_id)["rules"]


async def set_rules(chat_id: int, text: str):
    await rulesdb.update_one({"chat_id": chat_id}, {"$set": {"rules": text}}, upsert=True)


async def reset_rules(chat_id: int):
    await rulesdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"rules": _default_rules(chat_id)["rules"]}},
        upsert=True,
    )


async def get_private_rules(chat_id: int) -> bool:
    return bool((await get_rules_config(chat_id)).get("private_rules", False))


async def set_private_rules(chat_id: int, enabled: bool):
    await rulesdb.update_one({"chat_id": chat_id}, {"$set": {"private_rules": bool(enabled)}}, upsert=True)


async def get_rules_button(chat_id: int) -> str:
    return (await get_rules_config(chat_id)).get("button_name") or "Rules"


async def set_rules_button(chat_id: int, text: str):
    await rulesdb.update_one({"chat_id": chat_id}, {"$set": {"button_name": text.strip()}}, upsert=True)


async def reset_rules_button(chat_id: int):
    await rulesdb.update_one({"chat_id": chat_id}, {"$set": {"button_name": "Rules"}}, upsert=True)
