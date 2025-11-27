from bitarray import bitarray

# Constantes importantes usadas pelos métodos de enquadramento
# FLAG é usada para marcar início/fim de quadro
FLAG_SEQUENCE = [0,1,1,1,1,1,1,0]  # 0x7E
# ESC é usada no byte stuffing para indicar que o próximo byte faz parte dos dados
ESCAPE_CHAR   = [0,0,0,1,1,0,1,1]  # 0x1B

# Polinômio gerador do CRC-32 (na forma binária)
CRC32_POLY = [1,0,0,0,0,0,1,0,0,1,1,0,0,0,0,0,1,0,0,0,1,1,1,0,1,1,0,1,1,0,1,1,1]
CRC32_DEGREE = 32

# Auxiliar: converte texto para sequência de bits

def convert_to_bytes(text: str) -> list[int]:
    """
    Converte a string de entrada em uma lista de bits.
    A biblioteca bitarray facilita a conversão para bytes
    e depois para bits individuais.
    """
    arr = bitarray()
    arr.frombytes(text.encode('utf-8','surrogatepass'))
    return [int(b) for b in arr]

# ENQUADRAMENTO (TX)   

def character_count(bit_stream: list[int], header_bits=8) -> list[int]:
    """
    Implementa a técnica de contagem de caracteres.
    Insere no início um cabeçalho informando o tamanho do payload em bits.
    """
    length = len(bit_stream)
    header = bin(length)[2:].zfill(header_bits)
    return [int(b) for b in header] + bit_stream


def byte_insertion(bit_stream: list[int]) -> list[int]:
    """
    Enquadramento com FLAG + byte stuffing.
    Sempre que um byte igual à FLAG ou ao ESC aparece,
    insere-se primeiro o byte ESC seguido do próprio byte.
    Isso evita que o receptor confunda com marcas de início/fim.
    """
    stuffed = []
    for i in range(0, len(bit_stream), 8):
        byte = bit_stream[i:i+8]

        # completa o byte caso o último tenha menos de 8 bits
        if len(byte) < 8:
            byte += [0] * (8 - len(byte))

        # se for FLAG ou ESC, aplica stuffing
        if byte == FLAG_SEQUENCE or byte == ESCAPE_CHAR:
            stuffed += ESCAPE_CHAR + byte
        else:
            stuffed += byte

    # adiciona FLAG no início e no fim do quadro
    return FLAG_SEQUENCE + stuffed + FLAG_SEQUENCE


def bit_insertion(bit_stream: list[int]) -> list[int]:
    """
    Enquadramento com FLAG + bit stuffing.
    Sempre que aparecem 5 bits '1' seguidos, insere-se um '0'
    para evitar que o padrão FLAG apareça dentro dos dados.
    """
    stuffed = []
    ones = 0

    for bit in bit_stream:
        stuffed.append(bit)

        if bit == 1:
            ones += 1
            # se atingiu 5 '1's, insere um zero extra
            if ones == 5:
                stuffed.append(0)
                ones = 0
        else:
            ones = 0

    return FLAG_SEQUENCE + stuffed + FLAG_SEQUENCE

# DETECÇÃO / CORREÇÃO (TX)

def bit_parity(bit_stream: list[int]) -> list[int]:
    """
    Bit de paridade par: adiciona 1 bit no final
    que indica se o total de '1's é par ou ímpar.
    """
    parity = sum(bit_stream) % 2
    return bit_stream + [parity]


# CRC-32

def calculate_crc_remainder(data_with_padding: list[int]) -> list[int]:
    """
    Aplica a divisão binária (XOR) do CRC.
    O polinômio é percorrido sobre os bits, e no final
    os últimos 32 bits são o resto (checksum).
    """
    temp = data_with_padding.copy()

    for i in range(len(temp) - CRC32_DEGREE):
        if temp[i] == 1:
            for j in range(len(CRC32_POLY)):
                temp[i+j] ^= CRC32_POLY[j]

    return temp[-CRC32_DEGREE:]


def prepara_CRC_para_transmissao(bits: list[int]) -> list[int]:
    """
    Para calcular o CRC corretamente, adiciona-se 32 zeros ao final.
    Depois, o resto da divisão é colocado no lugar dos zeros.
    """
    padded = bits + [0] * CRC32_DEGREE
    rem = calculate_crc_remainder(padded)
    return bits + rem




# HAMMING DINÂMICO

def hamming_dinamico(bit_stream: list[int]) -> list[int]:
    """
    Implementação de Hamming com blocos de tamanho fixo.
    Usa blocos de tamanho padrão: Hamming(7,4), (15,11), (31,26), (63,57)
    Formato: (n, k) onde n = tamanho total, k = bits de dados
    """
    encoded = []
    idx = 0
    L = len(bit_stream)

    # Configurações padrão: (tamanho_bloco, bits_dados, bits_paridade)
    hamming_configs = [
        (63, 57, 6),  # Hamming(63,57) - 6 bits de paridade
        (31, 26, 5),  # Hamming(31,26) - 5 bits de paridade  
        (15, 11, 4),  # Hamming(15,11) - 4 bits de paridade
        (7, 4, 3),    # Hamming(7,4) - 3 bits de paridade
    ]

    while idx < L:
        # Escolhe o maior bloco que cabe nos bits restantes
        bits_restantes = L - idx
        n, k, p = None, None, None
        
        for config in hamming_configs:
            if config[1] <= bits_restantes:
                n, k, p = config
                break
        
        # Se nenhum bloco padrão cabe, usa o menor
        if n is None:
            n, k, p = 7, 4, 3
        
        # Extrai k bits de dados (com padding se necessário)
        data_bits = bit_stream[idx : idx + k]
        if len(data_bits) < k:
            data_bits = data_bits + [0] * (k - len(data_bits))
        idx += len(bit_stream[idx : idx + k])  # avança apenas pelos bits reais
        
        # Cria bloco Hamming indexado a partir de 1
        block = [None] * (n + 1)
        
        # Posições de paridade: 1, 2, 4, 8, 16, 32
        parity_positions = [2 ** i for i in range(p)]
        
        # Preenche bits de dados nas posições não-paridade
        data_idx = 0
        for pos in range(1, n + 1):
            if pos not in parity_positions:
                block[pos] = data_bits[data_idx] if data_idx < len(data_bits) else 0
                data_idx += 1
        
        # Calcula bits de paridade
        for parity_pos in parity_positions:
            xor_sum = 0
            for pos in range(1, n + 1):
                # Se a posição tem o bit de paridade ativo
                if pos & parity_pos:
                    if block[pos] is not None:
                        xor_sum ^= block[pos]
            block[parity_pos] = xor_sum
        
        # Adiciona bloco ao resultado (ignorando índice 0)
        encoded.extend(block[1:])

    return encoded
