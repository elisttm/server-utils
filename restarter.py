import os, argparse, requests, subprocess, psutil, time, a2s, mcstatus, json, traceback

parser = argparse.ArgumentParser(prog="restarter", description="")

parser.add_argument("-e", "--exclusive", nargs="*", default=[], help="will restart ONLY the provided server(s)")
parser.add_argument("-u", "--update", nargs="*", default=[], help="same as '--exclusive' with different messages")
parser.add_argument("--shutdown", action="store_true", help="will only stop servers and not restart them")
parser.add_argument("--watchdog", action="store_true", help="used when directly invoked by watchdog.py")
parser.add_argument("--debug", action="store_true", help="for debugging, no commands will be sent")
args = parser.parse_args()

query_ip = "play.elisttm.space"
servers = {
    "tf2": {
        "ids": {
            "tf2a": 27016,
            "tf2b": 27019,
            #"tf2z": 27043,
        },
        "type": "source",
        "msg": 'sm_say {}; sm_play @all "ui/system_message_alert.wav"',
    },
    "gmod": {
        "ids": {
            "gmoda": 27015,
            "gmodb": 27018,
            "sandbox": 27017
        },
        "type": "source",
        "msg": 'ulx tsay <!> {}; ulx playsound common/warning.wav',
    },
    "sven": {
        "ids": {"sven": 27040},
        "type": "goldsrc",
        "msg": 'amx_say <!> {}',
    },
    "hldm": {
        "ids": {"hldm": 27013},
        "type": "goldsrc",
        "msg": 'amx_say <!> {}',
        "flags": ("noupdate")
    },
    "mc-creative": {
        "ids": {"mc-creative": 25570},
        "type": "minecraft",
        "msg": 'warning {}',
    },
    "mc-snow": {
        "ids": {"mc-snow": 25569},
        "type": "minecraft",
        "msg": 'warning {}',
    },
    "quake": {
        "ids": {"quake": 27049},
        "type": "quake",
        "msg": 'say <!> {}',
        "flags": ("noupdate")
    },
}

user = "eli"
gamedir = f"/home/{user}/_games/"

qstat_bin = "/usr/bin/quakestat"
qstat_games = {
    "quake": "qws",
    "halo": "gs2",
}

error_logs = []

# timer to use if playercount is above 4
server_timers = {
    "tf2b": 240,
    "gmoda": 120,
    "gmodb": 180,
}

def screen_cmd(sid, cmd):
    if args.debug:
        return
    sid = [sid] if not isinstance(sid, list) else sid
    for s in sid:
        subprocess.run(f'screen -S {s} -X stuff "{cmd}\r"', shell=True)

def screen_msg(game, sid, msg):
    screen_cmd(sid, servers[game].get("msg", "").format(msg))

def qstat_query(server_address, game):
    try:
        result = subprocess.run(f"{qstat_bin} -json -ts -P -{qstat_games[game]} {server_address}", capture_output=True, text=True, check=True, shell=True)
        return json.loads(result.stdout)[0]
    except Exception as e:
        return f"QSTAT ERROR: {e}"

def query_server(game, port):
    try:
        if servers[game]["type"] in ("source","goldsrc"):
            return a2s.info((query_ip, port)).player_count
        elif servers[game]["type"] == "minecraft":
            return mcstatus.JavaServer.lookup(f"{query_ip}:{port}").status().players.online
        if servers[game]["type"] in ("quake","halo"):
            return dict(qstat_query(f"{query_ip}:{port}", game)).get("numplayers", 0)
        return 0
    except Exception as e:
        print(f"EXCEPTION in query_server({game}): {e}")
        print(traceback.format_exc())
        return None

def is_empty(game, ids):
    total = 0
    for qid in ids:
        total += query_server(game, servers[game]["ids"][qid])
    return total <= 0

def get_pid(game_type, port):
    # different games have different port mapping systems so this is necessary
    if game_type in ("source", "minecraft"):
        lsof_args = ['lsof', '-nPFp', f'-iTCP:{port}', '-sTCP:LISTEN']
    elif game_type == "goldsrc":
        lsof_args = ['lsof', '-nPFp', f'-iUDP:{port}']
    else:
        lsof_args = ['lsof', '-nPFp', f'-i:{port}']

    return subprocess.run(lsof_args, capture_output=True, text=True).stdout

