pkg install -y python
cat > ~/xor.py << 'PYEOF'
#!/usr/bin/env python3
# ============================================================
#  XOR v3 :: python core  (stdlib only, termux-friendly)
#    python xor.py          -> boot + shell
#    python xor.py !scan    -> jump to menu
# ============================================================
import os, sys, json, time, random, socket, subprocess, shutil, re
import urllib.request, urllib.error
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
CACHE = os.path.join(HOME, ".cache", "xor")
os.makedirs(CACHE, exist_ok=True)
for f in ("links", "notes", "history", "vendors", "theme"):
    p = os.path.join(CACHE, f)
    if not os.path.exists(p):
        open(p, "w").close()

RST = "\x1b[0m"; DIM = "\x1b[2m"; HI = "\x1b[1;97m"
WARN = "\x1b[1;33m"; ERR = "\x1b[1;31m"; OK = "\x1b[1;32m"

def load_theme():
    global A1, A2, A3
    t = open(os.path.join(CACHE, "theme")).read().strip()
    themes = {
        "cyan":   ("\x1b[1;36m", "\x1b[36m",  "\x1b[2;36m"),
        "green":  ("\x1b[1;32m", "\x1b[32m",  "\x1b[2;32m"),
        "purple": ("\x1b[1;35m", "\x1b[35m",  "\x1b[2;35m"),
        "red":    ("\x1b[1;31m", "\x1b[31m",  "\x1b[2;31m"),
        "amber":  ("\x1b[1;33m", "\x1b[33m",  "\x1b[2;33m"),
        "ice":    ("\x1b[1;94m", "\x1b[94m",  "\x1b[2;34m"),
    }
    A1, A2, A3 = themes.get(t, themes["cyan"])
load_theme()

UA = "Mozilla/5.0 (Linux; Android 13)"

def term_size():
    try:
        s = shutil.get_terminal_size()
        return s.columns, s.lines
    except Exception:
        return 80, 24

COLS, ROWS = term_size()

def cprint(text, color=None):
    color = color or A1
    pad = max(0, (COLS - len(text)) // 2)
    print(" " * pad + color + text + RST)

def hr(w=48):
    print("  " + A3 + "=" * w + RST)

def title(text):
    os.system("clear")
    global COLS, ROWS
    COLS, ROWS = term_size()
    print()
    cprint(text)
    hr()
    print()

def typew(text, color=None, delay=0.012):
    color = color or A2
    sys.stdout.write("  " + color)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RST + "\n")

