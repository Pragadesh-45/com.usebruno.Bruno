#!/bin/bash
set -e

# Extract the appimage
chmod +x bruno.appimage
unappimage bruno.appimage >/dev/null

# Check the payload: every entry in the image must have been extracted
expected=$(unappimage -l bruno.appimage | grep '^squashfs-root' | LC_ALL=C sort)
actual=$(find squashfs-root | LC_ALL=C sort)
if [ "$expected" != "$actual" ]; then
  echo "apply_extra: bruno.appimage was only partially extracted" >&2
  exit 1
fi

# Move all the data to /app/extra/bruno
mv squashfs-root bruno

# Clean up
rm bruno.appimage
