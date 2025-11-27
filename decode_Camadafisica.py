import numpy as np
import matplotlib.pyplot as plt

V_POSITIVO = 1.0  
V_NEGATIVO = -1.0 
V_ZERO = 0.0      

# Fator de normalização para o 16-QAM ter a mesma energia média do QPSK
# QPSK amplitude 1 -> Energia 1. QAM níveis 1,3 -> Energia média 10.
# Fator de escala = sqrt(10)
NORM_QAM = np.sqrt(10) 
BIT_RATE = 1000 
TEMPO_BIT = 1/BIT_RATE
FREEQUENCIA_PORTADORA = 5000  # CORRIGIDO: deve ser igual ao da modulação
TAXA_DE_AMOSTRAGEM = 10 * FREEQUENCIA_PORTADORA 
AMOSTRAS_POR_BIT = int(TAXA_DE_AMOSTRAGEM / BIT_RATE)

def decode_nrz_polar(sinal):
    bits = []
    amostras = AMOSTRAS_POR_BIT
    # Limiar baseado na soma do sinal
    # Se sinal é +1, soma é +100. Se -1, soma é -100. Limiar é 0.
    limiar = 0.0 
    
    for i in range(0, len(sinal), amostras):
        chunk = sinal[i : i+amostras]
        if len(chunk) < amostras: break
        
        soma = np.sum(chunk)
        
        if soma > limiar:
            bits.append(1)
        else:
            bits.append(0)
    return np.array(bits)

def decode_manchester(sinal):
    bits = []
    amostras = AMOSTRAS_POR_BIT
    meio = amostras // 2
    
    for i in range(0, len(sinal), amostras):
        chunk = sinal[i : i+amostras]
        if len(chunk) < amostras: break
        
        # Divide o símbolo em duas metades
        parte1 = chunk[:meio]
        parte2 = chunk[meio:]
        
        # Correlaciona: (Parte2 - Parte1)
        # Se Bit 1 (-V, +V): (+V) - (-V) = +2V (Resultado Positivo)
        # Se Bit 0 (+V, -V): (-V) - (+V) = -2V (Resultado Negativo)
        valor_decisao = np.sum(parte2) - np.sum(parte1)
        
        if valor_decisao > 0:
            bits.append(1)
        else:
            bits.append(0)
    return np.array(bits)


def decode_bipolar(sinal):
    bits = []
    amostras = AMOSTRAS_POR_BIT
    
    # Limiar de Energia: Metade da energia esperada de um bit 1
    # Amplitude 1, N amostras -> Energia N. Limiar N/2.
    limiar_energia = (AMOSTRAS_POR_BIT * (V_POSITIVO**2)) / 4 
    #  0.5V de amplitude média
    
    for i in range(0, len(sinal), amostras):
        chunk = sinal[i : i+amostras]
        if len(chunk) < amostras: break
        
        # Bipolar: 1 tem energia, 0 não tem
        energia = np.sum(chunk**2)
        
        if energia > limiar_energia:
            bits.append(1)
        else:
            bits.append(0)
    return np.array(bits)


def decode_ask_modulate(sinal_com_ruido):
    bits = []
    t = np.linspace(0, TEMPO_BIT, AMOSTRAS_POR_BIT)
    
    # Cálculo dinâmico do limiar baseado na energia teórica
    template_1 = 1.0 * np.sin(2*np.pi*FREEQUENCIA_PORTADORA*t)
    energia_bit_1 = np.sum(template_1 ** 2)    
    limiar = energia_bit_1 / 2
    
    amostras_por_simbolo = AMOSTRAS_POR_BIT
    for i in range(0, len(sinal_com_ruido), amostras_por_simbolo):
        chunk = sinal_com_ruido[i : i+amostras_por_simbolo]
        if len(chunk) < amostras_por_simbolo:
            break
            
        energia = np.sum(chunk ** 2)

        if energia > limiar:
            bits.append(1)
        else:
            bits.append(0)
    return np.array(bits)

def decode_fsk_modulate(sinal_com_ruido):
    bits = []
    amostras_por_simbolo = AMOSTRAS_POR_BIT
    frequencia_desvio = 2000  # CORRIGIDO: deve ser igual ao da modulação
    t = np.linspace(0, TEMPO_BIT, AMOSTRAS_POR_BIT)
    
    template_0 = 1.0 * np.sin(2*np.pi*(FREEQUENCIA_PORTADORA + frequencia_desvio) * t)
    template_1 = 1.0 * np.sin(2*np.pi*(FREEQUENCIA_PORTADORA - frequencia_desvio) * t)
    
    for i in range(0, len(sinal_com_ruido), amostras_por_simbolo):
        chunk = sinal_com_ruido[i : i+amostras_por_simbolo]
        if len(chunk) < amostras_por_simbolo:
            break
            
        correlacao_0 = np.sum(chunk * template_0)
        correlacao_1 = np.sum(chunk * template_1)
        
        if correlacao_0 > correlacao_1:
            bits.append(1)
        else:
            bits.append(0)
    return np.array(bits)

