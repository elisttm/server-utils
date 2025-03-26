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
SRUN "/home/eli/_web/cupid/start.sh"
SRUN "/home/eli/_web/fileserver/start.sh"
SRUN "/home/eli/_web/stav/start.sh"
SRUN "/home/eli/_web/fastdl/start.sh"

SRUN "/home/eli/_other/elibot/start.sh"
SRUN "/home/eli/_other/shermbot/start.sh"
pm2 start /home/eli/_other/tf2autobot/ecosystem.json

SRUN "/home/eli/_games/doom/start.sh"
SRUN "/home/eli/_games/quake/start.sh"
SRUN "/home/eli/_games/hldm/start.sh"
SUPD "/home/eli/_games/sven/update.sh" && SRUN "/home/eli/_games/sven/start.sh"
SUPD "/home/eli/_games/hl2mp/update.sh" && SRUN "/home/eli/_games/hl2mp/start.sh"
SUPD "/home/eli/_games/tf2/update.sh" && SRUN "/home/eli/_games/tf2/start.sh"
SUPD "/home/eli/_games/gmod/update.sh" && SRUN "/home/eli/_games/gmod/start.sh"
SUPD "/home/eli/_games/mc-creative/update.sh" && SRUN "/home/eli/_games/mc-creative/start.sh"

echo "[$(DATETIME)] autorun tasks completed!"

# not in use
#SRUN /home/eli/_web/botdash/start.sh
#SRUN /home/eli/_other/elibotold/start.sh