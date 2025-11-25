from bitarray import bitarray

# --- Constantes de Enlace ---
FLAG_SEQUENCE = [0, 1, 1, 1, 1, 1, 1, 0]  # 0x7E
ESCAPE_CHAR = [0, 0, 0, 1, 1, 0, 1, 1]   # 0x1B (ESC)
CRC32_POLY = [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1]
CRC32_DEGREE = 32

# --- Camada de Aplicação (Auxiliar) ---

def text_to_bit_list(text: str, encoding='utf-8', errors='surrogatepass') -> list[int]:
    bin_array = bitarray()
    bin_array.frombytes(text.encode(encoding, errors))
    return [int(bit) for bit in bin_array]

# --- Camada de Enlace: Enquadramento (TX) ---

def frame_char_count(bit_stream: list[int], header_bits=8) -> list[int]:
    stream_length = len(bit_stream)
    header_str = bin(stream_length)[2:].zfill(header_bits)
    frame_header = [int(bit) for bit in header_str]
    return frame_header + bit_stream

def frame_byte_stuffing(bit_stream: list[int]) -> list[int]:
    stuffed_stream = []
    
    for i in range(0, len(bit_stream), 8):
        byte_chunk = bit_stream[i:i+8]
        
        if len(byte_chunk) < 8:
            byte_chunk.extend([0] * (8 - len(byte_chunk)))

        if byte_chunk == FLAG_SEQUENCE or byte_chunk == ESCAPE_CHAR:
            stuffed_stream.extend(ESCAPE_CHAR)
            stuffed_stream.extend(byte_chunk)
        else:
            stuffed_stream.extend(byte_chunk)
            
    return FLAG_SEQUENCE + stuffed_stream + FLAG_SEQUENCE

def frame_bit_stuffing(bit_stream: list[int]) -> list[int]:
    # (VERSÃO CORRIGIDA)
    stuffed_stream = []
    one_count = 0
    
    for bit in bit_stream:
        stuffed_stream.append(bit)
        
        if bit == 1:
            one_count += 1
            if one_count == 5:
                stuffed_stream.append(0)
                one_count = 0
        else:
            one_count = 0
            
    return FLAG_SEQUENCE + stuffed_stream + FLAG_SEQUENCE

# --- Camada de Enlace: Detecção/Correção de Erros (TX) ---

def apply_even_parity(bit_stream: list[int]) -> list[int]:
    ones_count = sum(bit_stream)
    parity_bit = ones_count % 2
    return bit_stream + [parity_bit]

def calculate_crc_remainder(data_with_padding: list[int]) -> list[int]:
    temp_data = list(data_with_padding)
    poly_len = len(CRC32_POLY)

    for i in range(len(temp_data) - CRC32_DEGREE):
        if temp_data[i] == 1:
            for j in range(poly_len):
                temp_data[i + j] = temp_data[i + j] ^ CRC32_POLY[j]
    
    remainder = temp_data[-CRC32_DEGREE:]
    return remainder

def create_crc_frame(original_data: list[int]) -> list[int]:
    data_to_calculate = original_data + [0] * CRC32_DEGREE
    crc_calculated = calculate_crc_remainder(data_to_calculate)
    frame_to_send = original_data + crc_calculated
    return frame_to_send

def encode_hamming_7_4(bit_stream: list[int]) -> list[int]:
    encoded_stream = []
    
    for i in range(0, len(bit_stream), 4):
        data_chunk = bit_stream[i:i+4]
        
        if len(data_chunk) < 4:
            data_chunk.extend([0] * (4 - len(data_chunk)))
        
        m3, m5, m6, m7 = data_chunk[0], data_chunk[1], data_chunk[2], data_chunk[3]
        
        p1 = m3 ^ m5 ^ m7
        p2 = m3 ^ m6 ^ m7
        p4 = m5 ^ m6 ^ m7
        
        hamming_byte = [p1, p2, m3, p4, m5, m6, m7]
        encoded_stream.extend(hamming_byte)
            
    return encoded_stream