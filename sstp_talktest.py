#!/usr/bin/env python3
"""ランダムトーク実機確認用 SSTP NOTIFY 送信スクリプト（WSL内で実行する）

使い方:
  python3 sstp_talktest.py

動作:
  - WSLのデフォルトゲートウェイ（Windowsホスト）の portproxy 中継
    ポート 19801（→127.0.0.1:9801）へ SSTP NOTIFY を送る
  - Event: OnFurfurTalkTest / IfGhost: アスタロト
  - ゴースト辞書（astaroth_talk.dic）のフックが RandomTalk を1本返し、
    SSP の画面上で即座にランダムトークが再生される
  - 送信方式は voice_work/say.py の send_notify と同型
"""
import re
import socket
import subprocess
import sys

PORT = 19801


def gateway_ip() -> str:
    out = subprocess.check_output(["ip", "route"]).decode()
    m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", out)
    if not m:
        raise RuntimeError("default gateway not found")
    return m.group(1)


def main() -> int:
    lines = [
        "NOTIFY SSTP/1.1",
        "Charset: UTF-8",
        "Sender: Astaroth",
        "Event: OnFurfurTalkTest",
        "IfGhost: アスタロト",
        "",
        "",
    ]
    req = "\r\n".join(lines).encode("utf-8")
    host = gateway_ip()
    print(f"-> {host}:{PORT} NOTIFY OnFurfurTalkTest")
    sock = socket.create_connection((host, PORT), timeout=15)
    sock.settimeout(40)
    sock.sendall(req)
    chunks = []
    try:
        while True:
            b = sock.recv(4096)
            if not b:
                break
            chunks.append(b)
            if b"\r\n\r\n" in b"".join(chunks):
                break
    except socket.timeout:
        pass
    sock.close()
    raw = b"".join(chunks)
    try:
        resp = raw.decode("utf-8")
    except UnicodeDecodeError:
        resp = raw.decode("shift_jis", errors="replace")
    print("--- SSP response ---")
    print(resp if resp else "(empty)")
    ok = "200 OK" in resp and "Script:" in resp
    print("TALK PLAYED" if ok else "NOT PLAYED (check response)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
