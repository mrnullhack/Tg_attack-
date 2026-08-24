#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
████████╗ ██████╗       █████╗ ████████╗██╗  ██╗███████╗██████╗ 
╚══██╔══╝██╔════╝      ██╔══██╗╚══██╔══╝██║ ██╔╝██╔════╝██╔══██╗
   ██║   ██║  ███╗     ███████║   ██║   █████╔╝ █████╗  ██████╔╝
   ██║   ██║   ██║     ██╔══██║   ██║   ██╔═██╗ ██╔══╝  ██╔══██╗
   ██║   ╚██████╔╝     ██║  ██║   ██║   ██║  ██╗███████╗██║  ██║
   ╚═╝    ╚═════╝      ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                    v4.0 - KALI EDITION
 Telegram Group Security Assessment Framework
 For Authorized Penetration Testing Only
"""

import os, sys, json, asyncio, random, time, re, base64
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter, defaultdict

# رنگ‌های پیشرفته ترمینال
os.system("")  # فعالسازی ANSI در CMD ویندوز — توی کالی هم کار می‌کنه
from colorama import init, Fore, Style
init(autoreset=True)

import requests
from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message, User, Chat, ChatMember, ChatPrivileges
from pyrogram.errors import (
    FloodWait, PeerIdInvalid, ChatAdminRequired, 
    UserNotParticipant, UsernameInvalid, UsernameNotOccupied,
    InviteHashExpired, InviteHashInvalid, UserAlreadyParticipant,
    ChatWriteForbidden, SlowmodeInterval, MessageTooLong
)

# ============================================================
#                   کانفیگ اصلی
# ============================================================
CONFIG = {
    # Credentials
    "api_id": 0,                # از my.telegram.org
    "api_hash": "",             # از my.telegram.org
    "phone": "+989121234567",   # شماره حساب حمله
    "is_bot": False,            # True اگر بات (محدودیت بیشتر)
    "bot_token": "",
    
    # Proxy (اختیاری)
    "proxy": None,              # {"scheme":"socks5","hostname":"127.0.0.1","port":9050}
    
    # Rate limiting
    "max_actions_per_min": 28,
    "action_delay": (0.8, 2.5),
    "flood_safe_mode": True,
    
    # Storage
    "output_dir": "TG_ATKER_OUTPUT",
    "auto_save": True,
}

# ============================================================
#                   رنگ‌های کمکی
# ============================================================
R = Fore.RED
G = Fore.GREEN  
Y = Fore.YELLOW
C = Fore.CYAN
M = Fore.MAGENTA
W = Fore.WHITE
B = Fore.BLUE
L = Fore.LIGHTBLACK_EX
RS = Style.RESET_ALL
BO = Style.BRIGHT
DI = Style.DIM

# ============================================================
#                   کلاس Rate Limiter 
# ============================================================
class AntiFlood:
    """جلوگیری از بلاک شدن توسط محدودیت تلگرام"""
    def __init__(self, max_per_min=28):
        self.max_per_min = max_per_min
        self.history = []
    
    async def wait(self):
        now = time.time()
        self.history = [t for t in self.history if now - t < 60]
        if len(self.history) >= self.max_per_min:
            wait = 60 - (now - self.history[0])
            if wait > 0:
                print(f"{Y}{BO}[!] Anti-Flood: waiting {wait:.1f}s...{RS}")
                await asyncio.sleep(wait + 0.5)
        self.history.append(time.time())
        if CONFIG["action_delay"]:
            await asyncio.sleep(random.uniform(*CONFIG["action_delay"]))

# ============================================================
#                   کلاس اصلی — هسته مرکزی
# ============================================================
class TGAtker:
    def __init__(self):
        self.app: Optional[Client] = None
        self.me: Optional[User] = None
        self.af = AntiFlood(CONFIG["max_actions_per_min"])
        self.out = Path(CONFIG["output_dir"])
        self.out.mkdir(parents=True, exist_ok=True)
        self.stats = {
            "groups_joined": 0,
            "members_scraped": 0,
            "messages_collected": 0,
            "admins_found": 0,
            "phones_extracted": 0,
            "targets_attacked": 0,
        }
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
    
    # ========================================================
    #                   راه‌اندازی
    # ========================================================
    async def start(self):
        log(f"{C}{BO}⚡ Initializing TG-Atker v4.0...{RS}", C)
        
        if CONFIG["is_bot"]:
            self.app = Client(
                "tg_atker_session", 
                api_id=CONFIG["api_id"],
                api_hash=CONFIG["api_hash"],
                bot_token=CONFIG["bot_token"],
                proxy=CONFIG["proxy"],
                workdir=str(self.out)
            )
        else:
            self.app = Client(
                "tg_atker_session",
                api_id=CONFIG["api_id"],
                api_hash=CONFIG["api_hash"],
                phone_number=CONFIG["phone"],
                proxy=CONFIG["proxy"],
                workdir=str(self.out)
            )
        
        await self.app.start()
        self.me = await self.app.get_me()
        
        print(f"""
{BO}{M}╔══════════════════════════════════════════════╗{RS}
{BO}{M}║{RS}  {C}{BO}TG-ATKER v4.0 — READY FOR ACTION{RS}        {M}{BO}║{RS}
{BO}{M}╠══════════════════════════════════════════════╣{RS}
{BO}{M}║{RS}  {G}User:{RS}     {C}{self.me.first_name}{RS} @{self.me.username or '—'}
{BO}{M}║{RS}  {G}ID:{RS}       {Y}{self.me.id}{RS}
{BO}{M}║{RS}  {G}Premium:{RS}  {'✅ Yes' if self.me.is_premium else '❌ No'}
{BO}{M}║{RS}  {G}Type:{RS}     {'🤖 Bot' if CONFIG['is_bot'] else '👤 User'}
{BO}{M}╚══════════════════════════════════════════════╝{RS}
""")
        
        if self.me.is_premium:
            log("🔥 Premium account detected — scraping limits increased!", M)
        
        return self
    
    async def stop(self):
        if self.app:
            await self.app.stop()
            self._save_stats()
            log(f"{G}{BO}✓ Session ended. Stats saved.{RS}", G)
    
    def _save_stats(self):
        path = self.out / "session_stats.json"
        with open(path, "w") as f:
            json.dump(self.stats, f, indent=2)
    
    # ========================================================
    #                   PARSE TARGET
    # ========================================================
    def parse_target(self, target: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        خروجی: (chat_id, username, invite_hash)
        """
        target = target.strip()
        
        # لینک دعوت خصوصی: https://t.me/+abc123
        if "t.me/+" in target or "t.me/joinchat/" in target:
            hash_part = target.split("+")[-1].split("/")[0] if "+" in target else target.split("joinchat/")[-1].split("/")[0]
            return (None, None, hash_part)
        
        # لینک عمومی: https://t.me/username
        if "t.me/" in target:
            username = target.split("t.me/")[-1].split("/")[0]
            if username.startswith("+"):
                return (None, None, username[1:])
            return (None, username, None)
        
        # @username
        if target.startswith("@"):
            return (None, target[1:], None)
        
        # آیدی عددی
        if target.lstrip("-").isdigit():
            return (int(target), None, None)
        
        # username مستقیم
        return (None, target, None)
    
    # ========================================================
    #                   JOIN — عضویت در گروه
    # ========================================================
    async def join(self, target: str) -> Optional[int]:
        chat_id, username, invite_hash = self.parse_target(target)
        
        try:
            if invite_hash:
                link = f"https://t.me/+{invite_hash}"
                log(f"{Y}🔗 Joining via invite link...{RS}", Y)
                chat = await self.app.join_chat(link)
            elif username:
                log(f"{Y}🔗 Joining via username @{username}...{RS}", Y)
                chat = await self.app.join_chat(username)
            elif chat_id:
                log(f"{Y}🔗 Joining via chat ID {chat_id}...{RS}", Y)
                chat = await self.app.join_chat(chat_id)
            else:
                log(f"{R}✗ Invalid target format{RS}", R)
                return None
            
            self.stats["groups_joined"] += 1
            log(f"{G}{BO}✓ JOINED: {chat.title} [{chat.id}]{RS}", G)
            return chat.id
        
        except UserAlreadyParticipant:
            log(f"{Y}⚠ Already a member, resolving ID...{RS}", Y)
            return await self._resolve_id(target)
        except (InviteHashExpired, InviteHashInvalid):
            log(f"{R}✗ Invite link expired or invalid{RS}", R)
            return None
        except Exception as e:
            log(f"{R}✗ Join failed: {e}{RS}", R)
            return None
    
    async def _resolve_id(self, target: str) -> Optional[int]:
        chat_id, username, invite_hash = self.parse_target(target)
        if username:
            try:
                chat = await self.app.get_chat(username)
                return chat.id
            except:
                pass
        if chat_id:
            return chat_id
        return None
    
    # ========================================================
    #                   INFO — اطلاعات گروه
    # ========================================================
    async def get_info(self, chat_id) -> Dict:
        chat = await self.app.get_chat(chat_id)
        info = {
            "id": chat.id,
            "title": chat.title,
            "username": chat.username,
            "description": (chat.description or "")[:500],
            "type": str(chat.type).split(".")[-1],
            "members_count": chat.members_count or 0,
            "online_count": getattr(chat, 'online_count', 0) or 0,
            "slow_mode": chat.slow_mode,
            "dc_id": chat.dc_id,
            "is_verified": chat.is_verified,
            "is_scam": chat.is_scam,
            "is_fake": chat.is_fake,
            "is_restricted": chat.is_restricted,
            "invite_link": chat.invite_link,
            "linked_chat_id": chat.linked_chat.id if chat.linked_chat else None,
            "permissions": {
                "can_send_messages": chat.permissions.can_send_messages if chat.permissions else None,
                "can_send_media": chat.permissions.can_send_media if chat.permissions else None,
                "can_add_web_page_previews": chat.permissions.can_add_web_page_previews if chat.permissions else None,
            } if chat.permissions else None,
        }
        
        if CONFIG["auto_save"]:
            safe = re.sub(r'[\\/*?:"<>|]', '_', str(chat.title or chat.id))[:50]
            path = self.out / f"info_{safe}_{chat.id}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            log(f"{G}✓ Info saved → {path.name}{RS}", G)
        
        return info
    
    # ========================================================
    #                   SCRAPE — استخراج کامل اعضا
    # ========================================================
    async def scrape_members(self, chat_id, limit: int = 0) -> List[Dict]:
        log(f"{C}{BO}[*] Scraping members...{RS}", C)
        members = []
        count = 0
        
        try:
            async for member in self.app.get_chat_members(
                chat_id, 
                limit=limit if limit > 0 else 0
            ):
                user = member.user
                if not user:
                    continue
                
                m = {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "phone": user.phone_number,
                    "status": str(member.status).split(".")[-1],
                    "is_bot": user.is_bot,
                    "is_premium": user.is_premium,
                    "is_verified": user.is_verified,
                    "is_scam": user.is_scam,
                    "is_fake": user.is_fake,
                    "custom_title": member.custom_title,
                    "joined_date": str(member.joined_date) if member.joined_date else None,
                    "invited_by": member.invited_by.id if member.invited_by else None,
                }
                members.append(m)
                count += 1
                
                if count % 100 == 0:
                    print(f"{C}  → Scraped {count} members...{RS}")
                
                await self.af.wait()
        
        except FloodWait as e:
            log(f"{Y}⚠ FloodWait: {e.value}s — sleeping{RS}", Y)
            await asyncio.sleep(e.value + 2)
        except ChatAdminRequired:
            log(f"{Y}⚠ Only admins can scrape all members — getting what's available{RS}", Y)
        except Exception as e:
            log(f"{Y}⚠ Scrape error: {e}{RS}", Y)
        
        self.stats["members_scraped"] += count
        
        if members and CONFIG["auto_save"]:
            safe = re.sub(r'[\\/*?:"<>|]', '_', str(chat_id))[:50]
            path = self.out / f"members_{safe}_{len(members)}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(members, f, indent=2, ensure_ascii=False)
            log(f"{G}✓ {count} members saved → {path.name}{RS}", G)
        
        return members
    
    # ========================================================
    #                   PHONE EXTRACT — استخراج شماره تلفن
    # ========================================================
    async def extract_phones(self, chat_id) -> List[Dict]:
        """استخراج اعضایی که شماره تلفن قابل مشاهده دارند"""
        members = await self.scrape_members(chat_id)
        with_phone = [m for m in members if m.get("phone")]
        
        for m in with_phone:
            # ماسک کردن بخشی از شماره برای گزارش (قبل از ذخیره)
            phone = m["phone"]
            if phone and len(phone) > 6:
                m["phone_masked"] = phone[:4] + "****" + phone[-3:]
        
        self.stats["phones_extracted"] += len(with_phone)
        
        if with_phone:
            safe = re.sub(r'[\\/*?:"<>|]', '_', str(chat_id))[:50]
            path = self.out / f"phones_{safe}_{len(with_phone)}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(with_phone, f, indent=2, ensure_ascii=False)
            
            print(f"""
{BO}{M}╔══════════════════════════════════╗{RS}
{BO}{M}║{RS}  {G}📞 PHONE NUMBERS EXTRACTED{RS}       {M}{BO}║{RS}
{BO}{M}║{RS}  {Y}Total:{RS} {G}{len(with_phone)}{RS}                       {M}{BO}║{RS}
{BO}{M}╠══════════════════════════════════╣{RS}""")
            for m in with_phone[:20]:
                print(f"{BO}{M}║{RS}  {C}{m['id']:<10}{RS} {m.get('phone_masked', m['phone']):<20}{M}{BO}║{RS}")
            if len(with_phone) > 20:
                print(f"{BO}{M}║{RS}  {DI}... and {len(with_phone)-20} more{M}{BO}║{RS}")
            print(f"{BO}{M}╚══════════════════════════════════╝{RS}")
            
            log(f"{G}✓ {len(with_phone)} phones saved ✅{RS}", G)
        else:
            log(f"{Y}⚠ No visible phone numbers found{RS}", Y)
        
        return with_phone
    
    # ========================================================
    #                   FIND ADMINS
    # ========================================================
    async def admins(self, chat_id) -> List[Dict]:
        log(f"{C}{BO}[*] Extracting admin list...{RS}", C)
        admins_list = []
        
        try:
            async for member in self.app.get_chat_members(
                chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS
            ):
                user = member.user
                privs = member.privileges
                a = {
                    "id": user.id,
                    "username": user.username,
                    "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                    "title": member.custom_title,
                    "is_owner": member.status == enums.ChatMemberStatus.OWNER,
                    "privileges": {
                        "can_change_info": privs.can_change_info if privs else False,
                        "can_delete_messages": privs.can_delete_messages if privs else False,
                        "can_restrict_members": privs.can_restrict_members if privs else False,
                        "can_invite_users": privs.can_invite_users if privs else False,
                        "can_pin_messages": privs.can_pin_messages if privs else False,
                        "can_promote_members": privs.can_promote_members if privs else False,
                        "can_manage_chat": privs.can_manage_chat if privs else False,
                        "is_anonymous": privs.is_anonymous if privs else False,
                    }
                }
                admins_list.append(a)
                await self.af.wait()
        except Exception as e:
            log(f"{Y}⚠ Error: {e}{RS}", Y)
        
        self.stats["admins_found"] += len(admins_list)
        
        if CONFIG["auto_save"]:
            safe = re.sub(r'[\\/*?:"<>|]', '_', str(chat_id))[:50]
            path = self.out / f"admins_{safe}_{len(admins_list)}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(admins_list, f, indent=2, ensure_ascii=False)
        
        # نمایش ادمین‌ها
        print(f"\n{BO}{M}╔═══ ADMINS ({len(admins_list)}) ═══╗{RS}")
        for a in admins_list:
            owner = f"{R}{BO}[OWNER]{RS}" if a["is_owner"] else ""
            print(f"  {C}{a['id']}{RS} @{a['username'] or '—'} {a['title'] or ''} {owner}")
            # سطح دسترسی
            privs_on = [k for k, v in a["privileges"].items() if v]
            if privs_on:
                print(f"    {G}Privileges: {', '.join(privs_on)}{RS}")
        print()
        
        log(f"{G}✓ {len(admins_list)} admins extracted{RS}", G)
        return admins_list
    
    # ========================================================
    #                   FLOOD — ارسال پیام انبوه
    # ========================================================
    async def flood(self, chat_id, text: str, count: int = 10, 
                    smart: bool = True, html: bool = False):
        log(f"{C}{BO}[*] Starting flood: {count} messages{RS}", C)
        sent = 0
        
        variants = [
            text,
            text + " 🔥",
            text + " ⚡",
            text + " 💥",
            text.upper(),
            text.lower(),
            text + "‼️",
            "⚠️ " + text,
            "🔴 " + text,
            text + " @everyone",
        ]
        
        for i in range(count):
            try:
                await self.af.wait()
                
                if smart and variants:
                    msg = random.choice(variants)
                else:
                    msg = text
                
                if html:
                    await self.app.send_message(chat_id, msg, parse_mode=enums.ParseMode.HTML)
                else:
                    await self.app.send_message(chat_id, msg)
                
                sent += 1
                
                if sent % 5 == 0:
                    print(f"{C}  → Sent {sent}/{count}{RS}")
            
            except SlowmodeInterval:
                log(f"{Y}⚠ Slowmode active — slowing down{RS}", Y)
                await asyncio.sleep(30)
            except ChatWriteForbidden:
                log(f"{R}✗ Cannot write in this group (banned/restricted){RS}", R)
                break
            except FloodWait as e:
                log(f"{Y}⚠ FloodWait: {e.value}s{RS}", Y)
                await asyncio.sleep(e.value + 3)
            except Exception as e:
                log(f"{R}✗ Flood error: {e}{RS}", R)
                break
        
        log(f"{G}✓ Flood complete: {sent}/{count} sent{RS}", G)
        return sent
    
    # ========================================================
    #                   COLLECT MESSAGES
    # ========================================================
    async def collect_messages(self, chat_id, limit: int = 200) -> List[Dict]:
        log(f"{C}{BO}[*] Collecting {limit} messages...{RS}", C)
        msgs = []
        
        try:
            async for msg in self.app.get_chat_history(chat_id, limit=limit):
                m = {
                    "id": msg.id,
                    "date": str(msg.date),
                    "user_id": msg.from_user.id if msg.from_user else None,
                    "username": msg.from_user.username if msg.from_user else None,
                    "name": f"{msg.from_user.first_name or ''} {msg.from_user.last_name or ''}".strip() if msg.from_user else None,
                    "text": (msg.text or msg.caption or "")[:500],
                    "has_media": bool(msg.media),
                    "media_type": str(msg.media).split(".")[-1] if msg.media else None,
                    "has_urls": bool(msg.entities and any(
                        e.type in ["url", "text_link"] for e in (msg.entities or [])
                    )),
                }
                msgs.append(m)
        except Exception as e:
            log(f"{Y}⚠ Error: {e}{RS}", Y)
        
        self.stats["messages_collected"] += len(msgs)
        
        if CONFIG["auto_save"]:
            safe = re.sub(r'[\\/*?:"<>|]', '_', str(chat_id))[:50]
            path = self.out / f"messages_{safe}_{len(msgs)}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(msgs, f, indent=2, ensure_ascii=False)
            log(f"{G}✓ {len(msgs)} messages saved → {path.name}{RS}", G)
        
        return msgs
    
    # ========================================================
    #                   ADMIN ACTIONS — عملیات ادمین
    # ========================================================
    async def admin_kick(self, chat_id, user_id, ban_only: bool = False):
        try:
            if ban_only:
                await self.app.ban_chat_member(chat_id, user_id)
                log(f"{R}{BO}⚠ BANNED user {user_id}{RS}", R)
            else:
                await self.app.ban_chat_member(chat_id, user_id)
                await asyncio.sleep(0.5)
                await self.app.unban_chat_member(chat_id, user_id)
                log(f"{R}{BO}⚠ KICKED user {user_id}{RS}", R)
            return True
        except ChatAdminRequired:
            log(f"{R}✗ Need admin rights to kick/ban{RS}", R)
        except Exception as e:
            log(f"{R}✗ Error: {e}{RS}", R)
        return False
    
    async def admin_purge_all(self, chat_id, exclude_admins: bool = True):
        """حذف دسته‌جمعی اعضا (نیاز به ادمین)"""
        log(f"{R}{BO}[!] PURGE MODE — Removing members...{RS}", R)
        members = await self.scrape_members(chat_id)
        admins_ids = set()
        
        if exclude_admins:
            async for m in self.app.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                admins_ids.add(m.user.id)
        
        removed = 0
        for m in members:
            if m["id"] in admins_ids or m["id"] == self.me.id:
                continue
            if m["status"] in ["owner", "administrator"]:
                continue
            if await self.admin_kick(chat_id, m["id"]):
                removed += 1
                await asyncio.sleep(random.uniform(1, 2.5))
        
        log(f"{R}{BO}⚠ Purge complete: {removed} members removed{RS}", R)
        return removed
    
    async def admin_rename(self, chat_id, title: str):
        try:
            await self.app.set_chat_title(chat_id, title)
            log(f"{G}✓ Title changed to: {title}{RS}", G)
            return True
        except ChatAdminRequired:
            log(f"{R}✗ Need admin rights{RS}", R)
        except Exception as e:
            log(f"{R}✗ Error: {e}{RS}", R)
        return False
    
    async def admin_set_photo(self, chat_id, photo_path: str):
        try:
            await self.app.set_chat_photo(chat_id, photo=photo_path)
            log(f"{G}✓ Photo changed{RS}", G)
            return True
        except ChatAdminRequired:
            log(f"{R}✗ Need admin rights{RS}", R)
        except Exception as e:
            log(f"{R}✗ Error: {e}{RS}", R)
        return False
    
    async def admin_delete_msgs(self, chat_id, msg_ids: List[int]):
        try:
            await self.app.delete_messages(chat_id, msg_ids)
            log(f"{G}✓ {len(msg_ids)} messages deleted{RS}", G)
            return True
        except ChatAdminRequired:
            log(f"{R}✗ Need admin rights{RS}", R)
        except Exception as e:
            log(f"{R}✗ Error: {e}{RS}", R)
        return False
    
    # ========================================================
    #                   LEAVE EXTRACT — استخراج و خروج
    # ========================================================
    async def leave(self, chat_id, delete_exit: bool = False):
        try:
            await self.app.leave_chat(chat_id, delete=delete_exit)
            log(f"{G}✓ Left chat {chat_id}{RS}", G)
            return True
        except Exception as e:
            log(f"{R}✗ Error: {e}{RS}", R)
        return False
    
    # ========================================================
    #                   MASS MENTION
    # ========================================================
    async def mass_mention(self, chat_id, limit: int = 50, msg: str = ""):
        members = await self.scrape_members(chat_id, limit=limit)
        with_username = [m for m in members if m.get("username") and not m["is_bot"]]
        
        if not with_username:
            log(f"{Y}⚠ No users with usernames found{RS}", Y)
            return
        
        # ساخت منشن در batches
        batch = []
        for m in with_username[:limit]:
            batch.append(f"@{m['username']}")
        
        full = f"{msg}\n\n" + " ".join(batch) if msg else " ".join(batch)
        
        try:
            await self.af.wait()
            await self.app.send_message(chat_id, full)
            log(f"{G}✓ Mentioned {len(batch)} users{RS}", G)
        except MessageTooLong:
            log(f"{Y}⚠ Message too long, sending in parts...{RS}", Y)
            for i in range(0, len(batch), 30):
                part = " ".join(batch[i:i+30])
                await self.app.send_message(chat_id, part)
                await asyncio.sleep(2)
            log(f"{G}✓ Mentioned {len(batch)} users in {len(batch)//30+1} parts{RS}", G)
        except Exception as e:
            log(f"{R}✗ Error: {e}{RS}", R)
    
    # ========================================================
    #                   LINKS EXTRACT — استخراج لینک‌ها
    # ========================================================
    async def extract_links(self, chat_id, limit: int = 300) -> Dict:
        msgs = await self.collect_messages(chat_id, limit)
        link_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
        urls = defaultdict(list)
        
        for m in msgs:
            text = m.get("text", "")
            found = re.findall(link_pattern, text)
            for url in found:
                if "t.me" in url:
                    urls["telegram"].append(url)
                elif any(ext in url for ext in ['.jpg', '.png', '.gif', '.jpeg']):
                    urls["images"].append(url)
                else:
                    urls["other"].append(url)
        
        # آمار
        total = sum(len(v) for v in urls.values())
        log(f"{G}✓ Extracted {total} links ({len(urls['telegram'])} Telegram, {len(urls['images'])} media, {len(urls['other'])} other){RS}", G)
        
        if CONFIG["auto_save"]:
            safe = re.sub(r'[\\/*?:"<>|]', '_', str(chat_id))[:50]
            path = self.out / f"links_{safe}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(dict(urls), f, indent=2, ensure_ascii=False)
        
        return dict(urls)
    
    # ========================================================
    #                   FULL ATTACK — حمله کامل
    # ========================================================
    async def full_attack(self, target: str):
        log(f"{R}{BO}{'='*60}{RS}", R)
        log(f"{R}{BO}🔥 FULL ATTACK MODE ENGAGED{RS}", R)
        log(f"{R}{BO}Target: {target}{RS}", R)
        log(f"{R}{BO}{'='*60}{RS}", R)
        
        # مرحله ۰: جوین
        chat_id = await self.join(target)
        if not chat_id:
            return False
        
        self.stats["targets_attacked"] += 1
        results = {}
        
        # مرحله ۱: اطلاعات
        log(f"\n{C}{BO}[1/8] Gathering intel...{RS}", C)
        results["info"] = await self.get_info(chat_id)
        
        # مرحله ۲: اسکراپ اعضا
        log(f"\n{C}{BO}[2/8] Scraping members...{RS}", C)
        results["members"] = await self.scrape_members(chat_id)
        
        # مرحله ۳: استخراج شماره تلفن
        log(f"\n{C}{BO}[3/8] Extracting phone numbers...{RS}", C)
        results["phones"] = await self.extract_phones(chat_id)
        
        # مرحله ۴: ادمین‌ها
        log(f"\n{C}{BO}[4/8] Finding admins...{RS}", C)
        results["admins"] = await self.admins(chat_id)
        
        # مرحله ۵: پیام‌ها
        log(f"\n{C}{BO}[5/8] Collecting messages...{RS}", C)
        results["messages"] = await self.collect_messages(chat_id, limit=150)
        
        # مرحله ۶: استخراج لینک‌ها
        log(f"\n{C}{BO}[6/8] Extracting links...{RS}", C)
        results["links"] = await self.extract_links(chat_id)
        
        # مرحله ۷: ارسال پیام تستی
        log(f"\n{C}{BO}[7/8] Sending assessment notice...{RS}", C)
        await self.flood(chat_id, "🔐 Security Assessment In Progress", count=3)
        
        # مرحله ۸: منشن
        log(f"\n{C}{BO}[8/8] Mass mention action...{RS}", C)
        await self.mass_mention(chat_id, limit=30, msg="🔐 Security Assessment Notice")
        
        # ذخیره نتایج نهایی
        result_file = self.out / f"FULL_ATTACK_{chat_id}_{int(time.time())}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "target": target,
                "chat_id": chat_id,
                "timestamp": datetime.now().isoformat(),
                "stats": self.stats,
                "summary": {
                    "members": len(results.get("members", [])),
                    "phones": len(results.get("phones", [])),
                    "admins": len(results.get("admins", [])),
                    "messages": len(results.get("messages", [])),
                    "links": sum(len(v) for v in results.get("links", {}).values()),
                }
            }, f, indent=2, ensure_ascii=False)
        
        # گزارش نهایی
        print(f"""
{BO}{R}╔══════════════════════════════════════════════╗{RS}
{BO}{R}║{RS}  {M}🔥 ATTACK COMPLETE — RESULTS{RS}               {R}{BO}║{RS}
{BO}{R}╠══════════════════════════════════════════════╣{RS}
{BO}{R}║{RS}  {G}Target:{RS}     {Y}{target}{RS}
{BO}{R}║{RS}  {G}Chat ID:{RS}    {C}{chat_id}{RS}
{BO}{R}║{RS}  {G}Members:{RS}    {len(results.get('members', []))}
{BO}{R}║{RS}  {G}Phones:{RS}     {len(results.get('phones', []))}
{BO}{R}║{RS}  {G}Admins:{RS}     {len(results.get('admins', []))}
{BO}{R}║{RS}  {G}Messages:{RS}   {len(results.get('messages', []))}
{BO}{R}║{RS}  {G}Links:{RS}      {sum(len(v) for v in results.get('links', {}).values())}
{BO}{R}║{RS}  {G}Report:{RS}    {result_file.name}
{BO}{R}╚══════════════════════════════════════════════╝{RS}
""")
        
        return True
    
    # ========================================================
    #                   FIND SIMILAR GROUPS
    # ========================================================
    async def find_similar(self, chat_id):
        """پیدا کردن گروه‌های مشابه با استفاده از description"""
        info = await self.get_info(chat_id)
        desc = info.get("description", "")
        
        if not desc:
            log(f"{Y}⚠ No description to search from{RS}", Y)
            return []
        
        # استخراج کلمات کلیدی
        keywords = [w for w in desc.split() if len(w) > 3][:10]
        log(f"{C}[*] Searching similar groups using keywords: {keywords[:5]}...{RS}", C)
        
        # استفاده از search public chats
        similar = []
        for kw in keywords[:3]:
            try:
                async for chat in self.app.search_global(kw, limit=5):
                    if chat.id != chat_id and hasattr(chat, 'username') and chat.username:
                        similar.append({
                            "title": chat.title,
                            "username": chat.username,
                            "id": chat.id,
                            "members": chat.members_count or 0,
                        })
            except:
                pass
        
        if similar:
            safe = re.sub(r'[\\/*?:"<>|]', '_', str(chat_id))[:50]
            path = self.out / f"similar_groups_{safe}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(similar, f, indent=2, ensure_ascii=False)
            log(f"{G}✓ Found {len(similar)} similar groups → {path.name}{RS}", G)
        
        return similar


