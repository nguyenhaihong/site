import socket
import threading
import time
import traceback
from collections import defaultdict
from heapq import heappush, heappop

__author__ = 'Quantum'


class BaseServer(object):
    def __init__(self, host, port, client):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setblocking(0)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((host, port))
        self._stop = threading.Event()
        self._clients = set()
        self._ClientClass = client
        self._send_queue = defaultdict(str)
        self._job_queue = []
        self._job_queue_lock = threading.Lock()

    def _serve(self):
        raise NotImplementedError()

    def _accept(self):
        conn, address = self._server.accept()
        conn.setblocking(0)
        client = self._ClientClass(self, conn)
        self._clients.add(client)
        return client

    def schedule(self, delay, job):
        with self._job_queue_lock:
            heappush(self._job_queue, (time.time() + delay, job))

    def _register_write(self, client):
        raise NotImplementedError()

    def _register_read(self, client):
        raise NotImplementedError()

    def _clean_up_client(self, client, finalize=False):
        try:
            del self._send_queue[client.fileno()]
        except KeyError:
            pass
        client.on_close()
        client._socket.close()
        if not finalize:
            self._clients.remove(client)

    def _dispatch_event(self):
        t = time.time()
        tasks = []
        with self._job_queue_lock:
            while True:
                dt = self._job_queue[0][0] - t if self._job_queue else 1
                if dt > 0:
                    break
                tasks.append(heappop(self._job_queue)[1])
        for task in tasks:
            task()
        if not self._job_queue or dt > 1:
            dt = 1
        return dt

    def _nonblock_read(self, client):
        try:
            data = client._socket.recv(1024)
        except socket.error:
            self._clean_up_client(client)
        else:
            if not data:
                self._clean_up_client(client)
            else:
                try:
                    client._recv_data(data)
                except Exception:
                    traceback.print_exc()
                    self._clean_up_client(client)

    def _nonblock_write(self, client):
        fd = client.fileno()
        try:
            cb = client._socket.send(self._send_queue[fd])
            self._send_queue[fd] = self._send_queue[fd][cb:]
            if not self._send_queue[fd]:
                self._register_read(client)
                del self._send_queue[fd]
        except socket.error:
            self._clean_up_client(client)

    def send(self, client, data):
        self._send_queue[client.fileno()] += data
        self._register_write(client)

    def stop(self):
        self._stop.set()

    def serve_forever(self):
        self._serve()