from bitarray import bitarray

#Constantes

FLAG_SEQUENCE = [0,1,1,1,1,1,1,0]  # 0x7E
ESCAPE_CHAR   = [0,0,0,1,1,0,1,1]  # 0x1B
CRC32_POLY = [1,0,0,0,0,0,1,0,0,1,1,0,0,0,0,0,1,0,0,0,1,1,1,0,1,1,0,1,1,0,1,1,1]
CRC32_DEGREE = 32




# Auxiliares Aplicação



def convert_to_bytes(text: str) -> list[int]:
    arr = bitarray()
    arr.frombytes(text.encode('utf-8','surrogatepass'))
    return [int(b) for b in arr]


#ENQUADRAMENTO (TX)


def character_count(bit_stream: list[int], header_bits=8) -> list[int]:
    length = len(bit_stream)
    header = bin(length)[2:].zfill(header_bits)
    return [int(b) for b in header] + bit_stream


def byte_insertion(bit_stream: list[int]) -> list[int]:
    stuffed = []
    for i in range(0, len(bit_stream), 8):
        byte = bit_stream[i:i+8]

        if len(byte) < 8:
            byte += [0] * (8 - len(byte))

        if byte == FLAG_SEQUENCE or byte == ESCAPE_CHAR:
            stuffed += ESCAPE_CHAR + byte
        else:
            stuffed += byte

    return FLAG_SEQUENCE + stuffed + FLAG_SEQUENCE


def bit_insertion(bit_stream: list[int]) -> list[int]:
    stuffed = []
    ones = 0

    for bit in bit_stream:
        stuffed.append(bit)

        if bit == 1:
            ones += 1
            if ones == 5:
                stuffed.append(0)
                ones = 0
        else:
            ones = 0

    return FLAG_SEQUENCE + stuffed + FLAG_SEQUENCE



#DETECÇÃO / CORREÇÃO (TX)


def bit_parity(bit_stream: list[int]) -> list[int]:
    parity = sum(bit_stream) % 2
    return bit_stream + [parity]

#CRC-32

def calculate_crc_remainder(data_with_padding: list[int]) -> list[int]:
    temp = data_with_padding.copy()
    for i in range(len(temp) - CRC32_DEGREE):
        if temp[i] == 1:
            for j in range(len(CRC32_POLY)):
                temp[i+j] ^= CRC32_POLY[j]
    return temp[-CRC32_DEGREE:]


def prepara_CRC_para_transmissao(bits: list[int]) -> list[int]:
    padded = bits + [0] * CRC32_DEGREE
    rem = calculate_crc_remainder(padded)
    return bits + rem


#HAMMING

def hamming_dinamico(bit_stream: list[int]) -> list[int]:
    encoded = []
    idx = 0
    L = len(bit_stream)

    while idx < L:

        # --- 1. descobrir o maior bloco possível ---
        max_d = min(57, L - idx)  # limite para Hamming real (6 bits de paridade)
        d = max_d

        while d > 0:
            p = 0
            while (2 ** p) < (p + d + 1):
                p += 1
            if d + p <= 63:  # bloco máximo razoável
                break
            d -= 1

        # dados do bloco
        data_bits = bit_stream[idx : idx + d]
        idx += d

        # --- 2. criar bloco com espaços para paridade ---
        n = d + p
        block = [None] * (n + 1)  # posição 1-indexed

        # posições de paridade: 1,2,4,8,...
        parity_positions = [2 ** i for i in range(p)]

        # preencher dados
        di = 0
        for pos in range(1, n + 1):
            if pos not in parity_positions:
                if di < d:
                    block[pos] = data_bits[di]
                else:
                    block[pos] = 0  # padding
                di += 1

        # --- 3. calcular bits de paridade ---
        for pp in parity_positions:
            xor_sum = 0
            for pos in range(1, n + 1):
                if pos & pp:  # se bit correspondente é 1
                    val = block[pos]
                    if val is not None:
                        xor_sum ^= val
            block[pp] = xor_sum

        # remover índice 0
        encoded.extend(block[1:])

    return encoded