# ============================================================
#                   توابع کمکی
# ============================================================
def log(msg: str, color=W):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"{color}{BO}[{t}]{RS} {color}{msg}{RS}")

def banner():
    os.system("clear" if os.name == "posix" else "cls")
    print(f"""
{BO}{R}████████╗ ██████╗       █████╗ ████████╗██╗  ██╗███████╗██████╗ {RS}
{BO}{R}╚══██╔══╝██╔════╝      ██╔══██╗╚══██╔══╝██║ ██╔╝██╔════╝██╔══██╗{RS}
{BO}{R}   ██║   ██║  ███╗     ███████║   ██║   █████╔╝ █████╗  ██████╔╝{RS}
{BO}{R}   ██║   ██║   ██║     ██╔══██║   ██║   ██╔═██╗ ██╔══╝  ██╔══██╗{RS}
{BO}{R}   ██║   ╚██████╔╝     ██║  ██║   ██║   ██║  ██╗███████╗██║  ██║{RS}
{BO}{R}   ╚═╝    ╚═════╝      ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝{RS}
{BO}{M}                    v4.0 — KALI EDITION{RS}
{BO}{W}       Telegram Group Security Assessment Framework{RS}
{BO}{Y}         For Authorized Penetration Testing Only{RS}
{RS}""")