def bar(steps=20):
    w = min(26, COLS - 8)
    for i in range(steps + 1):
        f = i * w // steps
        line = "\r  " + A3 + "[" + A1 + "#" * f + A3 + "." * (w - f) + RST + "] %3d%%" % (i * 100 // steps)
        sys.stdout.write(line); sys.stdout.flush()
        time.sleep(0.012)
    print()

def pause():
    input("  " + A3 + "[enter]" + RST)

def ask(prompt):
    try:
        return input("  " + A2 + prompt + RST + " ").strip()
    except EOFError:
        return ""

def move(r, c):
    return "\x1b[%d;%dH" % (r, c)

def http_json(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None

def http_status(url, timeout=6):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

def get(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return ""

def clipboard_set(text):
    if shutil.which("termux-clipboard-set"):
        subprocess.run(["termux-clipboard-set", text])
        print("  " + OK + "copied" + RST)
    else:
        print("  " + WARN + "no clipboard tool (pkg install termux-api)" + RST)

def open_url(url):
    if shutil.which("termux-open-url"):
        subprocess.run(["termux-open-url", url])
    else:
        print("  " + WARN + "open manually: " + url + RST)

# ---------- animation ----------
LOGO = [
    "#     #  #######  ###### ",
    " #   #  #        #     # ",
    "  # #   #####    #     # ",
    "  # #   #####    #     # ",
    " #   #  #        #     # ",
    "#     #  #######  ###### ",
]
GLYPHS = "#%&*+-=<>01XOR"

def draw_logo(glitch=False):
    pad = max(0, (COLS - 25) // 2)
    for line in LOGO:
        out = ""
        for ch in line:
            if ch == " ":
                out += " "
            elif glitch and random.random() < 0.8:
                out += HI + random.choice(GLYPHS)
            else:
                out += A1 + ch
        print(" " * pad + out + RST + "\x1b[K")

def rain(frames=35):
    chars = "01XOR#%&*+=/<>"
    heads = {}
    for c in range(1, COLS, 3):
        heads[c] = random.randint(0, ROWS)
    sys.stdout.write("\x1b[?25l")
    for _ in range(frames):
        buf = []
        for c, y in heads.items():
            if y > 6:
                buf.append(move(y - 6, c) + " ")
            if 1 <= y <= ROWS:
                buf.append(move(y, c) + HI + random.choice(chars))
            if 2 <= y <= ROWS:
                buf.append(move(y - 1, c) + A3 + random.choice(chars))
            heads[c] = random.randint(0, 4) if y > ROWS else y + 1
        sys.stdout.write("".join(buf) + RST)
        sys.stdout.flush()
        time.sleep(0.04)
    sys.stdout.write("\x1b[?25h")

def boot():
    os.system("clear")
    global COLS, ROWS
    COLS, ROWS = term_size()
    rain()
    os.system("clear")
    for _ in range(12):
        sys.stdout.write("\x1b[2J" + move(2, 1))
        draw_logo(glitch=True)
        sys.stdout.flush()
        time.sleep(0.05)
    sys.stdout.write("\x1b[2J" + move(2, 1))
    draw_logo(glitch=False)
    print()
    cprint("XOR :: eXclusive-OR terminal core  v3.0", A2)
    typew("booting xor core ...", A3); bar()
    typew("loading modules: scan / osint / gen / notes", A3); bar()
    time.sleep(0.2)
    os.system("clear")
    print()
    status_panel()
    print()
    typew("access granted - type !help for the menu", OK)

def banner_again():
    os.system("clear")
    for _ in range(8):
        sys.stdout.write("\x1b[2J" + move(2, 1))
        draw_logo(glitch=True)
        sys.stdout.flush()
        time.sleep(0.06)
    sys.stdout.write("\x1b[2J" + move(2, 1))
    draw_logo(glitch=False)
    print()
    cprint("XOR :: v3.0", A2)

# ---------- status ----------
def status_panel():
    op = os.environ.get("USER") or os.environ.get("LOGNAME") or "user"
    node = os.uname().nodename
    acc = "root (full)" if os.geteuid() == 0 else "user"
    dev = "unknown"
    try:
        out = subprocess.run(["getprop", "ro.product.model"], capture_output=True, text=True, timeout=2)
        if out.stdout.strip():
            dev = out.stdout.strip()
    except Exception:
        pass
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    osname = os.uname().sysname + " " + os.uname().release
    try:
        out = subprocess.run(["getprop", "ro.build.version.release"], capture_output=True, text=True, timeout=2)
        if out.stdout.strip():
            osname = "Android " + out.stdout.strip() + " / " + os.uname().machine
    except Exception:
        pass
    data = http_json("http://ip-api.com/json/?fields=query,country,isp", 4) or {}
    pub = data.get("query", "offline")
    cc = data.get("country", "")
    isp = data.get("isp", "-")
    rows = [
        ("OPERATOR", op + "@" + node),
        ("ACCESS", acc),
        ("DEVICE", dev),
        ("NODE", node),
        ("TIME", t),
        ("OS", osname),
        ("EXTERNAL", pub + (" [" + cc + "]" if cc else "")),
        ("ISP", isp),
    ]
    w = 44
    print("  " + A1 + "+" + "-" * (w + 2) + "+" + RST)
    for k, v in rows:
        print("  " + A1 + "|" + RST + " " + A3 + k.ljust(9) + RST + " " + A2 + str(v)[:w].ljust(w) + RST + " " + A1 + "|" + RST)
    print("  " + A1 + "+" + "-" * (w + 2) + "+" + RST)
    warns = []
    if pub == "offline":
        warns.append("no-internet")
    if not shutil.which("termux-clipboard-set"):
        warns.append("clipboard-optional-missing")
    if warns:
        print("  " + WARN + "[!] WARNINGS:" + RST + " " + ERR + " ".join(warns) + RST)
    else:
        print("  " + OK + "[ok] all systems nominal" + RST)

# ---------- net ----------
def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def read_mac_for(ip):
    try:
        with open("/proc/net/arp") as f:
            for line in f:
                parts = line.split()
                if parts and parts[0] == ip and len(parts) >= 6:
                    return parts[3]
    except Exception:
        pass
    return "--"

def vendor_lookup(mac):
    if mac in ("--", "00:00:00:00:00:00", "incomplete"):
        return "unknown"
    try:
        with open(os.path.join(CACHE, "vendors")) as f:
            for line in f:
                if line.lower().startswith(mac.lower()):
                    return line.strip().split("|", 1)[1]
    except Exception:
        pass
    v = get("https://api.macvendors.com/" + mac, 4)[:26].strip() or "unknown"
    time.sleep(0.25)
    try:
        with open(os.path.join(CACHE, "vendors"), "a") as f:
            f.write(mac + "|" + v + "\n")
    except Exception:
        pass
    return v

def lan_scan():
    base = local_ip()
    if base.startswith("127."):
        print("  " + ERR + "no network" + RST)
        return
    prefix = ".".join(base.split(".")[:3])
    print("  " + A3 + "sweeping" + RST + " " + prefix + ".0/24\n")
    hosts = []
    if shutil.which("nmap"):
        try:
            out = subprocess.run(["nmap", "-sn", prefix + ".0/24"], capture_output=True, text=True, timeout=60)
            for line in out.stdout.splitlines():
                line = line.strip()
                if line.startswith("Nmap scan report for"):
                    hosts.append(line.split()[-1].strip("()"))
        except Exception:
            pass
    else:
        print("  " + A3 + "(nmap absent - using arp cache)" + RST)
        try:
            with open("/proc/net/arp") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 6 and parts[3] not in ("00:00:00:00:00:00", "incomplete"):
                        hosts.append(parts[0])
        except Exception:
            pass
    hosts = sorted(set(hosts))
    print("  %-16s %-18s %-26s" % ("IP", "MAC", "VENDOR / DEVICE"))
    print("  " + "-" * 60)
    for ip in hosts:
        mac = read_mac_for(ip)
        vendor = vendor_lookup(mac)
        tag = " *this-device" if ip == base else ""
        print("  " + A1 + ip.ljust(16) + RST + " " + mac.ljust(18) + " " + A2 + vendor.ljust(26) + RST + OK + tag + RST)
    print("\n  " + A3 + "hosts: " + str(len(hosts)) + RST)

PORTS = [21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445, 3306, 3389, 5432, 8080, 8443]

def port_scan():
    tgt = ask("target ip/domain:")
    if not tgt:
        return
    print("  " + A3 + "scanning" + RST + " " + tgt + " (" + str(len(PORTS)) + " common ports)\n")
    for p in PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.6)
        try:
            s.connect((tgt, p))
            print("  " + OK + "open" + RST + "   " + str(p))
        except Exception:
            pass
        finally:
            s.close()

def ip_info():
    t = ask("ip or domain:")
    if not t:
        return
    d = http_json("http://ip-api.com/json/" + t) or {}
    if d.get("status") != "success":
        print("  " + ERR + "lookup failed" + RST)
        return
    for k in ("query", "country", "regionName", "city", "zip", "timezone",
              "isp", "org", "as", "reverse"):
        print("  " + A3 + k.ljust(10) + RST + " " + str(d.get(k, "-")))
    print("  " + A3 + "coords".ljust(10) + RST + " " + str(d.get("lat")) + ", " + str(d.get("lon")))
    for flag in ("mobile", "proxy", "hosting"):
        print("  " + A3 + flag.ljust(10) + RST + " " + str(d.get(flag)))

def url_info():
    u = ask("url (full http/https):")
    if not u:
        return
    code = http_status(u)
    print("  " + A3 + "status".ljust(8) + RST + " " + str(code))
    body = get(u)
    m = re.search(r"<title[^>]*>(.{0,90}?)</title>", body, re.S | re.I)
    if m:
        print("  " + A3 + "title".ljust(8) + RST + " " + m.group(1).strip())
    host = u.split("//")[-1].split("/")[0].split(":")[0]
    d = http_json("http://ip-api.com/json/" + host + "?fields=query,country,isp") or {}
    if d:
        print("  " + A3 + "host-ip".ljust(8) + RST + " " + str(d.get("query", "-")) + " [" + str(d.get("country", "")) + "] " + str(d.get("isp", "")))

# ---------- osint ----------
def deep_tiktok(username):
    d = http_json("https://www.tiktok.com/api/user/detail/?uniqueId=" + username)
    user, stats = {}, {}
    if isinstance(d, dict):
        block = d.get("userInfo") or d or {}
        user = block.get("user", {}) or block.get("userDict", {})
        stats = block.get("stats", {})
    if not user:
        code = http_status("https://www.tiktok.com/@" + username)
        if code == 200:
            print("  " + A1 + "== TIKTOK == " + RST + "(limited data - page exists)")
            print("  " + A3 + "profile".ljust(10) + RST + " https://www.tiktok.com/@" + username)
        else:
            print("  " + DIM + "TikTok: no public data (blocked/private)" + RST)
        return
    print("  " + A1 + "== TIKTOK ==" + RST)
    rows = [
        ("nickname", user.get("nickname", "-")),
        ("handle", user.get("uniqueId", username)),
        ("bio", (user.get("signature", "-") or "-")[:70]),
        ("verified", str(user.get("verified", False))),
        ("userId", user.get("id", "-")),
        ("secUid", (user.get("secUid", "-") or "-")[:34]),
        ("followers", str(stats.get("followerCount", "-"))),
        ("following", str(stats.get("followingCount", "-"))),
        ("hearts", str(stats.get("heartCount", "-"))),
        ("videos", str(stats.get("videoCount", "-"))),
    ]
    for k, v in rows:
        print("  " + A3 + k.ljust(10) + RST + " " + str(v))
    print("  " + A3 + "profile".ljust(10) + RST + " https://www.tiktok.com/@" + username)

def snowflake_date(sid):
    try:
        ts = (int(sid) >> 22) + 1420070400000
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return "-"

def deep_discord(ident):
    if not ident.isdigit():
        print("  " + DIM + "Discord: paste a numeric ID (17-20 digits) - username lookup is auth-gated" + RST)
        return
    d = http_json("https://discord.com/api/v9/users/" + ident + "/profile")
    if not d or "user" not in d:
        print("  " + DIM + "Discord: not found / blocked (needs open profile)" + RST)
        return
    u = d.get("user", {})
    print("  " + A1 + "== DISCORD ==" + RST)
    rows = [
        ("id", u.get("id", ident)),
        ("username", u.get("username", "-")),
        ("display", u.get("global_name", "-")),
        ("bot", str(u.get("bot", False))),
        ("banner", (u.get("banner") or "-")[:34]),
        ("avatar", (u.get("avatar") or "-")[:34]),
        ("created", snowflake_date(ident)),
    ]
    for k, v in rows:
        print("  " + A3 + k.ljust(10) + RST + " " + str(v))
    conns = d.get("connected_accounts", [])
    if conns:
        print("  " + A3 + "linked".ljust(10) + RST + " " + ", ".join(str(c.get("type", "?")) for c in conns[:8]))

SITES = [
    ("Instagram", "https://www.instagram.com/"),
    ("GitHub", "https://github.com/"),
    ("Reddit", "https://www.reddit.com/user/"),
    ("Telegram", "https://t.me/"),
    ("Twitch", "https://www.twitch.tv/"),
    ("Snapchat", "https://www.snapchat.com/add/"),
    ("Pinterest", "https://www.pinterest.com/"),
    ("Spotify", "https://open.spotify.com/user/"),
    ("Steam", "https://steamcommunity.com/id/"),
    ("Facebook", "https://www.facebook.com/"),
    ("Replit", "https://replit.com/@"),
    ("YouTube", "https://www.youtube.com/@"),
    ("X", "https://x.com/"),
    ("Roblox", "https://www.roblox.com/users/profile?username="),
    ("Xbox", "https://www.xbox.com/en-US/search?q="),
]

def username_lookup():
    u = ask("username:")
    if not u:
        return
    mode = ask("deep (d) or quick (q)? [d]:") or "d"
    print()
    if mode == "d":
        deep_tiktok(u)
        print()
        deep_discord(u)
        print()
    hits = 0
    for name, url in SITES:
        code = http_status(url + u)
        if code == 200:
            print("  " + OK + "[+] " + name.ljust(11) + RST + " " + url + u)
            hits += 1
        elif code == 404:
            print("  " + DIM + "[-] " + name.ljust(11) + RST + " none")
        else:
            print("  " + WARN + "[?] " + name.ljust(11) + RST + " http " + str(code))
        time.sleep(0.15)
    print("\n  " + A3 + "hits: " + str(hits) + RST)

def email_lookup():
    e = ask("email address:")
    if not e:
        return
    ok = re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", e)
    print("  " + A3 + "format".ljust(11) + RST + " " + ("valid" if ok else "suspicious"))
    d = http_json("https://emailrep.io/" + e)
    if d:
        for k in ("reputation", "suspicious", "blacklisted", "malicious_activity"):
            print("  " + A3 + k.ljust(11) + RST + " " + str(d.get(k, "-")))
        prof = d.get("details", {}).get("profiles", [])
        if prof:
            print("  " + A3 + "profiles".ljust(11) + RST + " " + ", ".join(str(p) for p in prof[:10]))
    else:
        print("  " + WARN + "no response (rate limited or offline)" + RST)

def osint_menu():
    while True:
        title("OSINT MENU")
        print("  " + A1 + "[1]" + RST + " IP lookup        (geo / isp / proxy)")
        print("  " + A1 + "[2]" + RST + " URL lookup       (status / title / ip)")
        print("  " + A1 + "[3]" + RST + " email lookup     (reputation)")
        print("  " + A1 + "[4]" + RST + " username search  (TikTok + Discord deep, 15 quick)")
        print("  " + A1 + "[0]" + RST + " back\n")
        c = input("  xor@osint > ").strip()
        if c == "1":
            os.system("clear"); ip_info(); pause()
        elif c == "2":
            os.system("clear"); url_info(); pause()
        elif c == "3":
            os.system("clear"); email_lookup(); pause()
        elif c == "4":
            os.system("clear"); username_lookup(); pause()
        elif c == "0":
            break

def scan_menu():
    while True:
        title("SCAN MENU")
        print("  " + A1 + "[1]" + RST + " LAN device sweep  (ip + mac + vendor)")
        print("  " + A1 + "[2]" + RST + " port scan         (common ports)")
        print("  " + A1 + "[3]" + RST + " IP intel")
        print("  " + A1 + "[4]" + RST + " website intel")
        print("  " + A1 + "[0]" + RST + " back\n")
        c = input("  xor@scan > ").strip()
        if c == "1":
            os.system("clear"); lan_scan(); pause()
        elif c == "2":
            os.system("clear"); port_scan(); pause()
        elif c == "3":
            os.system("clear"); ip_info(); pause()
        elif c == "4":
            os.system("clear"); url_info(); pause()
        elif c == "0":
            break

# ---------- generators (random TEST data only) ----------
FIRST = "James Maria Liam Aisha Noah Zoe Ethan Maya Kai Nova Luis Sara Omar Hana".split()
LAST = "Carter Silva Chen Okafor Novak Reyes Kim Frost Adler Vance Moreau Ito".split()
STREETS = "Oak Maple Cedar Ridge Pine Bay Hill Lake View Park Stone Vine".split()
CITY = "Toronto Berlin Miami Austin Osaka Lisbon Accra Manila Kyiv Lima Oslo".split()

def rname():
    return random.choice(FIRST) + " " + random.choice(LAST)

def luhn_card():
    n = "".join(random.choice("0123456789") for _ in range(15))
    total = 0
    for i, ch in enumerate(n):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    check = (10 - total % 10) % 10
    return "4" + n[:3] + " " + n[3:7] + " " + n[7:11] + " " + n[11:15] + " " + str(check)

def gen_menu():
    while True:
        title("GENERATORS  (random test data, not real people)")
        print("  " + A1 + "[1]" + RST + " name      " + A1 + "[2]" + RST + " address     " + A1 + "[3]" + RST + " phone")
        print("  " + A1 + "[4]" + RST + " email     " + A1 + "[5]" + RST + " ipv4        " + A1 + "[6]" + RST + " test card")
        print("  " + A1 + "[7]" + RST + " ssn-fmt   " + A1 + "[8]" + RST + " crypto addr " + A1 + "[9]" + RST + " password")
        print("  " + A1 + "[0]" + RST + " back\n")
        c = input("  xor@gen > ").strip()
        out = None
        if c == "1":
            out = rname()
        elif c == "2":
            out = "%d %s St, %s %05d" % (random.randint(100, 9999), random.choice(STREETS), random.choice(CITY), random.randint(10000, 99999))
        elif c == "3":
            out = "+1 (%03d) %03d-%04d" % (random.randint(200, 499), random.randint(0, 999), random.randint(0, 9999))
        elif c == "4":
            out = rname().lower().replace(" ", ".") + "%04d@example.test" % random.randint(0, 9999)
        elif c == "5":
            out = "%d.%d.%d.%d" % (random.randint(1, 223), random.randint(0, 255), random.randint(0, 255), random.randint(1, 254))
        elif c == "6":
            out = luhn_card() + "  (test, luhn-valid)"
        elif c == "7":
            out = "%03d-%02d-%04d  (random, not a real person)" % (random.randint(100, 899), random.randint(1, 99), random.randint(0, 9999))
        elif c == "8":
            pfx = "bc1q" if random.randint(0, 1) else "0x"
            n = 38 if pfx == "bc1q" else 40
            out = pfx + "".join(random.choice("0123456789abcdef") for _ in range(n))
        elif c == "9":
            pool = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789!@#$%"
            out = "".join(random.choice(pool) for _ in range(16))
        elif c == "0":
            break
        if out:
            print("\n  " + A2 + out + RST)
            pause()

# ---------- links + notes ----------
def notes_menu():
    linksp = os.path.join(CACHE, "links")
    notesp = os.path.join(CACHE, "notes")
    while True:
        title("LINKS + NOTES")
        print("  LINKS  " + A1 + "[1]" + RST + " add  " + A1 + "[2]" + RST + " open  " + A1 + "[3]" + RST + " copy  " + A1 + "[4]" + RST + " list  " + A1 + "[5]" + RST + " del")
        print("  NOTES  " + A1 + "[6]" + RST + " add  " + A1 + "[7]" + RST + " view  " + A1 + "[8]" + RST + " copy  " + A1 + "[9]" + RST + " del")
        print("  " + A1 + "[0]" + RST + " back\n")
        c = input("  xor@lib > ").strip()
        if c == "1":
            v = ask("link url:")
            if v:
                open(linksp, "a").write(v + "\n")
                print("  " + OK + "saved" + RST)
        elif c in ("2", "3", "4", "5"):
            lines = open(linksp).read().splitlines()
            if c == "4":
                if not lines:
                    print("  " + DIM + "empty" + RST)
                for i, l in enumerate(lines, 1):
                    print("  " + str(i) + ". " + l)
            elif not lines:
                print("  " + DIM + "empty" + RST)
            else:
                for i, l in enumerate(lines, 1):
                    print("  " + str(i) + ". " + l)
                n = ask("number:")
                if n.isdigit() and 0 < int(n) <= len(lines):
                    v = lines[int(n) - 1]
                    if c == "2":
                        open_url(v)
                    elif c == "3":
                        clipboard_set(v)
                    else:
                        del lines[int(n) - 1: int(n)]
                        open(linksp, "w").write("\n".join(lines) + ("\n" if lines else ""))
                        print("  " + OK + "deleted" + RST)
        elif c == "6":
            v = ask("note text:")
            if v:
                open(notesp, "a").write(datetime.now().strftime("%m-%d %H:%M") + " | " + v + "\n")
                print("  " + OK + "saved" + RST)
        elif c in ("7", "8", "9"):
            lines = open(notesp).read().splitlines()
            if not lines:
                print("  " + DIM + "empty" + RST)
            else:
                for i, l in enumerate(lines, 1):
                    print("  " + str(i) + ". " + l)
                if c in ("8", "9"):
                    n = ask("number:")
                    if n.isdigit() and 0 < int(n) <= len(lines):
                        if c == "8":
                            clipboard_set(lines[int(n) - 1])
                        else:
                            del lines[int(n) - 1: int(n)]
                            open(notesp, "w").write("\n".join(lines) + ("\n" if lines else ""))
                            print("  " + OK + "deleted" + RST)
        elif c == "0":
            break

# ---------- extras ----------
def theme_menu():
    title("THEME")
    print("  " + A1 + "[1]" + RST + " cyan  " + A1 + "[2]" + RST + " green  " + A1 + "[3]" + RST + " purple  " + A1 + "[4]" + RST + " red  " + A1 + "[5]" + RST + " amber  " + A1 + "[6]" + RST + " ice\n")
    c = input("  xor@theme > ").strip()
    names = {"1": "cyan", "2": "green", "3": "purple", "4": "red", "5": "amber", "6": "ice"}
    if c in names:
        open(os.path.join(CACHE, "theme"), "w").write(names[c])
        load_theme()
        print("  " + OK + "theme applied" + RST)

def sysinfo():
    title("SYSTEM")
    mem = "-"
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    mem = line.split()[1] + " kB total"
                    break
    except Exception:
        pass
    du = shutil.disk_usage(HOME)
    cache_size = sum(
        os.path.getsize(os.path.join(CACHE, f))
        for f in os.listdir(CACHE)
        if os.path.isfile(os.path.join(CACHE, f))
    )
    rows = [
        ("memory", mem),
        ("storage", str(du.used // (1 << 30)) + "G used / " + str(du.total // (1 << 30)) + "G"),
        ("cpu", os.uname().machine),
        ("python", sys.version.split()[0]),
        ("local-ip", local_ip()),
        ("cache", str(cache_size) + " bytes"),
    ]
    for k, v in rows:
        print("  " + A3 + k.ljust(10) + RST + " " + str(v))

def show_help():
    os.system("clear")
    print()
    cprint("XOR MENU")
    hr()
    print()
    print("  " + A1 + "[1]" + RST + " !scan    LAN sweep / port scan / IP + site intel")
    print("  " + A1 + "[2]" + RST + " !osint   IP / URL / email / username (TikTok + Discord deep)")
    print("  " + A1 + "[3]" + RST + " !gen     names, addresses, test cards, crypto, passwords")
    print("  " + A1 + "[4]" + RST + " !notes   links + notes: add / open / copy / view / del")
    print()
    print("  " + A2 + "extra" + RST + "  !theme  !sys  !banner  !hist  !cache  !clear  !exit")
    print("  " + A2 + "tip" + RST + "    any shell command typed here runs directly\n")

def prompt_loop():
    while True:
        try:
            cmd = input("\n  " + A1 + "xor@xor" + RST + " " + A3 + "~" + RST + " ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  " + A1 + "bye" + RST)
            break
        if not cmd:
            continue
        with open(os.path.join(CACHE, "history"), "a") as f:
            f.write(cmd + "\n")
        if cmd in ("!help", "!", "help"):
            show_help()
        elif cmd in ("!scan", "!1"):
            scan_menu()
        elif cmd in ("!osint", "!2"):
            osint_menu()
        elif cmd in ("!gen", "!3"):
            gen_menu()
        elif cmd in ("!notes", "!links", "!4"):
            notes_menu()
        elif cmd == "!theme":
            theme_menu()
        elif cmd == "!sys":
            sysinfo()
        elif cmd == "!banner":
            banner_again()
        elif cmd in ("!hist", "!history"):
            lines = open(os.path.join(CACHE, "history")).read().splitlines()[-20:]
            for i, l in enumerate(lines, 1):
                print("  " + str(i) + ". " + l)
        elif cmd == "!cache":
            for f in sorted(os.listdir(CACHE)):
                print("  " + f)
        elif cmd == "!clear":
            os.system("clear")
        elif cmd in ("!exit", "!quit", "exit", "quit"):
            print("  " + A1 + "bye" + RST)
            break
        else:
            if shutil.which(cmd.split()[0]):
                os.system(cmd)
            else:
                print("  " + WARN + "[?]" + RST + " unknown command: " + cmd + "  (!help)")

def main():
    jump = {
        "scan": scan_menu, "!scan": scan_menu,
        "osint": osint_menu, "!osint": osint_menu,
        "gen": gen_menu, "!gen": gen_menu,
        "notes": notes_menu, "!notes": notes_menu,
        "-h": show_help, "--help": show_help,
    }
    if len(sys.argv) > 1 and sys.argv[1] in jump:
        jump[sys.argv[1]]()
        return
    boot()
    prompt_loop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + RST + "bye")
PYEOF
chmod +x ~/xor.py
python ~/xor.py
