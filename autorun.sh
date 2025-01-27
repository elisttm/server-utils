#!/bin/bash
source /home/eli/.bashrc

DATETIME () { date '+%F %X'; }
SRUN () { sed 's/qDRS/dmS/g' $1 | bash; }

echo "[$(DATETIME)] starting autorun tasks..."

SRUN /home/eli/_web/elisttm/start.sh
SRUN /home/eli/_web/cupid/start.sh
SRUN /home/eli/_web/fileserver/start.sh
SRUN /home/eli/_web/stav/start.sh
#SRUN /home/eli/_web/botdash/start.sh
SRUN /home/eli/_web/fastdl/start.sh

SRUN /home/eli/_other/elibot/start.sh
#SRUN /home/eli/_other/elibotold/start.sh
SRUN /home/eli/_other/shermbot/start.sh
SRUN /home/eli/_other/tf2autobot/start.sh

steamcmd +force_install_dir /home/eli/_games/tf2/ +login anonymous +app_update 232250 +quit
steamcmd +force_install_dir /home/eli/_games/gmod/ +login anonymous +app_update 4020 +quit

SRUN /home/eli/_games/hldm/start.sh && sleep 5
SRUN /home/eli/_games/tf2/start.sh && sleep 10
/home/eli/_games/gmod/start.sh

echo "[$(DATETIME)] autorun tasks completed!"
