#!/bin/sh
# Commit as the author listed in config/author. Does not change git config.
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$root"
name=$(sed -n '1p' config/author | tr -d '\r')
email=$(sed -n '2p' config/author | tr -d '\r')
msg=$(mktemp)
trap 'rm -f "$msg"' EXIT
if [ "$#" -ge 1 ]; then
  printf '%s\n' "$1" > "$msg"
else
  cat > "$msg"
fi
GIT_AUTHOR_NAME="$name" \
GIT_AUTHOR_EMAIL="$email" \
GIT_COMMITTER_NAME="$name" \
GIT_COMMITTER_EMAIL="$email" \
git -c core.hooksPath="$root/.githooks" commit -F "$msg"
got=$(git log -1 --format='%an <%ae>')
if [ "$got" != "$name <$email>" ]; then
  echo "commit landed as $got" >&2
  exit 1
fi
