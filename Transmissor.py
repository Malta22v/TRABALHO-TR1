import time
from bitarray import bitarray
import socket

def startServer(message, host='127.0.0.1', port=12345, max_retries=3):
    """
    Envia uma sequência de bits para um servidor TCP.
    Realiza múltiplas tentativas caso o servidor não esteja disponível.
    """

    bit_data = bitarray() #Transforma array de bits em dados
    bit_data.extend(message)
    byte_array = bit_data.tobytes()
    
    # Loop de tentativas de conexão
    for tentativa in range(maximo_de_tentativas):
        try: # Cria o socket dentro do bloco 'with' para fechar automaticamente
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(byte_array)
                print("Envio de dados concluído!")
                return True
        except ConnectionRefusedError:
            print(f"Tentativa {tentativa + 1}/{maximo_de_tentativas} - Servidor com ero...")
            time.sleep(1)
    print("Não foi possível estabelecer conexão após todas as tentativas.")
    return False