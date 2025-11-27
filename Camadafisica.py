import numpy as np
import matplotlib.pyplot as plt

V_POSITIVO = 1.0  
V_NEGATIVO = -1.0 
V_ZERO = 0.0      


#---- Ruido Gaussiano -----
def add_ruido(bits, sigma):
    ruido = np.random.normal(0, sigma, bits.shape)
    sinal = bits + ruido
    return sinal

#---- NRZ-POLAR -----
def code_nrz_polar(bits):
    sinal = []
    # Cria os pulsos com duração de N amostras
    pulso_positivo = np.ones(AMOSTRAS_POR_BIT) * V_POSITIVO
    pulso_negativo = np.ones(AMOSTRAS_POR_BIT) * V_NEGATIVO
    
    for b in bits:
        if b == 1:
            sinal.extend(pulso_positivo)
        else:
            sinal.extend(pulso_negativo)
    return np.array(sinal)

# ---- MANCHESTER (Atualizado) ----
def code_manchester(bits):
    sinal = []
    meio = AMOSTRAS_POR_BIT // 2
    
    # Define as metades do pulso
    # Bit 1: Baixo -> Alto (-V, +V)
    # Bit 0: Alto -> Baixo (+V, -V)
    p_alto = np.ones(meio) * V_POSITIVO
    p_baixo = np.ones(meio) * V_NEGATIVO
    
    for b in bits:
        if b == 1:
            sinal.extend(p_baixo) # Começa negativo
            sinal.extend(p_alto)  # Termina positivo
        else:
            sinal.extend(p_alto)  # Começa positivo
            sinal.extend(p_baixo) # Termina negativo
    return np.array(sinal)

# ---- BIPOLAR / AMI (Atualizado) ----
def code_bipolar(bits):
    sinal = []
    counter = V_NEGATIVO
    
    pulso_zero = np.zeros(AMOSTRAS_POR_BIT)
    
    for b in bits:
        if b == 1:
            if counter == V_NEGATIVO:
                sinal.extend(np.ones(AMOSTRAS_POR_BIT) * V_POSITIVO)
                counter = V_POSITIVO
            else:
                sinal.extend(np.ones(AMOSTRAS_POR_BIT) * V_NEGATIVO)
                counter = V_NEGATIVO
        else:
            sinal.extend(pulso_zero)
    return np.array(sinal)
#----- MODULACAO POR PORTADORA -----

BIT_RATE = 1000 
TEMPO_BIT = 1/BIT_RATE
FREEQUENCIA_PORTADORA = 10000 
TAXA_DE_AMOSTRAGEM = 10 * FREEQUENCIA_PORTADORA 
AMOSTRAS_POR_BIT = int(TAXA_DE_AMOSTRAGEM / BIT_RATE)

def ask_modulate(bits):
    sinal = []
    t = np.linspace(0, TEMPO_BIT, AMOSTRAS_POR_BIT)
    for i in bits:
        if i == 0:
            sinal_bit = np.zeros(AMOSTRAS_POR_BIT) 
        else:
            sinal_bit = 1.0 * np.sin(2*np.pi*FREEQUENCIA_PORTADORA*t)
        sinal.extend(sinal_bit)
    return np.array(sinal)

def fsk_modulate(bits):
    sinal = []
    frequencia_desvio = 5000
    t = np.linspace(0, TEMPO_BIT, AMOSTRAS_POR_BIT)
    
    for i in bits:
        if i == 1:
            sinal_bit = 1.0 * np.sin(2*np.pi*(FREEQUENCIA_PORTADORA + frequencia_desvio) * t)    
        else:
            sinal_bit = 1.0 * np.sin(2*np.pi*(FREEQUENCIA_PORTADORA - frequencia_desvio) * t)
        sinal.extend(sinal_bit)
    return np.array(sinal)

def psk_modulate(bits):
    sinal = []
    tempo_simbolo = 2 * TEMPO_BIT
    t = np.linspace(0, tempo_simbolo, 2 * AMOSTRAS_POR_BIT)
    fases = {'00': 0 , '01': 90 , '11': 180 , '10': 270}

    for i in range(0, len(bits), 2):
        bit1 = str(bits[i])
        bit2 = str(bits[i+1])
        bit_concat = bit1 + bit2

        fase = fases[bit_concat]
        fase_rad = np.deg2rad(fase)

        sinal_bit = 1.0 * np.sin(2*np.pi*FREEQUENCIA_PORTADORA*t + fase_rad)
        sinal.extend(sinal_bit)

    return np.array(sinal)

# --- 16-QAM NORMALIZADO ---

# Fator de normalização para o 16-QAM ter a mesma energia média do QPSK
# QPSK amplitude 1 -> Energia 1. QAM níveis 1,3 -> Energia média 10.
# Fator de escala = sqrt(10)
NORM_QAM = np.sqrt(10) 

def qam_16(bits):
    sinal = []
    tempo_simbolo = 4 * TEMPO_BIT
    t = np.linspace(0, tempo_simbolo, 4 * AMOSTRAS_POR_BIT)
    
    QAM_16_MAP = {
    '0000': (-3, -3), '0001': (-3, -1), '0011': (-3,  1), '0010': (-3,  3),
    '0100': (-1, -3), '0101': (-1, -1), '0111': (-1,  1), '0110': (-1,  3),
    '1100': ( 1, -3), '1101': ( 1, -1), '1111': ( 1,  1), '1110': ( 1,  3),
    '1000': ( 3, -3), '1001': ( 3, -1), '1011': ( 3,  1), '1010': ( 3,  3),
    }

    for i in range(0, len(bits), 4):
        bit_concat = "".join(map(str, bits[i:i+4]))
        
        a = QAM_16_MAP[bit_concat][0]
        b = QAM_16_MAP[bit_concat][1]
        
        # --- NORMALIZAÇÃO AQUI ---
        # Dividi-se por sqrt(10) para que a energia média seja igual à do QPSK
        # Implementação inicial estava com valores de amplitude até 3,o que nao condiz com os outros modelos
        # Normalização resolve isso sem alterar implementação
        onda_I = (a / NORM_QAM) * np.cos(2 * np.pi * FREEQUENCIA_PORTADORA * t)
        onda_Q = (b / NORM_QAM) * np.sin(2 * np.pi * FREEQUENCIA_PORTADORA * t)
        
        onda_simbolo = onda_I - onda_Q
        sinal.extend(onda_simbolo)

    return np.array(sinal)

