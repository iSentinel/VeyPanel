"""Isolated CI HTTPS/WSS fixture. No production credentials, network exposure or state."""
import base64
import hashlib
import json
import ssl
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REVOKED = threading.Event()


class Fixture(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        """Do not print headers or request data."""

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def reply(self, code, payload=b""):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    @staticmethod
    def sample():
        return json.dumps(dict(timestampUtc=datetime.now(timezone.utc).isoformat(),
                               cpuPercent=42, status="ok")).encode()

    def do_GET(self):
        if self.path == "/api/v1/telemetry/ws":
            self.websocket()
            return
        if self.path not in ("/api/v1/telemetry", "/api/v1/history"):
            self.reply(404)
            return
        token = self.headers.get("Authorization", "")
        if token in ("Bearer " + "A" * 64, "Bearer " + "C" * 64) or (
                token == "Bearer " + "D" * 64 and not REVOKED.is_set()):
            if self.path == "/api/v1/history":
                stamp = datetime.now(timezone.utc).isoformat()
                payload = dict(timestampUtc=stamp, windowSeconds=900,
                               samples=[dict(timestampUtc=stamp, cpuPercent=42)])
                self.reply(200, json.dumps(payload).encode())
            else:
                self.reply(200, self.sample())
        else:
            self.reply(401)

    def websocket(self):
        key = self.headers.get("Sec-WebSocket-Key")
        if self.headers.get("Upgrade", "").lower() != "websocket" or not key:
            self.reply(400)
            return
        # Refuse the first upgrade only for the fallback scenario using the next-frame token:
        # no credentials occur in the handshake; accept and close after checking the token.
        accept = base64.b64encode(hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        self.send_response(101)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        self.close_connection = True
        try:
            header = self.rfile.read(2)
            if header != bytes([0x81, 0x80 | 64]):
                return
            mask = self.rfile.read(4)
            raw = self.rfile.read(64)
            if len(mask) != 4 or len(raw) != 64:
                return
            token = bytes(value ^ mask[i % 4] for i, value in enumerate(raw))
            if token == b"E"*64:
                # Advertise an excessive length without sending or allocating its payload.
                self.wfile.write(bytes([0x81, 127]) + (1024 * 1024 + 1).to_bytes(8, "big"))
                self.wfile.flush()
                return
            if token == b"F"*64:
                self.control_exchange()
                return
            if token == b"H"*64:
                self.frame(0x81, self.sample())
                # Stay silent after a valid sample until the client cancels.
                time.sleep(5)
                return
            if token == b"G"*64:
                self.frame(0x88, bytes([3, 237]))
                return
            if token not in (b"A"*64,b"D"*64):
                self.frame(0x88, bytes([3, 240]))
                return
            self.frame(0x81, self.sample())
            if token == b"D"*64:
                REVOKED.set()
            time.sleep(2)
            self.frame(0x88, bytes([3, 232]))
        except (OSError, ValueError):
            return

    def control_exchange(self):
        self.frame(0x89, b"check")
        if not self.client_frame(0x8a, b"check"):
            return
        self.frame(0x81, self.sample())
        self.frame(0x81, self.sample())
        self.frame(0x88, bytes([3, 232]))
        self.client_frame(0x88, bytes([3, 232]))

    def client_frame(self, opcode, payload):
        header = self.rfile.read(2)
        if header != bytes([opcode, 0x80 | len(payload)]):
            return False
        mask = self.rfile.read(4)
        raw = self.rfile.read(len(payload))
        if len(mask) != 4 or len(raw) != len(payload):
            return False
        return bytes(value ^ mask[i % 4] for i, value in enumerate(raw)) == payload

    def frame(self, opcode, payload):
        size = len(payload)
        header = bytes([opcode, size]) if size < 126 else bytes([opcode,126]) + size.to_bytes(2,"big")
        self.wfile.write(header + payload)
        self.wfile.flush()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1",47861),Fixture)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(sys.argv[1],sys.argv[2])
    server.socket = context.wrap_socket(server.socket,server_side=True)
    print("READY: isolated transport fixture",flush=True)
    server.serve_forever()
