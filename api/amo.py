import os
import aiohttp

AMO_DOMAIN = os.environ.get("AMO_DOMAIN", "")
AMO_TOKEN = os.environ.get("AMO_TOKEN", "")


async def get_recording_url(phone: str) -> str | None:
    if not AMO_DOMAIN or not AMO_TOKEN:
        return None

    digits = "".join(c for c in phone if c.isdigit())

    headers = {
        "Authorization": f"Bearer {AMO_TOKEN}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # Find contact by phone
        async with session.get(
            f"https://{AMO_DOMAIN}/api/v4/contacts",
            params={"query": digits, "limit": 1},
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

        contacts = data.get("_embedded", {}).get("contacts", [])
        if not contacts:
            return None
        contact_id = contacts[0]["id"]

        # Get notes for contact, look for call recordings
        async with session.get(
            f"https://{AMO_DOMAIN}/api/v4/contacts/{contact_id}/notes",
            params={"limit": 50, "order[created_at]": "desc"},
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

        notes = data.get("_embedded", {}).get("notes", [])
        for note in notes:
            if note.get("note_type") in ("call_in", "call_out"):
                link = note.get("params", {}).get("link")
                if link:
                    return link

    return None