# ============================================================
#                   MAIN MENU
# ============================================================
async def main():
    banner()
    
    # تایید مسئولیت
    print(f"{R}{BO}⚠⚠⚠  RESPONSIBILITY ACKNOWLEDGMENT  ⚠⚠⚠{RS}")
    print(f"{Y}You confirmed responsibility for all actions.{RS}")
    print(f"{Y}Only use on systems you own or have written permission.{RS}\n")
    
    atker = TGAtker()
    try:
        await atker.start()
        
        while True:
            print(f"""
{BO}{C}╔══════════════════════════════════════════════╗{RS}
{BO}{C}║{RS}              {M}{BO}MAIN MENU{RS}                    {C}{BO}║{RS}
{BO}{C}╠══════════════════════════════════════════════╣{RS}
{BO}{C}║{RS}  {R}01{RS}  🔥 Full Attack (All-in-1)            {C}{BO}║{RS}
{BO}{C}║{RS}  ──────────────────────────────────────── {C}{BO}║{RS}
{BO}{C}║{RS}  {Y}02{RS}  📋 Get Group Info                  {C}{BO}║{RS}
{BO}{C}║{RS}  {Y}03{RS}  👥 Scrape Members                  {C}{BO}║{RS}
{BO}{C}║{RS}  {Y}04{RS}  📞 Extract Phone Numbers            {C}{BO}║{RS}
{BO}{C}║{RS}  {Y}05{RS}  🔍 Find Admins                     {C}{BO}║{RS}
{BO}{C}║{RS}  {Y}06{RS}  💬 Collect Messages                {C}{BO}║{RS}
{BO}{C}║{RS}  {Y}07{RS}  🔗 Extract Links                   {C}{BO}║{RS}
{BO}{C}║{RS}  ──────────────────────────────────────── {C}{BO}║{RS}
{BO}{C}║{RS}  {M}08{RS}  📢 Flood / Spam Test              {C}{BO}║{RS}
{BO}{C}║{RS}  {M}09{RS}  📣 Mass Mention                    {C}{BO}║{RS}
{BO}{C}║{RS}  ──────────────────────────────────────── {C}{BO}║{RS}
{BO}{C}║{RS}  {R}10{RS}  🚫 Kick/Ban User (Admin)           {C}{BO}║{RS}
{BO}{C}║{RS}  {R}11{RS}  🧹 Purge All Members (Admin)       {C}{BO}║{RS}
{BO}{C}║{RS}  {R}12{RS}  ✏️ Change Group Title (Admin)      {C}{BO}║{RS}
{BO}{C}║{RS}  {R}13{RS}  🖼️ Change Group Photo (Admin)      {C}{BO}║{RS}
{BO}{C}║{RS}  {R}14{RS}  🗑️ Delete Messages (Admin)         {C}{BO}║{RS}
{BO}{C}║{RS}  ──────────────────────────────────────── {C}{BO}║{RS}
{BO}{C}║{RS}  {G}15{RS}  🔄 Join Group by Link              {C}{BO}║{RS}
{BO}{C}║{RS}  {G}16{RS}  🚪 Leave Group                    {C}{BO}║{RS}
{BO}{C}║{RS}  {G}17{RS}  🔎 Find Similar Groups             {C}{BO}║{RS}
{BO}{C}║{RS}  ──────────────────────────────────────── {C}{BO}║{RS}
{BO}{C}║{RS}  {R}00{RS}  ❌ Exit                           {C}{BO}║{RS}
{BO}{C}╚══════════════════════════════════════════════╝{RS}
""")
            
            ch = input(f"{R}{BO}❯ {RS}{C}Select option{RS}{R}:{RS} ").strip()
            
            if ch == "00":
                break
            
            elif ch == "01":
                t = input(f"{Y}❯ Target (link/username/id): {RS}").strip()
                if t: await atker.full_attack(t)
            
            elif ch in ["02","03","04","05","06","07"]:
                t = input(f"{Y}❯ Target: {RS}").strip()
                if not t: continue
                cid = await atker.join(t) or await atker._resolve_id(t)
                if not cid: continue
                
                if ch == "02": await atker.get_info(cid)
                elif ch == "03": await atker.scrape_members(cid)
                elif ch == "04": await atker.extract_phones(cid)
                elif ch == "05": await atker.admins(cid)
                elif ch == "06":
                    lim = int(input(f"{Y}❯ Message count (200): {RS}") or "200")
                    await atker.collect_messages(cid, lim)
                elif ch == "07":
                    lim = int(input(f"{Y}❯ Messages to scan (300): {RS}") or "300")
                    await atker.extract_links(cid, lim)
            
            elif ch == "08":
                t = input(f"{Y}❯ Target: {RS}").strip()
                if not t: continue
                cid = await atker.join(t) or await atker._resolve_id(t)
                if not cid: continue
                cnt = int(input(f"{Y}❯ Message count (10): {RS}") or "10")
                txt = input(f"{Y}❯ Message text: {RS}") or "Test"
                await atker.flood(cid, txt, cnt)
            
            elif ch == "09":
                t = input(f"{Y}❯ Target: {RS}").strip()
                if not t: continue
                cid = await atker.join(t) or await atker._resolve_id(t)
                if not cid: continue
                lim = int(input(f"{Y}❯ Max mentions (50): {RS}") or "50")
                msg = input(f"{Y}❯ Optional message: {RS}").strip()
                await atker.mass_mention(cid, lim, msg)
            
            elif ch == "10":
                t = input(f"{Y}❯ Group target: {RS}").strip()
                uid = int(input(f"{Y}❯ User ID to kick: {RS}").strip())
                cid = await atker._resolve_id(t)
                if cid: await atker.admin_kick(cid, uid)
            
            elif ch == "11":
                t = input(f"{Y}❯ Group target: {RS}").strip()
                cid = await atker._resolve_id(t)
                if cid: await atker.admin_purge_all(cid)
            
            elif ch == "12":
                t = input(f"{Y}❯ Group target: {RS}").strip()
                title = input(f"{Y}❯ New title: {RS}").strip()
                cid = await atker._resolve_id(t)
                if cid and title: await atker.admin_rename(cid, title)
            
            elif ch == "13":
                t = input(f"{Y}❯ Group target: {RS}").strip()
                path = input(f"{Y}❯ Photo path: {RS}").strip()
                cid = await atker._resolve_id(t)
                if cid and path: await atker.admin_set_photo(cid, path)
            
            elif ch == "14":
                t = input(f"{Y}❯ Group target: {RS}").strip()
                ids = input(f"{Y}❯ Message IDs (comma): {RS}").strip()
                cid = await atker._resolve_id(t)
                if cid and ids:
                    msg_ids = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]
                    if msg_ids: await atker.admin_delete_msgs(cid, msg_ids)
            
            elif ch == "15":
                link = input(f"{Y}❯ Invite link: {RS}").strip()
                if link: await atker.join(link)
            
            elif ch == "16":
                t = input(f"{Y}❯ Target to leave: {RS}").strip()
                cid = await atker._resolve_id(t)
                if cid: await atker.leave(cid)
            
            elif ch == "17":
                t = input(f"{Y}❯ Target group (to find similar): {RS}").strip()
                cid = await atker._resolve_id(t)
                if cid: await atker.find_similar(cid)
            
            else:
                log(f"{R}Invalid option{RS}", R)
            
            print()
    
    except KeyboardInterrupt:
        log(f"\n{Y}⚠ Interrupted by user{RS}", Y)
    except Exception as e:
        log(f"{R}⚠ Fatal: {e}{RS}", R)
        import traceback
        traceback.print_exc()
    finally:
        await atker.stop()
        print(f"\n{BO}{M}Goodbye!{RS}")

# ============================================================
if __name__ == "__main__":
    asyncio.run(main())
