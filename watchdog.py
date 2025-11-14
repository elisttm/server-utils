# this script extends from restarter.py, most functions used here are declared there

import os, subprocess, time, vdf
from restarter import (
    user,
    gamedir,
    servers,
    query_server,
    ntfy_post,
    log,
    error_logs,
    get_pid,
)

# set to false when debugging servers
run = True
if not run:
    exit()

outdated_servers = set()
offline_servers = set()
#error_logs = []

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
            app_info = subprocess.run(f"{steamcmd} +app_info_update 1 +app_info_print {appids[game]} +quit", capture_output=True, text=True, check=True, shell=True, timeout=30).stdout
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
    ntfy_post(f"found {len(offline_servers) + len(outdated_servers)} issues! restarter.py has been invoked, please check logs...\n\n{'\n'.join(error_logs)}", "watchdog found issues!", "high", "warning")
    print(f"[{time.strftime('%x %X')}] found {len(offline_servers) + len(outdated_servers)} issues! invoking restarter.py to fix...\n")

    subprocess.Popen(f"python {restart_script} --watchdog {('-e '+' '.join(offline_servers)+' ') if offline_servers else ''}{('-u '+' '.join(outdated_servers)+' ') if outdated_servers else ''}2>&1", shell=True, start_new_session=True)
else:
    print(f"[{time.strftime('%x %X')}] no issues found!\n")