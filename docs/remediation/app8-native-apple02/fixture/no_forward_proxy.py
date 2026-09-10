#!/usr/bin/env python3
"""UNEXECUTED private draft: 25-second numeric-loopback canned HTTP proxy.

No outbound sockets, DNS, forwarding, subprocesses, PAC, or process supervision.
Counts every recv byte (including invalid requests). A receipt is only about this
socket, not proof that a native client could not contact some other endpoint.
"""
import argparse
import base64
import datetime
import json
import os
from pathlib import Path
import re
import signal
import socket
import time

HOSTS = ("raijinscan.co", "app8-probe.raijinscan.co")
LIFETIME_SECONDS = 25
BYTE_LIMIT = 8192
CONNECTION_LIMIT = 8


def save(directory, name, value):
    temporary = directory / (name + ".tmp")
    with temporary.open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")
    temporary.rename(directory / name)


def interrupted(signum, _frame):
    raise InterruptedError("Fixture interrupted by signal " + str(signum))


def exchange(connection, deadline, nonce, row):
    raw = bytearray()
    try:
        while b"\r\n\r\n" not in raw:
            connection.settimeout(min(1, max(0.001, deadline - time.monotonic())))
            block = connection.recv(min(2048, BYTE_LIMIT + 1 - len(raw)))
            if not block:
                row["peerEOF"] = True
                if raw:
                    raise ValueError("Incomplete HTTP header")
                return row  # A closed TCP connection with no bytes is recorded, not an HTTP request.
            raw.extend(block)
            if len(raw) > BYTE_LIMIT:
                raise ValueError("Request capture cap exceeded; incomplete observation")
        header, trailing = bytes(raw).split(b"\r\n\r\n", 1)
        lines = header.decode("ascii").split("\r\n")
        expected_lines = {"GET http://" + host + "/" + nonce + " HTTP/1.1": host for host in HOSTS}
        host = expected_lines.get(lines[0])
        if host is None or trailing:
            raise ValueError("Not an exact bodyless absolute-form probe request")
        headers = {}
        for line in lines[1:]:
            key, separator, value = line.partition(":")
            key = key.lower()
            if not separator or re.fullmatch("[a-z0-9-]+", key) is None or key in headers:
                raise ValueError("Invalid or duplicated HTTP header")
            headers[key] = value.strip()
        if headers.get("host") not in (host, host + ":80"):
            raise ValueError("Wrong Host header")
        if set(headers) & {"authorization", "proxy-authorization", "cookie", "cookie2", "transfer-encoding"}:
            raise ValueError("Credentials/cookies/transfer coding forbidden")
        if headers.get("content-length", "0") != "0":
            raise ValueError("Request body forbidden")
        body = ("app8-no-forward " + nonce + " " + host + "\n").encode("ascii")
        reply = ("HTTP/1.1 200 OK\r\nConnection: close\r\nCache-Control: no-store\r\n"
                 "Content-Type: text/plain; charset=utf-8\r\nContent-Length: " + str(len(body))
                 + "\r\nX-App8-Nonce: " + nonce + "\r\nX-App8-Host: " + host + "\r\n\r\n").encode("ascii")
        connection.sendall(reply + body)
        row.update(host=host, cannedResponseSent=True)
        connection.shutdown(socket.SHUT_WR)
        # Count any trailing bytes too; never silently ignore a body or second request.
        while len(raw) <= BYTE_LIMIT:
            connection.settimeout(min(1, max(0.001, deadline - time.monotonic())))
            block = connection.recv(min(2048, BYTE_LIMIT + 1 - len(raw)))
            if not block:
                row["peerEOF"] = True
                break
            raw.extend(block)
            row["error"] = "Unexpected bytes after request header"
        if len(raw) > BYTE_LIMIT:
            row["error"] = "Request capture cap exceeded; incomplete observation"
    except InterruptedError:
        raise
    except (OSError, ValueError) as failure:
        row["error"] = type(failure).__name__ + ": " + str(failure)
    finally:
        row["bytes"] = len(raw)
        row["rawBase64"] = base64.b64encode(raw).decode("ascii")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("allow", "deny"), required=True)
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if re.fullmatch("[0-9a-f]{32}", args.nonce) is None:
        parser.error("nonce must be fresh 32-character lowercase hex")
    os.umask(0o077)
    args.output.mkdir(mode=0o700, exist_ok=False)  # Parent must already be an owned private run path.
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, interrupted)
    started = time.monotonic()
    deadline = started + LIFETIME_SECONDS
    report = {"phase": args.phase, "nonce": args.nonce, "pid": os.getpid(),
              "bindHost": "127.0.0.1", "lifetimeSeconds": LIFETIME_SECONDS,
              "deadlineMonotonicSeconds": deadline,
              "windowComplete": False, "connections": [], "errors": [], "fixtureOK": False}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(4)
            report["port"] = listener.getsockname()[1]
            report["readyAtUTC"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            report["readyMonotonicSeconds"] = time.monotonic()
            save(args.output, "ready.json", {key: report[key] for key in
                 ("phase", "nonce", "pid", "bindHost", "port", "readyAtUTC", "lifetimeSeconds",
                  "readyMonotonicSeconds", "deadlineMonotonicSeconds")})
            while time.monotonic() < deadline:
                listener.settimeout(min(0.25, max(0.001, deadline - time.monotonic())))
                try:
                    connection, peer = listener.accept()
                except socket.timeout:
                    continue
                with connection:
                    if peer[0] != "127.0.0.1":
                        raise ValueError("Unexpected non-loopback peer")
                    if len(report["connections"]) >= CONNECTION_LIMIT:
                        raise ValueError("Connection cap exceeded; incomplete observation")
                    row = {"bytes": 0, "host": None, "cannedResponseSent": False,
                           "peerEOF": False, "error": None}
                    report["connections"].append(row)
                    exchange(connection, deadline, args.nonce, row)
            report["windowComplete"] = True
    except (OSError, ValueError) as failure:
        report["errors"].append(type(failure).__name__ + ": " + str(failure))
    finally:
        report["closedMonotonicSeconds"] = time.monotonic()
        report["closedAtUTC"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rows = report["connections"]
        report["receivedBytes"] = sum(row["bytes"] for row in rows)
        control = len(rows) == 2 and sorted(row["host"] or "" for row in rows) == sorted(HOSTS)
        control = control and all(row["cannedResponseSent"] and row["peerEOF"] for row in rows)
        complete = report["windowComplete"] and not report["errors"] and not any(row["error"] for row in rows)
        report["fixtureOK"] = complete and (control if args.phase == "allow" else report["receivedBytes"] == 0)
        report["elapsedSeconds"] = time.monotonic() - started
        save(args.output, "receipt.json", report)
    return 0 if report["fixtureOK"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
