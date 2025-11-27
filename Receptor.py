import socket
import threading
from bitarray import bitarray
import random

class Receiver:
    def __init__(self):
        self.received_data = None
        self.data_ready = threading.Event()
        self.sent_data = None
        self.changed_bit_position = None
        self.server_running = False   # evita iniciar o servidor duas vezes

    def TCPServer(self, host='127.0.0.1', port=12345):

        # --- proteção para evitar múltiplos servidores ---
        if self.server_running:
            print("Servidor já está rodando. Ignorando nova tentativa.")
            return
        self.server_running = True

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            # --- permite reusar a porta imediatamente ---
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                s.bind((host, port))
            except OSError as e:
                print(f"Erro ao tentar fazer bind na porta {port}: {e}")
                self.server_running = False
                return

            s.listen()
            print(f"Servidor aguardando conexão em {host}:{port}...")

            try:
                conn, addr = s.accept()
            except Exception as e:
                print("Erro ao aceitar conexão:", e)
                self.server_running = False
                return

            with conn:
                print(f"Conexão estabelecida com {addr}")
                self.received_data = conn.recv(1024)
                print(f"Dados recebidos: {self.received_data}")

                # converte bytes → trem de bits (bitarray)
                byte_to_bit = bitarray()
                byte_to_bit.frombytes(self.received_data)
                self.sent_data = byte_to_bit.tolist()

                # sinaliza que os dados estão prontos para a GUI
                self.data_ready.set()

        # --- servidor finalizado ---
        self.server_running = False
