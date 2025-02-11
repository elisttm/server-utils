import os, argparse, subprocess, psutil, time, a2s, mcstatus

parser = argparse.ArgumentParser(prog="restarter", description="")

parser.add_argument("-e", "--exclusive", nargs="*", help="will restart ONLY the provided server(s)")
parser.add_argument("--shutdown", action="store_true", help="will only stop servers and not restart them")
args = parser.parse_args()

query_ip = "play.elisttm.space"
servers = {
    "tf2": {
        "id": "tf2",
        "type": "source",
        "msg": 'sm_say {}; sm_play @all "ui/system_message_alert.wav"',
        "port": 27016,
    },
    "gmod": {
        "id": ["gmod", "sandbox"],
        "type": "source",
        "port": [27015, 27017],
        "msg": 'ulx tsay {}; ulx playsound common/warning.wav',
    },
    "hldm": {
        "id": "hldm",
        "type": "goldsrc",
        "port": 27013,
        "msg": 'amx_say {}',
        "flags": ("noupdate")
    },
    "mc-creative": {
        "id": "mc-creative",
        "type": "minecraft",
        "msg": 'warning {}',
        "port": 25570,
        "flags": ("noupdate")
    },
    "doom": {
        "id": "doom",
        "type": "doom",
        "port": 6950,
        "msg": 'say {}',
        "flags": ("noupdate")
    },

}

def screen_cmd(sid, cmd):
    sid = [sid] if not isinstance(sid, list) else sid
    for s in sid:
        subprocess.run(f'screen -S {s} -X stuff "{cmd}\r"', shell=True)

def screen_msg(game, sid, msg):
    screen_cmd(sid, servers[game]["msg"].format(msg))

def query_server(game, port):
    try:
        if servers[game]["type"] in ("source","goldsrc"):
            return a2s.info((query_ip, port)).player_count
        elif servers[game]["type"] == "minecraft":
            return mcstatus.JavaServer.lookup(f"{query_ip}:{port}").status().players.online
        return 0
    except Exception as e:
        print("EXCEPTION in query_server():",e)
        return None

