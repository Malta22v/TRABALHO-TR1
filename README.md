# Simulador de Camada de Enlace - Teleinformática e Redes 1

Este repositório contém a implementação do trabalho final da disciplina de Teleinformática e Redes 1 (UnB), focado na simulação dos protocolos da **Camada de Enlace** e **Camada Física**.

O objetivo é simular o fluxo de transmissão e recepção de dados, abordando técnicas de enquadramento, detecção e correção de erros.

## Integrantes do Grupo
* Victor Rodrigues Malta - 222014124
* Marcus Emanuel Carvalho Tenedini de Freitas - 222025960
* Moises de Araújo Altounian - 200069306

## Funcionalidades Implementadas

### Camada de Enlace
O projeto implementa os seguintes algoritmos sem o uso de bibliotecas prontas para a lógica de protocolos:

* **Enquadramento (Framing):**
    -  Contagem de Caracteres
    -  Inserção de Bytes (Byte Stuffing)
    -  Inserção de Bits (Bit Stuffing)

* **Detecção de Erros:**
    -  Bit de Paridade Par
    -  CRC-32 (IEEE 802) - Implementação manual via divisão polinomial

* **Correção de Erros:**
    -  Código de Hamming (7,4)

## Pré-requisitos

O projeto foi desenvolvido em **Python 3**. A única dependência externa utilizada é para manipulação de arrays de bits.

Para instalar a dependência, execute:

```bash
pip install bitarray
