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

    def TCPServer(self, host='127.0.0.1', port=12345):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            print(f"Servidor aguardando conexão em {host}:{port}...")
            conn, addr = s.accept()

            with conn:
                print(f"Conexão estabelecida com {addr}")
                self.received_data = conn.recv(1024)
                print(f"Dados recebidos: {self.received_data}")

                #pega a informação recebida em bytes e transforma em trem de bits
                byte_to_bit = bitarray()
                byte_to_bit.frombytes(self.received_data)
                self.sent_data = byte_to_bit.tolist()
                
                # Adiciona erro através de flip aleatório de bits
                for i in range(0, len(self.sent_data)):
                    if random.randint(0, 100) <= 5:
                        self.changed_bit_position = i+1
                        if self.sent_data[i] == 1:
                            self.sent_data[i] = 0
                        else:
                            self.sent_data[i] = 1
                        break
                self.data_ready.set()  # Sinaliza que os dados estão prontos