import CamadaEnlace as ce
from bitarray import bitarray

FLAG_SEQUENCE = [0,1,1,1,1,1,1,0]
ESCAPE_CHAR   = [0,0,0,1,1,0,1,1]
CRC32_DEGREE = 32


# ==========================
# Auxiliares Aplicação
# ==========================

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


# ==========================
# DESENQUADRAMENTO (RX)
# ==========================

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


# ==========================
# VERIFICAÇÃO / CORREÇÃO (RX)
# ==========================

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


def corr_haming(framing_method: str, bits: list[int]):
    out = []

    for i in range(0, len(bits), 7):
        chunk = bits[i:i+7]
        if len(chunk) < 7:
            continue

        p1, p2, m3, p4, m5, m6, m7 = chunk

        s1 = p1 ^ m3 ^ m5 ^ m7
        s2 = p2 ^ m3 ^ m6 ^ m7
        s3 = p4 ^ m5 ^ m6 ^ m7

        pos = int(f"{s3}{s2}{s1}", 2)

        if pos != 0:
            chunk[pos-1] ^= 1  # corrige

        # dados SEMPRE são adicionados
        out += [chunk[2], chunk[4], chunk[5], chunk[6]]

    return out
