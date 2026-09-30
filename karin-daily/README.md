# Karin Daily

軽量な個人向けニュース一面MVP。収集、AI分類、SQLite保存、HTML表示を一つの小さなサービスにまとめています。

```sh
python3 karin_daily.py --once
python3 karin_daily.py --serve --host 127.0.0.1 --port 8088
```

本番では `/opt/karin-daily` に配置し、`karin-daily.service` と `karin-daily.timer` を使用します。設定は環境変数または `config.json` で変更できます。

