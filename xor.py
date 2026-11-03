#!/usr/bin/env python3
# XOR — purple terminal toolkit for Termux
# Python standard library only. Use scans only on networks/systems you own or have permission to test.

import os, sys, json, time, random, socket, platform, subprocess, re, ipaddress, ssl
import urllib.request, urllib.error
from datetime import datetime
from urllib.parse import urlparse

APP = "XOR"
VERSION = "1.0"
BASE = os.path.join(os.path.expanduser("~"), ".xor")
DATA_FILE = os.path.join(BASE, "xor_data.json")

# ANSI palette: purple / violet / black / grey
P = "\033[38;5;141m"
V = "\033[38;5;99m"
L = "\033[38;5;183m"
W = "\033[97m"
G = "\033[38;5;245m"
R = "\033[38;5;203m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"

def color(text, c=P):
    return f"{c}{text}{RESET}"

def pause():
    input(color("\n[ press ENTER ]", G))

def line(ch="─", width=58):
    print(color(ch * width, V))

def typewrite(text, delay=0.006, c=P):
    for ch in str(text):
        print(c + ch + RESET, end="", flush=True)
        time.sleep(delay)
    print()

def safe_input(prompt):
    try:
        return input(color(prompt, L)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""

def load_data():
    os.makedirs(BASE, exist_ok=True)
    default = {"notes": [], "links": [], "history": [], "theme": "purple"}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            for k, v in default.items():
                saved.setdefault(k, v)
            return saved
    except (OSError, ValueError):
        pass
    return default

DATA = load_data()

def save_data():
    os.makedirs(BASE, exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)

def record_history(command):
    DATA["history"].append({"command": command, "time": datetime.now().isoformat(timespec="seconds")})
    DATA["history"] = DATA["history"][-100:]
    save_data()

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def banner():
    print(color(r"""
██╗  ██╗ ██████╗ ██████╗
╚██╗██╔╝██╔═══██╗██╔══██╗
 ╚███╔╝ ██║   ██║██████╔╝
 ██╔██╗ ██║   ██║██╔══██╗
██╔╝ ██╗╚██████╔╝██║  ██║
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝""", P))
    print(color("          X O R  /  OPERATOR TOOLKIT", L))
    print(color("          TERMUX EDITION  •  v" + VERSION, G))
    line()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("1.1.1.1", 80))
        return s.getsockname()[0]
    except OSError:
        return "Unavailable"
    finally:
        s.close()

def get_android_model():
    if "ANDROID_ROOT" not in os.environ and "TERMUX_VERSION" not in os.environ:
        return platform.node() or "Unknown device"
    try:
        model = subprocess.check_output(["getprop", " ro.product.model".strip()], text=True, timeout=2).strip()
        return model or "Android device"
    except Exception:
        return "Android device"

def boot():
    clear()
    banner()
    steps = [
        "Initializing XOR runtime",
        "Loading local operator profile",
        "Mounting persistent cache",
        "Checking terminal environment",
        "Preparing command interface",
    ]
    for item in steps:
        print(color("[", V) + color(" OK ", L) + color("] ", V) + color(item, W))
        time.sleep(0.22)
    try:
        uname = platform.system() + " " + platform.release()
    except Exception:
        uname = "Unknown"
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    info = [
        ("STATUS", "ONLINE"),
        ("OPERATOR.ACCESS", "LOCAL SESSION"),
        ("DEVICE", get_android_model()),
        ("NODE", socket.gethostname()),
        ("TIME", now),
        ("OS", uname),
        ("LOCAL.IP", get_local_ip()),
        ("CACHE", "READY  •  " + BASE),
    ]
    line("═")
    for k, v in info:
        print(color("  " + k.ljust(17), V) + color(v, W))
    line("═")
    print(color("  WARNING: Use network tools only with permission.", R))
    print(color("  OSINT tools use public information only.", G))
    line()
    typewrite("XOR READY. TYPE !help TO VIEW COMMANDS.", 0.012, L)
    print(color("\n  xor@xor:~$ ", P), end="", flush=True)

