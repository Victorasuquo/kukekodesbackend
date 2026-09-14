#!/usr/bin/env sh
set -eu
base_url="${API_BASE_URL:?Set API_BASE_URL}"
count="${REQUEST_COUNT:-20}"
i=0
while [ "$i" -lt "$count" ]; do
  curl --silent --show-error --fail --max-time 5 "$base_url/livez" >/dev/null
  i=$((i + 1))
done
echo "completed $count liveness requests"