def demodulate_psk_modulate(sinal_com_ruido):
    bits = []
    tempo_simbolo = 2 * TEMPO_BIT
    amostras_por_simbolo = 2 * AMOSTRAS_POR_BIT
    t = np.linspace(0, tempo_simbolo, 2 * AMOSTRAS_POR_BIT)

    for i in range(0, len(sinal_com_ruido), amostras_por_simbolo):
        chunk = sinal_com_ruido[i : i+amostras_por_simbolo]
        if len(chunk) < amostras_por_simbolo:
            break

        template_I = np.cos(2*np.pi*FREEQUENCIA_PORTADORA * t)
        template_Q = np.sin(2*np.pi*FREEQUENCIA_PORTADORA * t)

        valor_I = np.sum(chunk * template_I)
        valor_Q = np.sum(chunk * template_Q)
        
        bits_simbolo = []
        if abs(valor_I) > abs(valor_Q):
            if valor_I > 0:
                bits_simbolo = [0, 1] 
            else:
                bits_simbolo = [1, 0] 
        else:
            if valor_Q > 0:
                bits_simbolo = [0, 0] 
            else:
                bits_simbolo = [1, 1] 

        bits.extend(bits_simbolo)
    return np.array(bits)

def demodulate_qam_16(sinal_com_ruido):
    bits = []
    amostras_por_simbolo = int(4 * AMOSTRAS_POR_BIT) 
    tempo_simbolo = 4 * TEMPO_BIT
    t = np.linspace(0, tempo_simbolo, amostras_por_simbolo)

    QAM_16_MAP = {
        '0000': (-3, -3), '0001': (-3, -1), '0100': (-1, -3), '0101': (-1, -1),
        '0010': (-3,  3), '0011': (-3,  1), '0110': (-1,  3), '0111': (-1,  1),
        '1000': ( 3, -3), '1001': ( 3, -1), '1100': ( 1, -3), '1101': ( 1, -1),
        '1010': ( 3,  3), '1011': ( 3,  1), '1110': ( 1,  3), '1111': ( 1,  1),
    }
    REVERSE_MAP = {valor: chave for chave, valor in QAM_16_MAP.items()}
    IDEAL_LEVELS = [-3, -1, 1, 3]

    for i in range(0, len(sinal_com_ruido), amostras_por_simbolo):
        chunk = sinal_com_ruido[i : i + amostras_por_simbolo]
        if len(chunk) < amostras_por_simbolo:
            break
        
        template_I = np.cos(2 * np.pi * FREEQUENCIA_PORTADORA * t)
        template_Q = -np.sin(2 * np.pi * FREEQUENCIA_PORTADORA * t) 
        
        valor_I_bruto = np.sum(chunk * template_I)
        valor_Q_bruto = np.sum(chunk * template_Q)
        
        energia_referencia = np.sum(template_I ** 2) 
        
        # O valor normalizado aqui sai pequeno (ex: 0.94) por causa da redução na transmissão
        valor_I_norm = valor_I_bruto / energia_referencia
        valor_Q_norm = valor_Q_bruto / energia_referencia
        
        # --- DESNORMALIZAÇÃO PARA DECISÃO ---
        # Multiplicamos por sqrt(10) para trazer de volta à escala de inteiros (-3, -1, 1, 3)
        valor_I_escala_inteira = valor_I_norm * NORM_QAM
        valor_Q_escala_inteira = valor_Q_norm * NORM_QAM
        
        I_final = achar_valor(valor_I_escala_inteira, IDEAL_LEVELS)
        Q_final = achar_valor(valor_Q_escala_inteira, IDEAL_LEVELS)
        
        chave_encontrada = (I_final, Q_final)
        bits_string = REVERSE_MAP.get(chave_encontrada, '0000') 
        bits_simbolo = [int(b) for b in bits_string]
        bits.extend(bits_simbolo)

    return np.array(bits)

def achar_valor(valor, levels):
    match = None
    diff_minima = float('inf')
    for level in levels:
        diff = abs(valor - level)
        if diff < diff_minima:
            diff_minima = diff
            match = level
    return match