def help_menu():
    clear(); banner()
    print(color(" COMMAND DIRECTORY", L)); line()
    rows = [
        ("!scan", "LAN discovery, host details, authorized port check"),
        ("!osint", "Public IP, URL, email and username lookups"),
        ("!gen", "Synthetic test data generators"),
        ("!notes", "Create, read, edit, delete and search notes"),
        ("!links", "Save, list, copy and open useful links"),
        ("!system", "Device, network, storage and runtime details"),
        ("!history", "Recent commands"),
        ("!settings", "Theme and animation preferences"),
        ("!clear", "Clear terminal"),
        ("!help", "Show this menu"),
        ("!exit", "Close XOR"),
    ]
    for cmd, desc in rows:
        print("  " + color(cmd.ljust(13), P) + color(desc, W))
    line()
    print(color("Tip: menus also accept their command name without '!'.", G))

def fetch(url, method="GET", timeout=7, headers=None):
    req = urllib.request.Request(url, method=method, headers=headers or {"User-Agent": "XOR-Termux/1.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as response:
        return response.status, response.headers, response.read(16000)

def public_ip_lookup(value):
    try:
        ip = ipaddress.ip_address(value)
        if not ip.is_global:
            print(color("That is not a public routable IP address.", R)); return
    except ValueError:
        print(color("Invalid IP address.", R)); return
    try:
        status, _, body = fetch("https://ipwho.is/" + value)
        data = json.loads(body.decode("utf-8", "replace"))
        if not data.get("success", True):
            print(color("Lookup provider could not return details.", R)); return
        for k in ("ip", "type", "continent", "country", "region", "city", "connection", "timezone"):
            val = data.get(k)
            if isinstance(val, dict):
                val = ", ".join(str(x) for x in val.values() if x)
            if val:
                print(color("  " + k.upper().ljust(14), V) + color(str(val), W))
    except Exception as e:
        print(color("Lookup failed: " + str(e), R))

def url_lookup(raw):
    raw = raw if "://" in raw else "https://" + raw
    parsed = urlparse(raw)
    host = parsed.hostname
    if not host:
        print(color("That URL/host doesn't look valid.", R)); return
    print(color("\n[ URL INTELLIGENCE ]", L)); line()
    print(color("HOST       ", V) + color(host, W))
    print(color("SCHEME     ", V) + color(parsed.scheme, W))
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        ips = sorted({x[4][0] for x in infos})
        print(color("DNS        ", V) + color(", ".join(ips), W))
    except Exception as e:
        print(color("DNS        ", V) + color("Lookup failed: " + str(e), R))
    try:
        status, headers, _ = fetch(raw, method="HEAD", timeout=7)
        print(color("HTTP       ", V) + color(str(status), W))
        for key in ("server", "content-type", "content-length", "last-modified"):
            if headers.get(key):
                print(color(key.upper().ljust(11), V) + color(headers.get(key), W))
    except Exception as e:
        print(color("HTTP       ", V) + color("Could not retrieve headers: " + str(e), G))

def email_lookup(addr):
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", addr):
        print(color("Email format appears invalid.", R)); return
    domain = addr.rsplit("@", 1)[1].lower()
    print(color("FORMAT     ", V) + color("Valid-looking syntax", W))
    print(color("DOMAIN     ", V) + color(domain, W))
    try:
        records = socket.getaddrinfo(domain, 25, type=socket.SOCK_STREAM)
        print(color("DOMAIN DNS ", V) + color("Resolves", W))
    except Exception:
        print(color("DOMAIN DNS ", V) + color("No DNS result (or network unavailable)", G))
    print(color("LIMIT      ", V) + color("No mailbox delivery or ownership verification is performed.", G))

PLATFORMS = {
    "TikTok": "https://www.tiktok.com/@{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Roblox": "https://www.roblox.com/search/users?keyword={}",
    "X": "https://x.com/{}",
    "GitHub": "https://github.com/{}",
    "Reddit": "https://www.reddit.com/user/{}/",
    "Twitch": "https://www.twitch.tv/{}",
    "YouTube": "https://www.youtube.com/@{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Facebook": "https://www.facebook.com/{}",
}

def username_lookup(username):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,30}", username):
        print(color("Use 1–30 letters, numbers, dots, underscores or hyphens.", R)); return
    print(color("\nPUBLIC PROFILE URLS", L)); line()
    for name, template in PLATFORMS.items():
        print(color("  " + name.ljust(12), V) + color(template.format(username), W))
    print(color("\nThese are profile links, not confirmed account matches.", G))
    print(color("Open each platform to verify public profile details; no login bypasses.", G))

def osint_menu():
    while True:
        print(color("\n[ OSINT / PUBLIC DATA ]", L)); line()
        print("  1. Public IP lookup\n  2. URL / domain inspection\n  3. Email syntax + domain check\n  4. Username platform search\n  0. Back")
        choice = safe_input("xor@xor/osint > ")
        if choice == "1":
            public_ip_lookup(safe_input("Public IP: "))
        elif choice == "2":
            url_lookup(safe_input("URL or domain: "))
        elif choice == "3":
            email_lookup(safe_input("Email: "))
        elif choice == "4":
            username_lookup(safe_input("Username: "))
        elif choice == "0": return
        else: print(color("Unknown option.", R))
        pause()

def scan_menu():
    while True:
        print(color("\n[ NETWORK SCANNER ]", L)); line()
        print("  1. Show local network details\n  2. Discover devices on my /24 LAN\n  3. Check common ports on one authorized host\n  0. Back")
        choice = safe_input("xor@xor/scan > ")
        if choice == "1":
            ip = get_local_ip()
            print(color("LOCAL IP   ", V) + color(ip, W))
            try:
                print(color("HOSTNAME  ", V) + color(socket.gethostname(), W))
                print(color("REVERSE   ", V) + color(socket.gethostbyaddr(ip)[0], W))
            except Exception:
                pass
            print(color("NOTE      ", V) + color("Gateway/subnet details depend on Android permissions.", G))
        elif choice == "2":
            ip = get_local_ip()
            try:
                addr = ipaddress.ip_address(ip)
                if addr.version != 4 or not addr.is_private:
                    raise ValueError()
            except ValueError:
                print(color("Could not determine a private IPv4 LAN address.", R)); pause(); continue
            if safe_input("Scan your local /24 network? Type YES to confirm: ") != "YES":
                print(color("Cancelled.", G)); continue
            net = ipaddress.ip_network(str(addr) + "/24", strict=False)
            print(color("Scanning up to 254 local addresses; this may take a moment...", G))
            found = 0
            for target in net.hosts():
                host = str(target)
                s = socket.socket()
                s.settimeout(0.12)
                try:
                    s.connect((host, 80))
                    is_up = True
                except OSError:
                    is_up = False
                finally:
                    s.close()
                if is_up or host == ip:
                    found += 1
                    try: name = socket.gethostbyaddr(host)[0]
                    except Exception: name = "Unknown hostname"
                    mac = "Unavailable"
                    try:
                        with open("/proc/net/arp", "r") as f:
                            for row in f.readlines()[1:]:
                                parts = row.split()
                                if len(parts) >= 4 and parts[0] == host:
                                    mac = parts[3]; break
                    except OSError: pass
                    print(color("  " + host.ljust(16), P) + color(name, W) + color("  MAC " + mac, G))
            print(color(f"Finished. {found} responsive/known device(s) found.", L))
            print(color("Note: this lightweight check detects HTTP port 80 responders only; sleeping/firewalled devices may be missed.", G))
        elif choice == "3":
            host = safe_input("Host/IP you own or have permission to test: ")
            try:
                socket.getaddrinfo(host, None)
            except OSError:
                print(color("Host could not be resolved.", R)); pause(); continue
            if safe_input("Confirm you have permission? Type YES: ") != "YES":
                print(color("Cancelled.", G)); continue
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 8080, 8443]
            print(color("Checking a small set of common TCP ports...", G))
            for port in ports:
                s = socket.socket(); s.settimeout(0.45)
                try:
                    result = s.connect_ex((host, port))
                    if result == 0: print(color(f"  {port:<6} OPEN", L))
                except OSError: pass
                finally: s.close()
            print(color("Check complete.", G))
        elif choice == "0": return
        else: print(color("Unknown option.", R))
        pause()

