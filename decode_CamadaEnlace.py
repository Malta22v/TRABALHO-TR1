# Importa o módulo do transmissor para reusar a função de CRC
import CamadaEnlace as ce 
from bitarray import bitarray

# --- Constantes de Enlace (Receptor) ---
FLAG_SEQUENCE = [0, 1, 1, 1, 1, 1, 1, 0]
ESCAPE_CHAR = [0, 0, 0, 1, 1, 0, 1, 1]
CRC32_DEGREE = 32

# --- Camada de Aplicação (Auxiliares) ---

def is_valid_utf8(byte_list):
    try:
        bytes(byte_list).decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

def bit_list_to_text(bits: list[int], encoding="utf-8", errors="surrogatepass"):
    array = bitarray(bits)
    data_bytes = array.tobytes()
    
    if is_valid_utf8(data_bytes):
        text_output = data_bytes.decode(encoding, errors)
    else:
        text_output = "Sequência de bits impossível de decodificar"
    return text_output

# --- Camada de Enlace: Desenquadramento (RX) ---

def rx_char_count_decode(bits: list[int], header_size=8):
    # Remove o cabeçalho para obter o payload
    payload = bits[header_size:]
    text_output = bit_list_to_text(payload)
    return text_output

def rx_byte_stuffing_decode(bits: list[int]):
    # (VERSÃO CORRIGIDA)
    unpacked_data = []
    # Remove as flags de início e fim
    payload = bits[8:len(bits)-8]

    i = 0
    while i < len(payload):
        byte_chunk = payload[i:i+8]
        
        if byte_chunk == ESCAPE_CHAR:
            # Pula o byte de 'escape' e adiciona o próximo byte
            i += 8 
            if i < len(payload):
                unpacked_data.extend(payload[i:i+8])
        else:
            # Byte de dados normal
            unpacked_data.extend(byte_chunk)
        
        i += 8
        
    text_output = bit_list_to_text(unpacked_data)
    return text_output

def rx_bit_stuffing_decode(bits: list[int]):
    # (VERSÃO CORRIGIDA E ALTERADA)
    unpacked_data = []
    one_count = 0
    payload = bits[8:len(bits)-8] # Remove flags

    for bit in payload:
        if bit == 1:
            unpacked_data.append(bit)
            one_count += 1
        else: # bit == 0
            if one_count == 5:
                # Se 5 '1's vieram antes, este '0' é stuffing
                one_count = 0 # Ignora o bit
            else:
                unpacked_data.append(bit)
                one_count = 0
    
    text_output = bit_list_to_text(unpacked_data)
    return text_output

# --- Camada de Enlace: Verificação de Erros (RX) ---

def check_even_parity(bit_stream: list[int]):
    # (VERSÃO CORRIGIDA)
    status = "OK"
    
    # Para paridade PAR, a soma total (dados + paridade) deve ser PAR
    if sum(bit_stream) % 2 != 0:
        status = "Erro detectado - Bit de Paridade"
    
    data_only = bit_stream[:-1] # Remove o bit de paridade
    return status, data_only

def check_crc(bit_stream: list[int]):
    # Reutiliza a função de cálculo do encoder
    # (Assumindo que o nome da função no seu "CamadaEnlace.py" é esta)
    remainder = ce.calculate_crc_remainder(bit_stream) 
    
    data_only = bit_stream[:-CRC32_DEGREE]
    
    # Se não houver erro, o resto deve ser '000...0'
    if not (all(bit == 0 for bit in remainder)):
        status = "Erro detectado - CRC"
        return status, data_only
    else:
        return "OK", data_only

def decode_and_correct_hamming(bit_stream: list[int]):
    # (VERSÃO CORRIGIDA - Sem 'hardcoding' de tamanho)
    unpacked_data = []
    
    # Processa o fluxo inteiro em blocos de 7 bits
    for i in range(0, len(bit_stream), 7):
        chunk = list(bit_stream[i:i+7])
        
        if len(chunk) < 7:
            continue # Ignora pedaços no final

        p1, p2, m3, p4, m5, m6, m7 = chunk[0], chunk[1], chunk[2], chunk[3], chunk[4], chunk[5], chunk[6]

        # Calcula a síndrome (posição do erro)
        s1 = (p1 ^ m3 ^ m5 ^ m7)
        s2 = (p2 ^ m3 ^ m6 ^ m7)
        s3 = (p4 ^ m5 ^ m6 ^ m7)
        
        error_pos_str = f"{s3}{s2}{s1}"
        error_index = int(error_pos_str, 2)
        
        if error_index != 0:
            # Corrige o bit na posição do erro
            bit_to_flip_idx = error_index - 1
            chunk[bit_to_flip_idx] = 1 - chunk[bit_to_flip_idx]
        
        # Extrai os 4 bits de dados originais
        unpacked_data.extend([chunk[2], chunk[4], chunk[5], chunk[6]])

    return unpacked_data