def kill_tree(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except Exception:
        print("EXCEPTION in kill_tree()... ignoring!")

def stop_server(game, sid, pid):
    if servers[game]["type"] in ("source","goldsrc"):
        screen_cmd(sid, "quit")
    elif servers[game]["type"] == "minecraft":
        screen_cmd(sid, "stop")
    time.sleep(2)
    if psutil.pid_exists(pid):
        time.sleep(2)
        if psutil.pid_exists(pid):
            kill_tree(pid)

def msg_countdown(game, ids, sec):
    if sec >= 60:
        print("    @ 1 minute...")
        screen_msg(game, ids, "the server will restart in 1 minute!")
        time.sleep(30)
    if sec >= 30:
        print("    @ 30 seconds...")
        screen_msg(game, ids, "the server will restart in 30 seconds!")
        time.sleep(20)
    if sec >= 10:
        screen_msg(game, ids, "the server will restart in 10 seconds!")
        time.sleep(5)
    if sec >= 5:
        print("    @ 5 seconds...")
        screen_msg(game, ids, "the server will restart in 5 seconds!")
        time.sleep(1)
        screen_msg(game, ids, "the server will restart in 4 seconds!")
        time.sleep(1)
        screen_msg(game, ids, "the server will restart in 3 seconds!")
        time.sleep(1)
        screen_msg(game, ids, "the server will restart in 2 seconds!")
        time.sleep(1)
        screen_msg(game, ids, "the server will restart in 1 second!")
        time.sleep(1)

print("\n--------------------------------------------------\n")

_ing = "shutting down" if args.shutdown else "restarting"
print(f"[{time.strftime('%X %x %Z')}] {_ing} servers!\n")

# for exclusively picking which server(s) to restart
if args.exclusive:
    if not set(args.exclusive).issubset(servers.keys()):
        print("invalid server name(s) provided!")
        exit(1)
    for server in servers.copy().keys():
        if server not in args.exclusive:
            del servers[server]
    print(f"exclusively {_ing} {len(args.exclusive)} server(s): {', '.join(args.exclusive)}")

for game in servers:
    print(f"\n{_ing} {game} server(s)...")
    
    ids = [servers[game]["id"]] if not isinstance(servers[game]["id"], list) else servers[game]["id"]
    ports = [servers[game]["port"]] if not isinstance(servers[game]["port"], list) else servers[game]["port"]
    screens = os.listdir("/var/run/screen/S-eli")

    game_type = servers[game].get("type")
    flags = servers[game].get("flags", [])
    gdir = f"/home/eli/_games/{game}/"

    pids = {}
    queries = {}
    for sid in ids.copy():
        indx = ids.index(sid)
        port = ports[indx]
        skip = False

        # different games have different port mapping systems so this is necessary
        if game_type in ("source", "minecraft"):
            lsof_args = ['lsof', '-nPFp', f'-iTCP:{port}', '-sTCP:LISTEN']
        elif game_type == "goldsrc":
            lsof_args = ['lsof', '-nPFp', f'-iUDP:{port}']
        else:
            lsof_args = ['lsof', '-nPFp', f'-i:{port}']

        pid = subprocess.run(lsof_args, capture_output=True, text=True).stdout

        if not pid:
            print(f"  '{sid}' offline! skipping...")
            del ids[indx]
            del ports[indx]
        else:
            print(f"  querying '{sid}'...")
            pid = int(pid.strip().replace("p",""))
            pids[sid] = pid
            
            queries[ids[indx]] = query_server(game, port)
        
        # if multiple screens exist with the same name just kill all of them indiscriminately
        screen_count = sum(1 for y in screens if y.endswith(sid))
        if not screen_count:
            print(f"  no screen found for '{sid}'!")
        elif screen_count > 1:
            print(f"  found multiple screens named '{sid}'! killing all of them... ({screen_count})")
            scr_pids = sorted([int(x.split(".")[0]) for x in screens if x.endswith(game)])
            for spid in scr_pids:
                kill_tree(spid)
            pids.clear()
            subprocess.run(['screen', '-wipe']) # removes dead screens and prevents any issues those may cause

    if pids:
        # get highest playercount in group of servers (if any)
        player_count = 0
        for _, query_count in queries.items():
            if query_count and query_count > player_count:
                player_count = query_count
            else:
                continue

        if player_count <= 0:
            print("    no players online! skipping countdown.")
        elif player_count >= 1:
            timer = 60
            if args.shutdown:
                screen_msg(game, ids, "the server is preparing to reboot and will offline for an indeterminate amount of time! please check back later...")
            else:
                screen_msg(game, ids, "the server is scheduled to restart soon! check https://elisttm.space/servers for statuses")
            print(f"    {player_count} player(s) online! starting {timer} second countdown...")
            time.sleep(2)
            msg_countdown(game, ids, timer)

        for sid, pid in pids.items():
            print(f"  closing {sid} ({pid})...")
            stop_server(game, sid, pid)

    if not args.shutdown:
        if "noupdate" not in flags and os.path.exists(f"{gdir}update.sh"):
            print(f"  updating {game} server(s)")
            subprocess.run(f"sed 's/validate//g' {gdir}update.sh | bash", shell=True, stdout=subprocess.DEVNULL)

        print(f"  starting {game} server(s)")
        with open(f'{gdir}start.sh', 'r') as startfile:
            start_cmd = f"{gdir}start.sh" if 's/qDRS/dmS/g' in startfile.read() else f"sed 's/qDRS/dmS/g' {gdir}start.sh | bash"
        subprocess.Popen(start_cmd, shell=True, start_new_session=True, stdout=subprocess.DEVNULL)
    
print(f"\n[{time.strftime('%x %X %Z')}] done!")
print("\n--------------------------------------------------")