def generate_menu():
    while True:
        print(color("\n[ SYNTHETIC DATA GENERATOR ]", L)); line()
        print("  1. Random name\n  2. Test email\n  3. Documentation IP\n  4. Fictional phone number\n  5. Random username\n  6. Strong random password\n  0. Back")
        c = safe_input("xor@xor/gen > ")
        first = ["Alex", "Jordan", "Riley", "Taylor", "Morgan", "Casey", "Avery", "Jamie"]
        last = ["Reed", "Hayes", "Parker", "Stone", "Brooks", "Quinn", "Blake", "Wells"]
        if c == "1": result = random.choice(first) + " " + random.choice(last)
        elif c == "2": result = "test" + str(random.randint(1000,9999)) + "@example.com"
        elif c == "3": result = random.choice(["192.0.2.", "198.51.100.", "203.0.113."]) + str(random.randint(1,254))
        elif c == "4": result = "+1-202-555-" + str(random.randint(1000,1999))
        elif c == "5": result = random.choice(first).lower() + str(random.randint(10,999))
        elif c == "6": result = "".join(random.SystemRandom().choice("ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*") for _ in range(20))
        elif c == "0": return
        else: print(color("Unknown option.", R)); continue
        print(color("\n  GENERATED: ", V) + color(result, W))
        print(color("  Synthetic/demo data only — not a real person's details.", G))
        if safe_input("Copy to clipboard if Termux:API is installed? (y/N): ").lower() == "y":
            copy_text(result)
        pause()

