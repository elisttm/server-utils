#!/bin/bash

source /home/eli/.bashrc # just in case...

DATETIME () { date '+%F %X'; }
SUPD () { sed 's/validate//g' $1 | bash; }
SRUN () {
    if grep -wq 's/qDRS/dmS/g' $1; then
        $1
    else
        sed 's/qDRS/dmS/g' $1 | bash;
    fi
}

echo "[$(DATETIME)] starting autorun tasks..."

SRUN "/home/eli/_web/elisttm/start.sh"
SRUN "/home/eli/_web/elisttm/servers.sh"
SRUN "/home/eli/_web/redirects/start.sh"
SRUN "/home/eli/_web/fileserver/start.sh"
SRUN "/home/eli/_web/copyparty/start.sh"
SRUN "/home/eli/_web/fastdl/start.sh"

SRUN "/home/eli/syncthing.sh"
SRUN "/home/eli/_other/elibot/start.sh"
SRUN "/home/eli/_other/shermbot/start.sh"

pm2 start /home/eli/_other/tf2autobot/ecosystem.json

SRUN "/home/eli/_games/hldm/start.sh"
SUPD "/home/eli/_games/sven/update.sh" && SRUN "/home/eli/_games/sven/start.sh"
SUPD "/home/eli/_games/tf2/update.sh" && SRUN "/home/eli/_games/tf2/start.sh"
SUPD "/home/eli/_games/gmod/update.sh" && SRUN "/home/eli/_games/gmod/start.sh"

SRUN "/home/eli/_games/mc-creative/start.sh"
SRUN "/home/eli/_games/mc-jc/start.sh"
SRUN "/home/eli/_games/mc-snow/start.sh"

echo "[$(DATETIME)] autorun tasks completed!"