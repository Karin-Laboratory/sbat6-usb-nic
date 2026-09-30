# Karin Daily 本番配置手順

対象repo: https://github.com/everyoneknows/sbat6-usb-nic.git
対象commit: a82ce92b1e792873509b4e9317ead36edf8e40c1
配置先: karin-news (10.0.0.100), /opt/karin-daily

karin-news上で、以下を実行する。Karin Chat、Nginx、Cloudflare Tunnel、karin-ai (127.0.0.1:18080/v1) は変更しない。

## 配置

まず対象SHAを設定する。

    export TARGET_COMMIT=a82ce92b1e792873509b4e9317ead36edf8e40c1

次のブロックを実行する。

    set -Eeuo pipefail
    APP=/opt/karin-daily
    STAMP=$(date +%Y%m%d-%H%M%S)
    BACKUP="\${APP}.backup.\${STAMP}"
    WORK=$(mktemp -d /tmp/karin-daily-deploy.XXXXXX)
    trap 'rm -rf "$WORK"' EXIT

    sudo systemctl stop karin-daily-refresh.timer karin-daily.service || true
    sudo cp -a "$APP" "$BACKUP"

    git clone --no-checkout https://github.com/everyoneknows/sbat6-usb-nic.git "$WORK/repo"
    git -C "$WORK/repo" fetch --no-tags origin "$TARGET_COMMIT"
    git -C "$WORK/repo" cat-file -e "$TARGET_COMMIT^{commit}"
    git -C "$WORK/repo" checkout --detach "$TARGET_COMMIT"

    sudo mkdir -p "$WORK/new"
    git -C "$WORK/repo" archive "$TARGET_COMMIT" karin-daily | tar -x -C "$WORK/new"
    sudo rsync -a --delete --exclude 'data/' "$WORK/new/karin-daily/" "$APP/"
    sudo chown -R ubuntu:ubuntu "$APP"

    if [ -f "$APP/requirements.txt" ]; then
      sudo -u ubuntu python3 -m pip install --user -r "$APP/requirements.txt"
    fi

    sudo -u ubuntu env PYTHONPATH="$APP" python3 - <<'PY'
    from pipeline import load_config
    from storage import open_db
    cfg = load_config()
    db = open_db(cfg["database"])
    db.commit()
    db.close()
    print("migration OK:", cfg["database"])
    PY

    sudo -u ubuntu env PYTHONPATH="$APP" python3 "$APP/karin_daily.py" --once

    sudo -u ubuntu python3 - <<'PY'
    import sys
    sys.path.insert(0, "/opt/karin-daily")
    from pipeline import load_config
    from render import render
    html = render(load_config())
    assert "Karin Daily" in html and len(html) > 500
    print("HTML OK:", len(html), "bytes")
    PY

    sudo systemctl daemon-reload
    sudo systemctl restart karin-daily.service
    sudo systemctl start karin-daily-refresh.timer
    sudo systemctl --no-pager --full status karin-daily.service

    curl --fail --silent --show-error http://127.0.0.1:8088/healthz
    curl --fail --silent --show-error http://127.0.0.1:8088/ | grep -q 'Karin Daily'
    curl --fail --silent --show-error https://daily.karin-lab.com/ | grep -q 'Karin Daily'
    echo "deploy verified: $TARGET_COMMIT; backup: $BACKUP"

既存SQLiteは data/ を rsync対象外にして保持する。storage.open_db() はCREATE TABLE IF NOT EXISTSとALTER TABLEによる非破壊migrationである。構成は標準ライブラリのみで、requirements.txtが存在するときだけ依存を導入する。HTTPS cloneが認証を要求する場合は、担当者の認証済みGitHub経路を使用し、tokenや秘密値を出力しない。

## 問題時のrollback

実際のバックアップ名を指定して実行する。

    set -Eeuo pipefail
    APP=/opt/karin-daily
    BACKUP=/opt/karin-daily.backup.YYYYMMDD-HHMMSS

    sudo systemctl stop karin-daily-refresh.timer karin-daily.service || true
    sudo mv "$APP" "\${APP}.failed.$(date +%Y%m%d-%H%M%S)"
    sudo mv "$BACKUP" "$APP"
    sudo systemctl daemon-reload
    sudo systemctl restart karin-daily.service
    sudo systemctl start karin-daily-refresh.timer
    sudo systemctl --no-pager --full status karin-daily.service
    curl --fail --silent --show-error http://127.0.0.1:8088/healthz

新版実行後のSQLiteを保持したい場合は、rollback前に新版のdata/karin_daily.sqlite3を別名退避する。
