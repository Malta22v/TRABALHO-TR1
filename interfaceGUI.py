# GUI em GTK3 para o simulador de Camada Física e Enlace
# Requisitos: python3, python3-gi, matplotlib, bitarray, numpy

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

# Importações das bibliotecas utilizadas para plotar os gráficos
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
import numpy as np
import threading
import time

# Importação dos módulos do trabalho
import Camadafisica as fisica
import decode_Camadafisica as d_fisica
import CamadaEnlace as enlace
import decode_CamadaEnlace as d_enlace
import Transmissor as tm
import Receptor as rc

# ---------------------------------------------------------------------------------------------------------------------------
# RESPONSABILIDADES
# Construir layout UI, conectar callbacks dos botões, executar simulação em thread, desenhar gráficos e imprimir log de saída
# ---------------------------------------------------------------------------------------------------------------------------

class MainWindow(Gtk.Window):

    def __init__(self):

        super().__init__(title="Simulador de Telecomunicações - Os 3 Patetas") # Inicialização da janela GTK
        self.set_border_width(15)       # Tamanho da borda
        self.maximize()                 # Fullscreen mantendo barra de tarefas e ícone para fechar GTK
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12) # Espaçamento entre as colunas esquerda e direita
        self.add(self.main_box)

        # COLUNA ESQUERDA - Paramêtros (em cima) / Saída (em baixo)
        self.left_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25) # Espaçamento da caixa de cima pra de baixo
        self.left_column.set_size_request(420, -1) # Largura da coluna esquerda

        # PARÂMETROS
        params_frame = Gtk.Frame(label="Parâmetros")
        params_frame.set_label_align(0.5, 0.5) # Título centralizado
        params_frame.set_hexpand(False)
        params_frame.set_vexpand(False)
        self.params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        params_frame.add(self.params_box) # Adiciona caixa ao frame
        self.params_grid = Gtk.Grid(column_spacing=8, row_spacing=8, margin=10) # Distâncias dos campos de PARÂMETROS
        self.params_box.pack_start(self.params_grid, False, False, 0)

        # Cria as seções de parâmetros
        self._create_input_section()
        self._create_digital_section()
        self._create_analog_section()
        self._create_framing_section()
        self._create_noise_section()
        self._create_buttons()

        # SAÍDA (LOG)
        output_frame = Gtk.Frame(label="Saída (Log)")
        output_frame.set_label_align(0.5, 0.5) # Título centralizado
        output_frame.set_hexpand(False)
        output_frame.set_vexpand(True) # Ocupa espaço vertical restante
        self._create_output_text(parent=output_frame)

        # Adiciona os frames à coluna
        self.left_column.pack_start(params_frame, False, False, 0) # Recebe params, não cresce
        self.left_column.pack_start(output_frame, True, True, 0)   # Recebe output, cresce pra ocupar espaço que sobra e o ocupa todo

        # GRÁFICOS
        self.right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        frame_graphs = Gtk.Frame(label="Gráficos")
        frame_graphs.set_label_align(0.5, 0.5) # Título centralizado
        frame_graphs.set_hexpand(True) # Ocupa espaço horizontal restante
        frame_graphs.set_vexpand(True) # Ocupa espaço vertical restante
        self.graph_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame_graphs.add(self.graph_box)
        self.right_box.pack_start(frame_graphs, True, True, 0)    # Recebe frame graphs, cresce pra ocupar espaço que sobra e o ocupa todo

        # ADIÇÃO NA MAIN
        self.main_box.pack_start(self.left_column, False, False, 0) # Adiciona coluna esquerda
        self.main_box.pack_start(self.right_box, True, True, 0)     # Adiciona coluna direita e permite expansão

    # --------------------------------------------------
    # CRIAÇÃO DE WIDGETS
    # --------------------------------------------------

    def _create_input_section(self):
        lbl = Gtk.Label(label="Mensagem de entrada:")
        lbl.set_halign(Gtk.Align.START)
        self.params_grid.attach(lbl, 0, 0, 1, 1)

        self.input_entry = Gtk.Entry()
        self.input_entry.set_text("")
        self.params_grid.attach(self.input_entry, 1, 0, 2, 1)

    # MODULAÇÃO - DIGITAL
    def _create_digital_section(self):

        lbl = Gtk.Label(label="Modulação - Digital:")
        lbl.set_halign(Gtk.Align.START)
        self.params_grid.attach(lbl, 0, 1, 1, 1)

        self.digital_combo = Gtk.ComboBoxText()
        self.digital_combo.append_text("NRZ-Polar")
        self.digital_combo.append_text("Manchester")
        self.digital_combo.append_text("Bipolar")
        self.digital_combo.set_active(0)
        self.params_grid.attach(self.digital_combo, 1, 1, 2, 1)

    # MODULAÇÃO - PORTADORA
    def _create_analog_section(self):
        lbl = Gtk.Label(label="Modulação - Portadora:")
        lbl.set_halign(Gtk.Align.START)
        self.params_grid.attach(lbl, 0, 2, 1, 1)

        self.analog_combo = Gtk.ComboBoxText()
        self.analog_combo.append_text("Nenhum")
        self.analog_combo.append_text("ASK")
        self.analog_combo.append_text("FSK")
        self.analog_combo.append_text("PSK (QPSK)")
        self.analog_combo.append_text("16-QAM")
        self.analog_combo.set_active(0)
        self.params_grid.attach(self.analog_combo, 1, 2, 2, 1)

    # ENQUADRAMENTO E DETECÇÃO/CORREÇÃO DE ERROS
    def _create_framing_section(self):
        
        # ENQUADRAMENTO
        lbl = Gtk.Label(label="Enquadramento:")
        lbl.set_halign(Gtk.Align.START)
        self.params_grid.attach(lbl, 0, 3, 1, 1)

        self.framing_combo = Gtk.ComboBoxText()
        self.framing_combo.append_text("Nenhum")
        self.framing_combo.append_text("Contagem de caracteres")
        self.framing_combo.append_text("FLAG + Inserção de bytes")
        self.framing_combo.append_text("FLAG + Inserção de bits")
        self.framing_combo.set_active(0)
        self.params_grid.attach(self.framing_combo, 1, 3, 2, 1)

        # DETECÇÃO / CORREÇÃO DE ERROS
        lbl2 = Gtk.Label(label="Detecção / Correção:")
        lbl2.set_halign(Gtk.Align.START)
        self.params_grid.attach(lbl2, 0, 4, 1, 1)

        self.error_combo = Gtk.ComboBoxText()
        self.error_combo.append_text("Nenhum")
        self.error_combo.append_text("Bit de paridade")
        self.error_combo.append_text("CRC-32")
        self.error_combo.append_text("Hamming")
        self.error_combo.set_active(0)
        self.params_grid.attach(self.error_combo, 1, 4, 2, 1)

    # SIGMA DO RUÍDO E CHECKBOX DEMODULAÇÃO / DECODIFICAÇÃO
    def _create_noise_section(self):

        # SIGMA DO RUÍDO
        lbl = Gtk.Label(label="Sigma do ruído (AWGN):")
        lbl.set_halign(Gtk.Align.START)
        self.params_grid.attach(lbl, 0, 5, 1, 1)

        self.noise_adjustment = Gtk.Adjustment(value=0.0, lower=0.0, upper=5.0, step_increment=0.005) # limites e passos do ruído
        self.noise_spin = Gtk.SpinButton(adjustment=self.noise_adjustment, digits=3) # casas decimais permitidas
        self.params_grid.attach(self.noise_spin, 1, 5, 1, 1)

        # CHECKBOX DEMODULAÇÃO / DECODIFICAÇÃO
        self.show_decoding_check = Gtk.CheckButton(label="Executar demodulação/decodificação (RX)")
        # Ruído com distribuição gaussiana (normal) aleatória
        self.show_decoding_check.set_active(True)
        self.params_grid.attach(self.show_decoding_check, 1, 6, 2, 1)

    def _create_buttons(self):
    
        # EXECUTAR SIMULAÇÃO
        self.run_button = Gtk.Button(label="Executar Simulação")
        self.run_button.connect("clicked", self.on_run_clicked)
        self.params_grid.attach(self.run_button, 0, 7, 3, 1)


    def _create_output_text(self, parent=None):

        # ÁREA DE TEXTO - SAÍDA (LOG)
        sw = Gtk.ScrolledWindow()
        sw.set_hexpand(True)
        sw.set_vexpand(True)
        self.output_text = Gtk.TextView()
        self.output_text.set_editable(False)
        self.output_text.set_wrap_mode(Gtk.WrapMode.WORD)
        sw.add(self.output_text)
        if parent is None:
            self.grid.attach(sw, 0, 10, 3, 10)
        else:
            parent.add(sw)

    # --------------------------------------------------
    # UTILITÁRIOS
    # --------------------------------------------------
    def log(self, txt):

        # Adiciona um espaço a cada linha do log
        buf = self.output_text.get_buffer()
        end = buf.get_end_iter()
        buf.insert(end, txt + "\n\n")

    def on_run_clicked(self, widget):
        # Inicia a simulação em thread separada para não bloquear a UI.
        # Criamos a thread e o método run simulation faz o resto
        t = threading.Thread(target=self.run_simulation, daemon=True)
        t.start()

    def run_simulation(self):
        # Fluxo principal da simulação.

        # PASSO 1: LIMPA SAÍDA E GRÁFICOS ATUAIS
        GObject.idle_add(self._clear_output)
        GObject.idle_add(self._clear_graphs) 

        # PASSO 2: Leitura dos parâmetros na UI
        message = self.input_entry.get_text()
        digital_mod = self.digital_combo.get_active_text()
        analog_mod = self.analog_combo.get_active_text()
        framing_method = self.framing_combo.get_active_text()
        error_method = self.error_combo.get_active_text()
        sigma = float(self.noise_spin.get_value())
        do_decode = self.show_decoding_check.get_active()

        # Verifica se a camada de enlace e camada física foram carregadas
        if enlace is None or fisica is None:
            GObject.idle_add(self.log, "Erro: Camada de Enlace ou Camada Fisica não foram encontradas.")
            return

        # PASSO 3: CONVERSÃO PARA BITS (Camada de enlace)
        try:
            binary_sequence = enlace.convert_to_bytes(message)
        except Exception as e:
            GObject.idle_add(self.log, f"Erro convert_to_bytes: {e}")
            return

        GObject.idle_add(self.log, f"Mensagem original: {message}")
        GObject.idle_add(self.log, f"Sequência binária original (len = {len(binary_sequence)}): {binary_sequence}")

        # PASSO 4: APLICA ENQUADRAMENTO ESCOLHIDO
        framed = binary_sequence
        try:
            if framing_method == "Contagem de caracteres":
                framed = enlace.character_count(binary_sequence)
            elif framing_method == "FLAG + Inserção de bytes":
                framed = enlace.byte_insertion(binary_sequence)
            elif framing_method == "FLAG + Inserção de bits":
                framed = enlace.bit_insertion(binary_sequence)
        except Exception as e:
            GObject.idle_add(self.log, f"Erro no enquadramento: {e}")
            return

        GObject.idle_add(self.log, f"Sequência com enquadramento (len = {len(framed)}): {framed}")

        # PASSO 5: APLICA DETECÇÃO/CORREÇÃO DE ERROS ANTES DE ENVIAR
        processed = framed
        try:
            if error_method == "Bit de paridade":
                processed = enlace.bit_parity(framed)
            elif error_method == "CRC-32":
                processed = enlace.prepara_CRC_para_transmissao(framed)
            elif error_method == "Hamming":
                processed = enlace.hamming_dinamico(framed)
        except Exception as e:
            GObject.idle_add(self.log, f"Erro na codificação de erro: {e}")
            return

        GObject.idle_add(self.log, f"Sequência enviada ao meio (len = {len(processed)}): {processed}")

        # PASSO 6: TRANSMISSÃO LOCAL VIA SOCKET
        # Verifica se transmissor e receptor existem. Senão existirem, código copia os bits
        if tm is None or rc is None:
            GObject.idle_add(self.log, "Aviso: transmissor/Receptor locais não encontrados. O fluxo continuará localmente sem sockets.")
            received_bits = processed.copy()
        else:
            # Inicia receptor em thread
            receiver = rc.Receiver()
            receiver_thread = threading.Thread(target=receiver.TCPServer, daemon=True)
            receiver_thread.start()
            time.sleep(0.3)

            ok = tm.startServer(processed)
            if not ok:
                GObject.idle_add(self.log, "Erro ao transmitir via socket")
                return

            # Aguarda chegada dos dados
            receiver.data_ready.wait(timeout=5)
            received_bits = receiver.sent_data if getattr(receiver, 'sent_data', None) is not None else processed
            GObject.idle_add(self.log, f"Sequência recebida (len = {len(received_bits)}): {received_bits}")
            if hasattr(receiver, 'changed_bit_position'):
                GObject.idle_add(self.log, f"Posição do bit alterado (se houver): {receiver.changed_bit_position}")

        # PASSO 7: VERIFICAÇÃO E CORREÇÃO DE ERROS NO RECEPTOR
        error_report = "Não verificado"
        corrected = received_bits
        try:
            if error_method == "Bit de paridade":
                error_report, corrected = d_enlace.verifica_bit_parity(received_bits)
            elif error_method == "CRC-32":
                error_report, corrected = d_enlace.verifica_crc(received_bits)
            elif error_method == "Hamming":
                corrected = d_enlace.corr_hamming_dinamico(framing_method, received_bits)
                error_report = "Hamming aplicado"
        except Exception as e:
            GObject.idle_add(self.log, f"Erro na verificação de erros: {e}")

        GObject.idle_add(self.log, f"Relatório de erro: {error_report}")
        GObject.idle_add(self.log, f"Sequência após verificação/correção (len = {len(corrected)}): {corrected}")

        # PASSO 8: DESENQUADRAMENTO E OBTENÇÃO DO TEXTO DECODIFICADO
        decoded_text = ""
        try:
            # 1) funções de desenquadramento específicas (se existirem)
            if framing_method == "Contagem de caracteres" and hasattr(d_enlace, 'decode_charactere_count'):
                decoded_text = d_enlace.decode_charactere_count(corrected)
            elif framing_method == "FLAG + Inserção de bytes" and hasattr(d_enlace, 'decode_byte_insertion'):
                decoded_text = d_enlace.decode_byte_insertion(corrected)
            elif framing_method == "FLAG + Inserção de bits" and hasattr(d_enlace, 'decode_bit_insertion'):
                decoded_text = d_enlace.decode_bit_insertion(corrected)
            else:
                # 2) tenta funções genéricas do módulo enlace (nomes comuns)
                tried = False
                for fn_name in ('convert_from_bytes', 'bytes_to_string', 'convert_bytes_to_message', 'bits_to_bytes'):
                    if hasattr(enlace, fn_name):
                        try:
                            result = getattr(enlace, fn_name)(corrected)
                            # se a função retornar bytes, transforma em string
                            if isinstance(result, (bytes, bytearray)):
                                decoded_text = result.decode('utf-8', errors='replace')
                            else:
                                decoded_text = str(result)
                            tried = True
                            break
                        except Exception:
                            # continua para o próximo nome possível
                            pass

                # 3) fallback manual: trata corrected como bitarray / bytes / lista de bits
                if not tried:
                    try:
                        from bitarray import bitarray as _bitarray
                        if isinstance(corrected, _bitarray):
                            b = corrected.tobytes()
                            decoded_text = b.decode('utf-8', errors='replace')
                        elif isinstance(corrected, (bytes, bytearray)):
                            decoded_text = bytes(corrected).decode('utf-8', errors='replace')
                        elif isinstance(corrected, (list, tuple)):
                            # agrupa bits em octetos (descarta o último octeto incompleto)
                            bits = ''.join('1' if int(x) else '0' for x in corrected)
                            octets = [bits[i:i+8] for i in range(0, len(bits), 8)]
                            byts = bytes(int(o, 2) for o in octets if len(o) == 8)
                            decoded_text = byts.decode('utf-8', errors='replace')
                        else:
                            # última tentativa genérica
                            decoded_text = str(corrected)
                    except Exception as e:
                        GObject.idle_add(self.log, f"Erro no desenquadramento/manual decode: {e}")

        except Exception as e:
            GObject.idle_add(self.log, f"Erro no desenquadramento: {e}")

        # Se ainda estiver vazio, mostra um aviso (mas mostra sempre alguma coisa)
        if isinstance(decoded_text, (bytes, bytearray)):
            decoded_text = decoded_text.decode('utf-8', errors='replace')
        if not decoded_text:
            decoded_text = "<(não foi possível decodificar o texto)>"

        GObject.idle_add(self.log, f"Mensagem decodificada: {decoded_text}")

        # PASSO 9: GERA E PLOTA SINAIS DIGITAIS
        try:
            signal = None
            if digital_mod == "NRZ-Polar":
                if hasattr(fisica, 'code_nrz_polar'):
                    signal = fisica.code_nrz_polar(processed)
                elif hasattr(fisica, 'nrz_modulation'):
                    signal = fisica.nrz_modulation(processed)

            elif digital_mod == "Manchester":
                if hasattr(fisica, 'code_manchester'):
                    signal = fisica.code_manchester(processed)
                elif hasattr(fisica, 'manchester_modulation'):
                    signal = fisica.manchester_modulation(processed)

            elif digital_mod == "Bipolar":
                if hasattr(fisica, 'code_bipolar'):
                    signal = fisica.code_bipolar(processed)
                elif hasattr(fisica, 'bipolar_modulation'):
                    signal = fisica.bipolar_modulation(processed)

            if signal is not None:
                # Adiciona gráfico do sinal digital
                GObject.idle_add(self.plot_digital_signal, signal, digital_mod)

                # Aplicação de ruído e demodulação (se necessário)
                if do_decode and sigma > 0 and d_fisica is not None:
                    noisy = fisica.add_ruido(signal, sigma)
                    # tentar demodular com as funções de decode_Camadafisica
                    if digital_mod == "NRZ-Polar" and hasattr(d_fisica, 'decode_nrz_polar'):
                        bits_rx = d_fisica.decode_nrz_polar(noisy)
                        GObject.idle_add(self.log, f"Bits demodulados (NRZ): {bits_rx}")
                    elif digital_mod == "Manchester" and hasattr(d_fisica, 'decode_manchester'):
                        bits_rx = d_fisica.decode_manchester(noisy)
                        GObject.idle_add(self.log, f"Bits demodulados (Manchester): {bits_rx}")
                    elif digital_mod == "Bipolar" and hasattr(d_fisica, 'decode_bipolar'):
                        bits_rx = d_fisica.decode_bipolar(noisy)
                        GObject.idle_add(self.log, f"Bits demodulados (Bipolar): {bits_rx}")

        except Exception as e:
            GObject.idle_add(self.log, f"Erro ao gerar/plotar sinal digital: {e}")

        # PASSO 10: GERA E PLOTA SINAIS ANALÓGICOS
        try:
            analog_signal = None
            if analog_mod == "ASK" and hasattr(fisica, 'ask_modulate'):
                analog_signal = fisica.ask_modulate(processed)
            elif analog_mod == "FSK" and hasattr(fisica, 'fsk_modulate'):
                analog_signal = fisica.fsk_modulate(processed)
            elif analog_mod == "PSK (QPSK)" and hasattr(fisica, 'psk_modulate'):
                analog_signal = fisica.psk_modulate(processed)
            elif analog_mod == "16-QAM" and hasattr(fisica, 'qam_16'):
                analog_signal = fisica.qam_16(processed)

            if analog_signal is not None:
                # Adiciona ruído (se necessário)
                if sigma > 0 and hasattr(fisica, 'add_ruido'):
                    analog_signal = fisica.add_ruido(analog_signal, sigma)

                GObject.idle_add(self.plot_analog_signal, analog_signal, analog_mod)

                # Demodulação (se necessária)
                if do_decode and d_fisica is not None:
                    if analog_mod == "ASK" and hasattr(d_fisica, 'decode_ask_modulate'):
                        bits_rx = d_fisica.decode_ask_modulate(analog_signal)
                        GObject.idle_add(self.log, f"Bits demodulados (ASK): {bits_rx}")
                    if analog_mod == "FSK" and hasattr(d_fisica, 'decode_fsk_modulate'):
                        bits_rx = d_fisica.decode_fsk_modulate(analog_signal)
                        GObject.idle_add(self.log, f"Bits demodulados (FSK): {bits_rx}")
                    if analog_mod == "PSK (QPSK)" and hasattr(d_fisica, 'demodulate_psk_modulate'):
                        bits_rx = d_fisica.demodulate_psk_modulate(analog_signal)
                        GObject.idle_add(self.log, f"Bits demodulados (PSK/QPSK): {bits_rx}")
                    if analog_mod == "16-QAM" and hasattr(d_fisica, 'demodulate_qam_16'):
                        bits_rx = d_fisica.demodulate_qam_16(analog_signal)
                        GObject.idle_add(self.log, f"Bits demodulados (16-QAM): {bits_rx}")

        except Exception as e:
            GObject.idle_add(self.log, f"Erro ao gerar/plotar sinal analógico: {e}")

        GObject.idle_add(self.log, "\n\nSimulação concluída com sucesso.")

    def _clear_graphs(self):

        # Limpa os gráficos
        for c in self.graph_box.get_children():
            self.graph_box.remove(c)

    def _clear_output(self):

        # Limpa o log da saída
        if getattr(self, 'output_text', None) is None: # Nada feito cas a saída não exista
            return
        buf = self.output_text.get_buffer()
        buf.set_text("")

    def plot_digital_signal(self, signal, title):

        # Desenha um gráfico do sinal digital (usando step para representar níveis).
        fig = plt.Figure(figsize=(9, 3), dpi=100)
        ax = fig.add_subplot(111)

        # Eixos
        x = np.arange(len(signal))
        ax.step(x, signal, where='mid')
        ax.set_title(f"Sinal digital: {title}")
        ax.set_xlabel("Amostras")
        ax.set_ylabel("Amplitude")

        # Mostrar
        canvas = FigureCanvas(fig)
        self.graph_box.pack_start(canvas, True, True, 0)
        canvas.show()

    def plot_analog_signal(self, signal, title):

        # Desenha um gráfico do sinal analógico (curva contínua).
        fig = plt.Figure(figsize=(9, 3), dpi=100)
        ax = fig.add_subplot(111)

        # Eixos
        x = np.arange(len(signal))
        ax.plot(x, signal)
        ax.set_title(f"Sinal modulado: {title}")
        ax.set_xlabel("Amostras")
        ax.set_ylabel("Amplitude")

        # Mostrar
        canvas = FigureCanvas(fig)
        self.graph_box.pack_start(canvas, True, True, 0)
        canvas.show()


def main():
    # Cria e mostra a janela principal
    win = MainWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
