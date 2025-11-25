# Simulador de Camada Física e Enlace - Teleinformática e Redes 1

Este repositório contém a implementação do trabalho final da disciplina de Teleinformática e Redes 1 (UnB). O projeto consiste em um simulador completo de transmissão e recepção de dados, englobando desde a **Camada de Enlace** até a **Camada Física**, com visualização gráfica dos sinais.

## Integrantes do Grupo
* Victor Rodrigues Malta - 222014124
* Marcus Emanuel Carvalho Tenedini de Freitas - 222025960
* Moises de Araújo Altounian - 200069306

## Funcionalidades Implementadas

O simulador cobre as seguintes etapas de processamento de dados e sinais:

### 1. Camada de Enlace (Data Link Layer)
* **Enquadramento:** Contagem de Caracteres, Inserção de Bytes (Byte Stuffing) e Inserção de Bits (Bit Stuffing).
* **Detecção de Erros:** Bit de Paridade Par, Checksum e CRC-32 (IEEE 802).
* **Correção de Erros:** Código de Hamming.

### 2. Camada Física (Physical Layer)
* **Modulação Digital (Banda Base):**
    - NRZ-Polar
    - Manchester
    - Bipolar
* **Modulação por Portadora:**
    - ASK (Amplitude Shift Keying)
    - FSK (Frequency Shift Keying)
    - PSK/QPSK (Phase Shift Keying)
    - 16-QAM (Quadrature Amplitude Modulation)

### 3. Canal e Interface
* **Simulação de Canal:** Adição de ruído branco gaussiano (AWGN) ao sinal transmitido.
* **Interface Gráfica (GUI):** Configuração dos parâmetros de simulação e visualização gráfica dos sinais (transmitido vs. recebido) e constelações.

## Pré-requisitos

* **Linguagem:** Python 3
* **Dependências:**
    * `bitarray` (Manipulação de bits)

Para instalar a dependência principal:
```bash
pip install bitarray