def kill_tree(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except Exception:
        print(f"EXCEPTION in kill_tree({pid})... ignoring!")

def stop_server(game, sid, pid):
    if args.debug:
        return
    if servers[game]["type"] in ("source","goldsrc","doom","quake"):
        screen_cmd(sid, "quit")
    elif servers[game]["type"] == "minecraft":
        screen_cmd(sid, "stop")
    i = 10
    while i > 0 and psutil.pid_exists(pid):
        time.sleep(0.5)
        i -= 1
    if psutil.pid_exists(pid):
        kill_tree(pid)
    time.sleep(0.1)
    subprocess.run(['screen', '-wipe'], stdout=subprocess.DEVNULL) # extremely important, dead screens will cause lots of issues

def stop_server_warn(game, sid, pid):
    screen_msg(game, sid, "this server is restarting due to a technical issue! if you see this message, PLEASE get in contact!!! (@elisttm / https://elisttm.space/)")
    time.sleep(1)
    stop_server(game, sid, pid)

def log(message):
    error_logs.append(message)
    print(message)

def ntfy_post(message, title=None, priority=None, tags=None):
    requests.post(f"https://ntfy.sh/{os.getenv('NTFY','')}",
    data=message,
    headers={
        "Title": title,
        "Priority": priority,
        "Tags": tags,
    })

def msg_countdown(game, ids, sec):
    if sec >= 300:
        print("    @ 5 minutes...")
        screen_msg(game, ids, "the server will restart in 5 minutes!")
        time.sleep(60)
        if is_empty(game, ids):
            sec = 0
    if sec >= 240:
        print("    @ 4 minutes...")
        screen_msg(game, ids, "the server will restart in 4 minutes!")
        time.sleep(60)
        if is_empty(game, ids):
            sec = 0
    if sec >= 180:
        print("    @ 3 minutes...")
        screen_msg(game, ids, "the server will restart in 3 minutes!")
        time.sleep(60)
        if is_empty(game, ids):
            sec = 0
    if sec >= 120:
        print("    @ 2 minutes...")
        screen_msg(game, ids, "the server will restart in 2 minutes!")
        time.sleep(60)
        if is_empty(game, ids):
            sec = 0
    if sec >= 60:
        print("    @ 1 minute...")
        screen_msg(game, ids, "the server will restart in 1 minute!")
        time.sleep(30)
        if is_empty(game, ids):
            sec = 0
    if sec >= 30:
        print("    @ 30 seconds...")
        screen_msg(game, ids, "the server will restart in 30 seconds!")
        time.sleep(20)
        if is_empty(game, ids):
            sec = 0
    if sec >= 10:
        screen_msg(game, ids, "the server will restart in 10 seconds!")
        time.sleep(5)
        if is_empty(game, ids):
            sec = 0
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
    if sec == 0:
        print("    @ server(s) emptied! skipping...")
        screen_msg(game, ids, "server emptied! skipping countdown...")


if __name__ == "__main__": # beginning of the actual script

    _ing = "shutting down" if args.shutdown else "restarting"

    start_time = time.time()
    print(f"----- [{time.strftime('%X %x')}] {_ing} servers! -----")

    # for exclusive arg, selects only the desired servers
    sub_servers = [gid for game in servers.keys() for gid in servers[game].get("ids",[]) if gid != game]
    if args.update:
        if not args.exclusive:
            args.exclusive = args.update
        else:
            args.exclusive.extend(args.update)

    if args.exclusive:
        if not set(args.exclusive).issubset(set(sub_servers+list(servers.keys()))):
            print("invalid server keys provided!")
            exit(1)
        ex_servers = {}
        for ex in args.exclusive:
            if ex in servers.keys():
                ex_servers[ex] = servers[ex]
            elif ex in sub_servers:
                for game in servers:
                    if ex in servers[game]["ids"]:
                        if game not in ex_servers:
                            ex_servers[game] = servers[game].copy()
                            ex_servers[game]["ids"] = {}
                            ex_servers[game]["flags"] = ["noupdate"]
                        ex_servers[game]["ids"][ex] = servers[game]["ids"][ex]
                        break
        servers = ex_servers

    try:
        for i, game in enumerate(servers):
            try:
                print(f"\n[{i+1}] {_ing if game not in args.update else 'updating'} {game} server(s)...")
                
                ids = list(servers[game]["ids"])
                flags = servers[game].get("flags", [])
                gdir = f"{gamedir}{game}/"

                pids = {}
                queries = {}
                real_sids = {}

                for sid in ids.copy():
                    port = servers[game]["ids"][sid]

                    screens = sorted([int(x.split(".")[0]) for x in os.listdir(f"/var/run/screen/S-{user}") if x.endswith(sid)])
                    screen_count = sum(1 for y in screens)

                    pid = get_pid(servers[game]["type"], port)

                    if not pid:
                        if screen_count == 1:
                            log(f"    <> '{sid}' is unreachable, but a screen exists! killing and skipping to be safe...")
                            stop_server_warn(game, f"{screens[0]}.{sid}", screens[0])
                            ids.remove(sid)
                        if screen_count > 1:
                            log(f"    <> '{sid}' is unreachable, but multiple screens exist! this should never happen, skipping query to be safe...")
                        else:
                            log(f"    <> '{sid}' is offline! skipping...")
                            ids.remove(sid)
                    else:
                        pids[sid] = int(pid.strip().replace("p",""))
                        
                        if "noquery" not in flags:
                            print(f"    -- querying '{sid}'...")
                            queries[sid] = query_server(game, port)
                        
                        if args.debug:
                            print(queries)
                    
                    if sid in ids:
                        if not screen_count:
                            log(f"       <> no screen found for '{sid}'!")
                        elif screen_count > 1:
                            log(f"       <> found {screen_count} screens named '{sid}'! killing all of them...")
                            for spid in screens:
                                stop_server_warn(game, f"{spid}.{sid}", spid)
                            del pids[sid]
                            
                        else:
                            real_sids[sid] = f"{screens[0]}.{sid}" # stupid

                if pids and not args.debug:

                    if "noquery" not in flags:
                        player_count = 0
                        timer = 60

                        # get highest playercount in group of servers (if any)
                        for server_id, query_count in queries.items():
                            if not query_count:
                                continue
                            query_count = int(query_count) # fixes a ridiculous bug that i cannot replicate
                            if query_count > 0:
                                player_count += query_count

                                if query_count > 4 and server_id in server_timers:
                                    server_timer = server_timers[server_id]
                                    timer = server_timer if server_timer > timer else timer

                        if player_count <= 0:
                            print("       - no players online! skipping countdown...")
                        else:
                            if args.shutdown:
                                screen_msg(game, ids, "the server is preparing to reboot and will offline for an indeterminate amount of time! please check https://elisttm.space/servers for updates.")
                            elif game in args.update:
                                screen_msg(game, ids, "a new game update is available! the server will restart soon, check elisttm.space/servers for updates.")
                            elif args.watchdog:
                                screen_msg(game, ids, "the server will automatically restart soon due to a technical issue! check elisttm.space/servers for updates, apologies for the inconvenience!")
                            else:
                                screen_msg(game, ids, "the server is scheduled to restart soon! check elisttm.space/servers or join discord.gg/chVeByf6uP for updates.")
                            print(f"       -- {player_count} player(s) online! starting {timer} second countdown...")
                            time.sleep(2)
                            #msg_countdown(game, ids, timer)
                    else:
                        screen_msg(game, ids, "this server is scheduled to restart in a few seconds! please check discord.gg/chVeByf6uP for updates.")
                        time.sleep(5)

                    for sid, pid in pids.items():
                        print(f"    << closing {real_sids[sid]}...")
                        stop_server(game, real_sids[sid], pid)

                if not any((args.shutdown, args.debug)):

                    if "noupdate" not in flags and os.path.exists(f"{gdir}update.sh"):
                        print(f"    == updating {game} server(s)...")
                        subprocess.run(f"sed 's/validate//g' {gdir}update.sh | bash", shell=True, stdout=subprocess.DEVNULL)

                    if args.exclusive and os.path.exists(f"{gdir}_{list(servers[game]["ids"])[0]}.sh"):
                        print(f"    >> starting sub-server(s) ({", ".join(servers[game]["ids"].keys())})")
                        for sid in servers[game]["ids"].keys():
                            subprocess.Popen(f"sed 's/qDRS/dmS/g' {gdir}_{sid}.sh | bash", shell=True, start_new_session=True, stdout=subprocess.DEVNULL)
                            time.sleep(1)
                    else:
                        print(f"    >> starting {game} server(s)...")
                        with open(f'{gdir}start.sh', 'r') as startfile:
                            start_cmd = f"{gdir}start.sh" if 's/qDRS/dmS/g' in startfile.read() else f"sed 's/qDRS/dmS/g' {gdir}start.sh | bash"
                        subprocess.Popen(start_cmd, shell=True, start_new_session=True, stdout=subprocess.DEVNULL)

            except Exception:
                screen_msg(game, ids, "server restart aborted due to an error! PLEASE get in contact if you see this message! @elisttm / discord.gg/chVeByf6uP")
                log("<!> STOPPING DUE TO AN EXCEPTION! PLEASE CHECK LOGS... <!>")
                print(traceback.format_exc())

                ntfy_post("restart script was aborted due to an error! please check logs...", "fatal error in restarter.py!", "high", "stop_sign")

    except KeyboardInterrupt:
        print("FORCEFULLY STOPPING")
        try:
            screen_msg(game, ids, "server restart manually aborted! continue as you were...")
        except Exception:
            pass

    end_time = time.time()
    elapsed = round(end_time - start_time, 2)

    print(f"\n----- [{time.strftime('%x %X')}] done in {elapsed}s! -----")

    if not args.debug:
        if not error_logs:
            ntfy_post(f"successfully completed in {elapsed}s! no issues logged.", "restart script completed!", "min", "white_check_mark")
        else:
            ntfy_post(f"{len(error_logs)} possible issue(s) found!\n{'\n'.join(error_logs)}", f"restart script completed with {len(error_logs)} issues!", "default", "warning")