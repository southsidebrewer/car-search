#!/bin/bash

cd /opt/car-search || exit

eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

git add .
git commit -m "auto sync $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null

git push origin main
