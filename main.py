import socket
import threading
import os

PORT = int(os.environ.get("PORT", 9999))
rooms = {}
lock = threading.Lock()


def handle_client(conn, addr):
    role, room_id = None, None
    buffer = b""
    try:
        while b"\n" not in buffer:
            data = conn.recv(1024)
            if not data:
                return
            buffer += data
        idx = buffer.index(b"\n")
        first_line = buffer[:idx].decode("utf-8", errors="ignore").strip()
        buffer = buffer[idx + 1:]
        if first_line.startswith("A_"):
            role, room_id = "A", first_line[2:]
        elif first_line.startswith("B_"):
            role, room_id = "B", first_line[2:]
        else:
            return
        print(f"[+] {role} in room {room_id} from {addr}")
        with lock:
            rooms.setdefault(room_id, {})[role] = conn
        with lock:
            peer_role = "B" if role == "A" else "A"
            peer = rooms.get(room_id, {}).get(peer_role)
        if peer and buffer:
            try:
                peer.sendall(buffer)
            except Exception:
                pass
        while True:
            data = conn.recv(65536)
            if not data:
                break
            with lock:
                peer_role = "B" if role == "A" else "A"
                peer = rooms.get(room_id, {}).get(peer_role)
            if peer:
                try:
                    peer.sendall(data)
                except Exception:
                    break
    except Exception as e:
        print(f"[-] {addr}: {e}")
    finally:
        with lock:
            if room_id and room_id in rooms:
                if role and rooms[room_id].get(role) is conn:
                    del rooms[room_id][role]
                if not rooms[room_id]:
                    del rooms[room_id]
        try:
            conn.close()
        except Exception:
            pass
        print(f"[-] {role} left {room_id}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(50)
    print(f"[*] Relay listening on 0.0.0.0:{PORT}")
    while True:
        conn, addr = server.accept()
        print(f"[+] Connection from {addr}")
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
