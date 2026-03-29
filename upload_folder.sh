#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <folder_path> [oss_filename]"
  echo "  folder_path:  要上传的文件夹路径"
  echo "  oss_filename: OSS上的文件名 (默认: 文件夹名.tar.gz)"
  exit 1
fi

FOLDER_PATH="$(cd "$1" && pwd)"
FOLDER_NAME="$(basename "$FOLDER_PATH")"
OSS_FILENAME="${2:-${FOLDER_NAME}.tar.gz}"
ARCHIVE="/tmp/${OSS_FILENAME}"
OSS_BUCKET="oss://fcworks"
OSS_PATH="$OSS_BUCKET/$OSS_FILENAME"
OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"

echo "==> Packing $FOLDER_PATH to $ARCHIVE..."
tar czf "$ARCHIVE" -C "$FOLDER_PATH" .
SIZE=$(du -h "$ARCHIVE" | cut -f1)
echo "    $SIZE"

echo "==> Uploading to $OSS_PATH..."
ossutil cp "$ARCHIVE" "$OSS_PATH" -f -e "$OSS_ENDPOINT"
ossutil set-acl "$OSS_PATH" public-read -e "$OSS_ENDPOINT"
echo "==> Done."
