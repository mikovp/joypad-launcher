"""Steam account discovery from local client files."""

import os

from joypad.integrations.vdf import parse_vdf


def _vdf_flag(value):
    return str(value or "").strip().lower() in ("1", "true", "yes")


def read_steam_accounts(steam_dir):
    """
    Parse loginusers.vdf.
    Returns list of dicts: steam_id, persona_name, account_name, most_recent.
    """
    if not steam_dir or not os.path.isdir(steam_dir):
        return []
    path = os.path.join(steam_dir, "config", "loginusers.vdf")
    if not os.path.isfile(path):
        return []
    data = parse_vdf(path)
    if not data:
        return []
    users = data.get("users") or data.get("Users") or {}
    if not isinstance(users, dict):
        return []
    accounts = []
    for steam_id, entry in users.items():
        if not isinstance(entry, dict):
            continue
        persona = (entry.get("PersonaName") or entry.get("personaname") or "").strip()
        account_name = (entry.get("AccountName") or entry.get("accountname") or "").strip()
        most_recent = _vdf_flag(entry.get("MostRecent") or entry.get("mostrecent"))
        accounts.append({
            "steam_id": str(steam_id).strip(),
            "persona_name": persona or account_name or str(steam_id),
            "account_name": account_name,
            "most_recent": most_recent,
        })
    return accounts


def get_active_steam_account(steam_dir):
    """Most recently used Steam account on this PC, or None."""
    accounts = read_steam_accounts(steam_dir)
    if not accounts:
        return None
    for acct in accounts:
        if acct["most_recent"]:
            return acct
    return accounts[0]


def active_steam_login(account):
    """Steam login (AccountName) for UI labels, with persona fallback."""
    if not account:
        return None
    login = (account.get("account_name") or "").strip()
    if login:
        return login
    persona = (account.get("persona_name") or "").strip()
    return persona or None
