import os, sys, subprocess, psutil, time, a2s, mcstatus

shutdown = True if (len(sys.argv) > 1 and sys.argv[1] == "shutdown") else False
gdir = "/home/eli/_games/"
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
        "msg": 'amx_say {}',
        "port": 27013,
    },
    #"mc": {
    #    "id": "mc",
    #    "type": "minecraft",
    #    "msg": 'warning {}',
    #    "port": 25565,
    #},
}

class server_info(object):
    player_count = 0
    def __init__(self, player_count):
        self.player_count = player_count

def screen_cmd(sid, cmd):
    sid = [sid] if not isinstance(sid, list) else sid
    for s in sid:
        subprocess.run(f'screen -S {s} -X stuff "{cmd}\r"', shell=True)

def screen_msg(game, sid, msg):
    screen_cmd(sid, servers[game]["msg"].format(msg))

def query_server(game, port):
    try:
        if servers[game]["type"] in ("source","goldsrc"):
            query = a2s.info((query_ip, port))
            return server_info(query.player_count)
        elif servers[game]["type"] == "minecraft":
            query = mcstatus.JavaServer.lookup(f"{query_ip}:{port}").status()
            return server_info(query.players.online)
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
    print("starting countdown...")
    if sec >= 60:
        print("  <@> 1 minute...")
        screen_msg(game, ids, "the server will restart in 1 minute!")
        time.sleep(30)
    if sec >= 30:
        print("  <@> 30 seconds...")
        screen_msg(game, ids, "the server will restart in 30 seconds!")
        time.sleep(20)
    if sec >= 10:
        screen_msg(game, ids, "the server will restart in 10 seconds!")
        time.sleep(5)
    if sec >= 5:
        print("  <@> 5 seconds...")
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

print(f"restarting servers! {time.strftime('%X %x %Z')}")

for game in servers:
    print(f"\nrestarting {game} server(s)...")
    
    ids = [servers[game]["id"]] if not isinstance(servers[game]["id"], list) else servers[game]["id"]
    ports = [servers[game]["port"]] if not isinstance(servers[game]["port"], list) else servers[game]["port"]
    game_type = servers[game]["type"]
    screens = os.listdir("/var/run/screen/S-eli")

    pids = {}
    queries = {}
    for sid in ids.copy():
        indx = ids.index(sid)
        port = ports[indx]

        # different games have different port mapping systems so this is necessary
        if game_type in ("source", "minecraft"):
            lsof_args = ['lsof', '-nPFp', f'-iTCP:{port}', '-sTCP:LISTEN']
        elif game_type == "goldsrc":
            lsof_args = ['lsof', '-nPFp', f'-iUDP:{port}']
        else:
            lsof_args = ['lsof', '-nPFp', f'-i:{port}']

        pid = subprocess.run(lsof_args, capture_output=True, text=True).stdout

        if not pid:
            print(f"  <!> {sid} offline... skipping!")
            del ids[indx]
            del ports[indx]
        else:
            print(f"  <?> querying {sid}...")
            pid = int(pid.strip().replace("p",""))
            pids[sid] = pid
            
            queries[ids[indx]] = query_server(game, port)
        
        # if multiple screens exist with the same name just kill all of them indiscriminately
        screen_count = sum(1 for y in screens if y.endswith(sid))
        if not screen_count:
            print(f"  <!> no screen exists for id {sid}!")
        elif screen_count > 1:
            print(f"  <!> multiple screens found under {sid} ({screen_count})! forcefully killing all of them...")
            scr_pids = sorted([int(x.split(".")[0]) for x in screens if x.endswith(game)])
            for spid in scr_pids:
                kill_tree(spid)
            pids.clear()
            subprocess.run(['screen', '-wipe']) # removes dead screens and prevents any issues those may cause

    if pids:
        if shutdown:
            screen_msg(game, ids, "the server is preparing to reboot and will offline for an indeterminate amount of time!")
        else:
            screen_msg(game, ids, "the server is scheduled to restart soon! check elisttm.space/servers for status...")
        time.sleep(2)

        # get highest playercount in group of servers (if any)
        player_count = 0
        for _, query in queries.items():
            if query and query.player_count > player_count:
                player_count = query.player_count
            else:
                continue

        if player_count <= 0:
            print("no players online... skipping countdown!")
        elif player_count >= 1:
            msg_countdown(game, ids, 60)

        for sid, pid in pids.items():
            print(f"closing server... ({sid} / {pid})")
            stop_server(game, sid, pid)

    if not shutdown:
        print(f"updating {game}...")
        subprocess.run(f"sed 's/validate//g' {gdir}{game}/update.sh | bash", shell=True, stdout=subprocess.DEVNULL)

        print(f"starting {game}!")
        with open(f'{gdir}{game}/start.sh', 'r') as startfile:
            if 's/qDRS/dmS/g' in startfile.read():
                subprocess.Popen(f"{gdir}{game}/start.sh", shell=True, start_new_session=True, stdout=subprocess.DEVNULL)
            else:
                subprocess.Popen(f"sed 's/qDRS/dmS/g' {gdir}{game}/start.sh | bash", shell=True, start_new_session=True, stdout=subprocess.DEVNULL)

print("\ndone!")
print("\n--------------------------------------------------\n")