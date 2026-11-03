#!/usr/bin/env python3
"""アスタロト音声パイプライン用 SSTP 送信スクリプト（WSL内で実行する）

使い方:
  python3 sstp_say.py --text "喋る本文" [--mp3 /path/to/voice.mp3] [--port 19801] [--ghost アスタロト]

動作:
  - WSLのデフォルトゲートウェイ（Windowsホスト）へ SSTP SEND を送る
  - 既定ポートは portproxy 中継の 19801（→127.0.0.1:9801）。直通確認時は --port 9801
  - --mp3 を渡すと \\_v[UNCパス] で音声再生タグを付け、本文バルーンと同期させる
  - MP3の置き場所は WSL内 ~/voice_work/out/ を想定し、SSP(Windows)からは
    \\\\wsl.localhost\\Muse\\home\\muse\\voice_work\\out\\<file> で読ませる

注意（2026-11-01の事故の教訓）:
  さくらスクリプトのバックスラッシュは chr(92) で組み立てること。
  JSONやシェルを経由すると \\0 が NUL バイト化してスクリプトが壊れる。
"""
import argparse
import socket
import subprocess
import sys

B = chr(92)  # backslash


def gateway_ip() -> str:
    out = subprocess.check_output(["ip", "route"]).decode()
    for line in out.splitlines():
        if line.startswith("default"):
            return line.split()[2]
    raise RuntimeError("default gateway not found")


def build_script(text: str, mp3_unc: str | None) -> str:
    parts = [B + "0", B + "s[0]"]
    if mp3_unc:
        parts.append(B + "_v[" + mp3_unc + "]")
    parts.append(text)
    if mp3_unc:
        parts.append(B + "_V")
    parts.append(B + "e")
    return "".join(parts)


def send_sstp(host: str, port: int, script: str, ghost: str | None, timeout: int = 40) -> str:
    lines = [
        "SEND SSTP/1.4",
        "Charset: UTF-8",
        "Sender: Astaroth",
    ]
    if ghost:
        lines.append("IfGhost: " + ghost)
    lines.append("Script: " + script)
    lines.append("Option: notranslate")
    msg = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8")
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((host, port))
    s.sendall(msg)
    resp = b""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            resp += chunk
            if b"\r\n\r\n" in resp:
                break
    except socket.timeout:
        resp += b"<read timeout>"
    finally:
        s.close()
    return resp.decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help="バルーンに出す本文")
    ap.add_argument("--mp3", default=None, help="WSL内のMP3ファイル名（~/voice_work/out/ 配下の名前のみ）")
    ap.add_argument("--port", type=int, default=19801, help="送信先ポート（中継=19801 / 直通=9801）")
    ap.add_argument("--ghost", default=None, help="IfGhostで宛先ゴースト名を指定する場合のみ")
    args = ap.parse_args()

    mp3_unc = None
    if args.mp3:
        mp3_unc = (
            B + B + "wsl.localhost" + B + "Muse" + B + "home" + B + "muse"
            + B + "voice_work" + B + "out" + B + args.mp3
        )
    script = build_script(args.text, mp3_unc)
    host = gateway_ip()
    print(f"-> {host}:{args.port}")
    print("Script:", script)
    resp = send_sstp(host, args.port, script, args.ghost)
    print("RESPONSE:", resp)
    ok = "200 OK" in resp and "Script:" in resp
    print("PLAYED" if ok else "NOT PLAYED (check response)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
