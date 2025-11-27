import CamadaEnlace as ce
from bitarray import bitarray

# Constantes usadas no desenquadramento
FLAG_SEQUENCE = [0,1,1,1,1,1,1,0]
ESCAPE_CHAR   = [0,0,0,1,1,0,1,1]
CRC32_DEGREE = 32



# ==========================================================
# Auxiliares da camada de aplicação
# ==========================================================

def is_valid_utf8(bts: bytes):
    """
    Verifica se a sequência de bytes pode ser decodificada como UTF-8.
    Isso evita que o programa tente converter algo inválido para texto.
    """
    try:
        bts.decode('utf-8')
        return True
    except:
        return False
    

def bit_list_to_text(bits: list[int]):
    """
    Converte uma lista de bits novamente para texto.
    Caso não seja UTF-8 válido, devolve uma mensagem de erro amigável.
    """
    arr = bitarray(bits)
    data = arr.tobytes()

    if is_valid_utf8(data):
        return data.decode('utf-8','surrogatepass')
    
    return "Sequência de bits impossível de decodificar"



# ==========================================================
# DESENQUADRAMENTO (RX)
# ==========================================================

def decode_charactere_count(bits: list[int], header_size=8):
    """
    Remove o cabeçalho inserido pelo método de contagem de caracteres.
    Basta descartar os primeiros 'header_size' bits.
    """
    payload = bits[header_size:]
    return bit_list_to_text(payload)


def decode_byte_insertion(bits: list[int]):
    """
    Realiza o processo inverso do byte stuffing.
    Remove as FLAGS de início/fim e interpreta ESC + byte como dados originais.
    """
    # remove FLAG inicial e final
    payload = bits[8:len(bits)-8]
    res = []
    i = 0

    while i < len(payload):
        byte = payload[i:i+8]

        # se encontrou ESC, significa que o próximo byte é literal
        if byte == ESCAPE_CHAR:
            i += 8
            res += payload[i:i+8]
        else:
            res += byte

        i += 8

    return bit_list_to_text(res)


def decode_bit_insertion(bits: list[int]):
    """
    Processo inverso do bit stuffing.
    Sempre que encontrar um zero após cinco '1's, descarta esse zero.
    """
    payload = bits[8:len(bits)-8]
    res = []
    ones = 0

    for b in payload:
        if b == 1:
            res.append(1)
            ones += 1
        else:
            # se encontrou 0 após cinco 1s, esse zero é stuffing e deve ser removido
            if ones == 5:
                ones = 0
                continue
            res.append(0)
            ones = 0

    return bit_list_to_text(res)



# ==========================================================
# VERIFICAÇÃO / CORREÇÃO (RX)
# ==========================================================

def verifica_bit_parity(bits: list[int]):
    """
    Verifica paridade par: se a soma for ímpar, há erro.
    Remove o bit de paridade antes de retornar.
    """
    if sum(bits) % 2 != 0:
        return "Erro detectado - Bit de Paridade", bits[:-1]
    return "OK", bits[:-1]


def verifica_crc(bits: list[int]):
    """
    Recalcula o CRC do quadro recebido.
    Se o resto não for todo zero, houve erro na transmissão.
    """
    rem = ce.calculate_crc_remainder(bits)
    data = bits[:-CRC32_DEGREE]

    if not all(b == 0 for b in rem):
        return "Erro detectado - CRC", data
    
    return "OK", data



# ==========================================================
# CORREÇÃO DE HAMMING DINÂMICO (RX)
# ==========================================================

def corr_hamming_dinamico(bits: list[int]) -> list[int]:
    """
    Decodifica e corrige blocos Hamming.
    Usa blocos de tamanho padrão: 7, 15, 31, 63
    """
    out = []
    i = 0
    L = len(bits)

    # Configurações Hamming: (tamanho_total, bits_paridade)
    hamming_configs = [
        (63, 6),
        (31, 5),
        (15, 4),
        (7, 3),
    ]

    while i < L:
        # Identifica qual bloco usar baseado nos bits restantes
        bits_restantes = L - i
        n, p = None, None
        
        for config in hamming_configs:
            if config[0] <= bits_restantes:
                n, p = config
                break
        
        # Se não couber nenhum bloco padrão, tenta o menor
        if n is None:
            if bits_restantes >= 7:
                n, p = 7, 3
            else:
                # Não há bits suficientes para um bloco válido
                break
        
        # Extrai o bloco
        chunk = bits[i:i+n]
        if len(chunk) < n:
            break
        i += n

        # Posições de paridade: 1, 2, 4, 8, 16, 32
        parity_positions = [2 ** j for j in range(p)]

        # 2. calcular síndrome
        syndrome = 0
        for pp in parity_positions:
            xor_sum = 0
            for pos in range(1, n + 1):
                if pos & pp:
                    xor_sum ^= chunk[pos - 1]
            if xor_sum == 1:
                syndrome += pp

        # 3. corrige caso haja erro em uma posição válida
        if syndrome != 0 and syndrome <= n:
            chunk[syndrome - 1] ^= 1

        # 4. extrai bits de dados (não-paridade)
        for pos in range(1, n + 1):
            if pos not in parity_positions:
                out.append(chunk[pos - 1])

    return out