def copy_text(text):
    try:
        p = subprocess.run(["termux-clipboard-set"], input=text, text=True, timeout=3)
        if p.returncode == 0: print(color("Copied to clipboard.", L)); return
    except Exception: pass
    print(color("Clipboard tool unavailable. Select and copy the text above.", G))

def notes_menu():
    while True:
        print(color("\n[ NOTES ]", L)); line()
        print("  1. Create note\n  2. List / read notes\n  3. Search notes\n  4. Edit note\n  5. Delete note\n  0. Back")
        c = safe_input("xor@xor/notes > ")
        notes = DATA["notes"]
        if c == "1":
            title = safe_input("Title: ")
            body = safe_input("Text: ")
            if title and body:
                notes.append({"title": title, "body": body, "created": datetime.now().isoformat(timespec="seconds")})
                save_data(); print(color("Note saved.", L))
        elif c in ("2", "4", "5"):
            if not notes: print(color("No notes saved yet.", G)); pause(); continue
            for i, n in enumerate(notes, 1): print(color(f"  {i}. ", P) + color(n["title"], W))
            try: idx = int(safe_input("Note number: ")) - 1
            except ValueError: idx = -1
            if not 0 <= idx < len(notes): print(color("Invalid note number.", R))
            elif c == "2":
                n = notes[idx]; line(); print(color(n["title"], L)); print(n["body"])
                if safe_input("Copy note? (y/N): ").lower() == "y": copy_text(n["body"])
            elif c == "4":
                notes[idx]["title"] = safe_input("New title (blank keeps current): ") or notes[idx]["title"]
                notes[idx]["body"] = safe_input("New text: ") or notes[idx]["body"]
                save_data(); print(color("Updated.", L))
            else:
                if safe_input("Delete this note? (yes/no): ").lower() == "yes":
                    notes.pop(idx); save_data(); print(color("Deleted.", L))
        elif c == "3":
            term = safe_input("Search text: ").lower()
            matches = [n for n in notes if term in n["title"].lower() or term in n["body"].lower()]
            for n in matches: print(color("  " + n["title"], L) + color(" — " + n["body"][:100], W))
            if not matches: print(color("No matches.", G))
        elif c == "0": return
        else: print(color("Unknown option.", R))
        pause()

