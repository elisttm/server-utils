# this script extends from restarter.py, most functions used here are declared there

import os, subprocess, time, vdf
from restarter import (
    args,
    user,
    gamedir,
    servers,
    query_server,
    ntfy_post,
    log,
    error_logs,
    get_pid,
    restarter_main,
)

# set to false when debugging servers
run = True
if not run:
    exit()

outdated_servers = set()
offline_servers = set()

restart_script = f"/home/{user}/restarter.py"
log_file = "/home/eli/logs.txt"
steamcmd = "/usr/games/steamcmd"

appids = {
    "tf2": 232250,
    "gmod": 4020,
    "hl2mp": 232370,
    "sven": 276060,
}

def is_latest_version(game):
    if game in appids:
        try:
            app_info = subprocess.run(f"{steamcmd} +login anonymous +app_info_update 1 +app_info_print {appids[game]} +quit", capture_output=True, text=True, check=True, shell=True, timeout=30).stdout
            latest = vdf.loads(app_info[app_info.find("{"):app_info.rfind("}")].strip())["depots"]["branches"]["public"]["buildid"]
            current = vdf.load(open(f"{gamedir}{game}/steamapps/appmanifest_{appids[game]}.acf"))["AppState"]["buildid"]
            return latest == current
        except Exception as e:
            log(f"fatal error while getting {game} version: {e}")
    return True

print(f"[{time.strftime('%x %X')}] running watchdog ...")

for game in servers:
    ids = list(servers[game]["ids"])
    game_type = servers[game].get("type")

    # check if server is outdated
    if not is_latest_version(game):
        log(f"  <!> {game} is outdated! cueing update...")
        outdated_servers.add(game)

    for sid in ids.copy():
        port = servers[game]["ids"][sid]

        screens = sorted([int(x.split(".")[0]) for x in os.listdir(f"/var/run/screen/S-{user}") if x.endswith(sid)])
        screen_count = sum(1 for y in screens)

        pid = get_pid(game_type, port)

        if not pid:
            log(f"  <!> '{sid}' is unreachable/offline!")
            offline_servers.add(sid)
            continue

        else:
            query = query_server(game, port)
            if query is None:
                log(f"  <!> failed to query '{sid}'!")
                offline_servers.add(sid)
                continue

        if screen_count != 1:
            log(f"  <!> {screen_count} screen(s) found for '{sid}'!")
            offline_servers.add(sid)
            continue

if offline_servers or outdated_servers:
    watchdog_logs = error_logs
    error_logs = []

    args.watchdog = True
    args.exclusive = list(offline_servers)
    args.update = list(outdated_servers)

    print(f"[{time.strftime('%x %X')}] found {len(offline_servers) + len(outdated_servers)} issue(s)! invoking restarter to fix...\n")

    restarter_main()

    if error_logs:
        ntfy_post("restarter encountered an error via watchdog.py! please fix ASAP!!!!!", "fatal error in watchdog!", "max", "warning")
    else:
        if offline_servers:
            print(f"[{time.strftime('%x %X')}] revived server(s) sucessfully!\n")
            ntfy_post(f"found and attempted to revive {len(offline_servers)} offline servers! please check logs just to be sure...\n\n{'\n'.join(watchdog_logs)}", f"watchdog revived {len(offline_servers)} server(s)!", "default", "ballot_box_with_check")
        if outdated_servers:
            print(f"[{time.strftime('%x %X')}] updated server(s) sucessfully!\n")
            ntfy_post(f"updated {len(outdated_servers)} out of date server(s)!\n\n{'\n'.join(watchdog_logs)}", f"watchdog updated {len(outdated_servers)} server(s)!", "low", "arrow_up_small")

else:
    print(f"[{time.strftime('%x %X')}] no issues found!\n")