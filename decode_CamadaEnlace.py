import CamadaEnlace as ce
from bitarray import bitarray

FLAG_SEQUENCE = [0,1,1,1,1,1,1,0]
ESCAPE_CHAR   = [0,0,0,1,1,0,1,1]
CRC32_DEGREE = 32



# Auxiliares Aplicação


def is_valid_utf8(bts:bytes):
    try:
        bts.decode('utf-8')
        return True
    except:
        return False
    

def bit_list_to_text(bits:list[int]):
    arr = bitarray(bits)
    data = arr.tobytes()
    if is_valid_utf8(data):
        return data.decode('utf-8','surrogatepass')
    return "Sequência de bits impossível de decodificar"



# DESENQUADRAMENTO (RX)


def decode_charactere_count(bits:list[int], header_size=8):
    payload = bits[header_size:]
    return bit_list_to_text(payload)


def decode_byte_insertion(bits:list[int]):
    payload = bits[8:len(bits)-8]
    res = []
    i = 0

    while i < len(payload):
        byte = payload[i:i+8]

        if byte == ESCAPE_CHAR:
            i += 8
            res += payload[i:i+8]
        else:
            res += byte

        i += 8

    return bit_list_to_text(res)


def decode_bit_insertion(bits:list[int]):
    payload = bits[8:len(bits)-8]
    res = []
    ones = 0

    for b in payload:
        if b == 1:
            res.append(1)
            ones += 1
        else:  # b == 0
            if ones == 5:
                ones = 0
                # este zero é descartado (stuffing)
                continue
            res.append(0)
            ones = 0

    return bit_list_to_text(res)



#VERIFICAÇÃO / CORREÇÃO (RX)

def verifica_bit_parity(bits:list[int]):
    if sum(bits) % 2 != 0:
        return "Erro detectado - Bit de Paridade", bits[:-1]
    return "OK", bits[:-1]


def verifica_crc(bits:list[int]):
    rem = ce.calculate_crc_remainder(bits)
    data = bits[:-CRC32_DEGREE]
    if not all(b == 0 for b in rem):
        return "Erro detectado - CRC", data
    return "OK", data


def corr_hamming_dinamico(bits: list[int]) -> list[int]:
    out = []
    i = 0
    L = len(bits)

    while i < L:

        # --- 1. descobrir automaticamente o tamanho do bloco ---
        # tentar blocos Hamming possíveis: 7,15,31,63
        possible_sizes = [7, 15, 31, 63]
        block_size = None

        for size in possible_sizes:
            if i + size <= L:
                block_size = size
                break

        if block_size is None:
            break

        chunk = bits[i:i+block_size]
        i += block_size

        n = block_size
        p = 0
        while (2 ** p) < (n + 1):
            p += 1

        parity_positions = [2 ** j for j in range(p) if 2**j <= n]

        # --- 2. calcular síndrome ---
        syndrome = 0
        for pp in parity_positions:
            xor_sum = 0
            for pos in range(1, n + 1):
                if pos & pp:
                    xor_sum ^= chunk[pos - 1]
            if xor_sum == 1:
                syndrome += pp

        # --- 3. corrigir ---
        if syndrome != 0 and syndrome <= n:
            chunk[syndrome - 1] ^= 1

        # --- 4. extrair bits de dados ---
        for pos in range(1, n + 1):
            if pos not in parity_positions:
                out.append(chunk[pos - 1])

    return out