def links_menu():
    while True:
        print(color("\n[ LINKS ]", L)); line()
        print("  1. Save link\n  2. List links\n  3. Open link\n  4. Copy link\n  5. Delete link\n  0. Back")
        c = safe_input("xor@xor/links > ")
        links = DATA["links"]
        if c == "1":
            label = safe_input("Label: ")
            url = safe_input("URL: ")
            if url and not url.startswith(("https://", "http://")): url = "https://" + url
            if label and urlparse(url).hostname:
                links.append({"label": label, "url": url}); save_data()
                print(color("Link saved.", L))
            else: print(color("Invalid URL.", R))
        elif c in ("2", "3", "4", "5"):
            if not links: print(color("No links saved yet.", G)); pause(); continue
            for i, item in enumerate(links, 1):
                print(color(f"  {i}. ", P) + color(item["label"], W) + color("  " + item["url"], G))
            if c != "2":
                try: idx = int(safe_input("Link number: ")) - 1
                except ValueError: idx = -1
                if not 0 <= idx < len(links): print(color("Invalid link number.", R))
                elif c == "3":
                    url = links[idx]["url"]
                    try:
                        if "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ:
                            subprocess.Popen(["termux-open-url", url])
                        else:
                            import webbrowser; webbrowser.open(url)
                        print(color("Opening link...", L))
                    except Exception: print(color("Could not open link: " + url, G))
                elif c == "4": copy_text(links[idx]["url"])
                elif c == "5":
                    if safe_input("Delete link? (yes/no): ").lower() == "yes":
                        links.pop(idx); save_data(); print(color("Deleted.", L))
        elif c == "0": return
        else: print(color("Unknown option.", R))
        pause()

def system_menu():
    clear(); banner()
    print(color("[ SYSTEM INFORMATION ]", L)); line()
    values = [
        ("Platform", platform.platform()),
        ("Python", sys.version.split()[0]),
        ("Architecture", platform.machine()),
        ("Hostname", socket.gethostname()),
        ("Local IP", get_local_ip()),
        ("Storage path", BASE),
        ("Saved notes", str(len(DATA["notes"]))),
        ("Saved links", str(len(DATA["links"]))),
    ]
    for k, v in values: print(color("  " + k.ljust(16), V) + color(str(v), W))
    try:
        st = os.statvfs(os.path.expanduser("~"))
        free = st.f_bavail * st.f_frsize / (1024**3)
        print(color("  Free storage     ", V) + color(f"{free:.2f} GB", W))
    except Exception: pass

def settings_menu():
    print(color("\n[ SETTINGS ]", L)); line()
    print("  Theme: PURPLE / BLACK (XOR default)")
    print("  Animation: enabled during startup")
    print("  Data: " + DATA_FILE)
    print(color("  All notes, links, history and settings persist between launches.", G))
    if safe_input("Clear command history? (y/N): ").lower() == "y":
        DATA["history"] = []; save_data(); print(color("History cleared.", L))

def main():
    boot()
    while True:
        cmd = safe_input("xor@xor:~$ ").lower()
        if not cmd: continue
        record_history(cmd)
        if cmd in ("!help", "help"): help_menu(); pause()
        elif cmd in ("!scan", "scan"): scan_menu()
        elif cmd in ("!osint", "osint"): osint_menu()
        elif cmd in ("!gen", "gen"): generate_menu()
        elif cmd in ("!notes", "notes"): notes_menu()
        elif cmd in ("!links", "links"): links_menu()
        elif cmd in ("!system", "system"): system_menu(); pause()
        elif cmd in ("!settings", "settings"): settings_menu(); pause()
        elif cmd in ("!history", "history"):
            for item in DATA["history"][-20:]:
                print(color("  " + item["time"] + "  ", G) + color(item["command"], W))
            pause()
        elif cmd in ("!clear", "clear"): clear(); banner()
        elif cmd in ("!exit", "exit", "quit"):
            save_data(); typewrite("Closing XOR session. Stay sharp.", 0.015, L); break
        else: print(color("Unknown command. Type !help.", R))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        save_data()
        print(color("\nXOR session interrupted. Data saved.", G))
