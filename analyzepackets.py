import socket
import datetime
from tabulate import tabulate
import numpy as np
from matplotlib import pyplot as plt

# Dict convertendo a porta de destino para a string
# que descreve o protocolo de aplicação
port_protocol_map = {
    21: 'FTP',
    23: 'TELNET',
    25: 'SMTP',
    53: 'DNS',
    80: 'HTTP',
    110: 'POP3',
    143: 'IMAP',
    443: 'HTTPS'
}

# Criando socket RAW, capaz de receber todos os pacotes
# é necessário executar o script com permissões de Administrador.
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
# Realizando o bind do socket RAW ao host
# Sockets RAW não precisam ser bindados a uma porta específica.
HOST = socket.gethostbyname(socket.gethostname())
s.bind((HOST, 0))
# Definindo opções do socket para incluir o cabeçalho IP
# (IP_HDRINCL)
# e receber todos os pacotes (SIO_RCVALL -> RCVALL_ON)
s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
# Criando arquivo res.txt contendo os dados de cada pacote
file_txt = open('res.txt', 'w+')
# Número de segundos que o script será executado
n_sec = 60
# Momento inicial
t1 = datetime.datetime.now()
# Momento final
t2 = datetime.datetime.now() + datetime.timedelta(seconds=n_sec)
# Array para cada segundo
t = np.arange(0, n_sec + 1)
# Quantidade de pacotes para cada protocolo de aplicação
# para cada segundo.
hist = np.zeros((n_sec + 1, len(port_protocol_map)))
# Capturando pacotes enquanto o script não é interrompido
try:
    while datetime.datetime.now() < t2:
        raw_packet, _ = s.recvfrom(65565)
        # Momento em que o pacote foi capturado
        captured_at = datetime.datetime.now()
        second = int((captured_at - t1).total_seconds())
        # Primeiro byte do pacote contém a versão do protocolo
        # assim como o tamanho do cabeçalho IP.
        # A versão está localizada nos 4 bits mais significativos
        # logo é necessário deslocar os mesmos 4 bits para a esquerda.
        version = raw_packet[0] >> 4
        # O cabeçalho IP está localizado nos 4 bits menos significativos
        # logo é necessário aplicar AND com 0b1111 para obter apenas os 4 bits.
        ip_header_length = raw_packet[0] & 0b1111
        # O valor ip_header_length indica a quantidade de blocos de 32 bits
        # que compõe o cabeçalho IP. Para obter o tamanho do cabeçalho em bytes
        # é necessário multiplicar o valor de ip_header_length por 4.
        ip_header_length *= 4
        # Protocolo de transporte está localizado no byte 9.
        transport_protocol = raw_packet[9]
        # IP de origem está localizado no bytes 12, 13, 14 e 15.
        # O método socket.inet_ntoa() converte o IP em uma string.
        source_ip = socket.inet_ntoa(raw_packet[12:16])
        # IP de destino está localizado no bytes 16, 17, 18 e 19.
        dest_ip = socket.inet_ntoa(raw_packet[16:20])

        # Se o protocolo possui número 6, então é um pacote TCP.
        if transport_protocol == 6:
            transport_protocol_str = 'TCP'
            # Tamanho do cabeçalho TCP está localizado nos 4 bits
            # mais significativos do byte 12. É contar a partir
            # do fim do cabeçalho IP.
            tcp_header_length = raw_packet[ip_header_length + 12] >> 4
            # Deve ser multiplicado por 4 da mesma forma que o cabeçalho IP
            tcp_header_length *= 4
            # Dados do pacote estão localizados a partir do fim do cabeçalho TCP.
            raw_data = raw_packet[ip_header_length + tcp_header_length:]

        # Se o protocolo possui número 17, então é um pacote UDP.
        elif transport_protocol == 17:
            transport_protocol_str = 'UDP'
            # Tamanho do cabeçalho UDP é sempre 8 bytes.
            raw_data = raw_packet[ip_header_length + 8:]
        # Se o protocolo não é TCP nem UDP, então é um protocolo desconhecido.
        # e é ignorado.
        else:
            continue

        # Independentemente do protocolo de transporte, as portas de origem
        # e destino estão localizadas nos 4 primeiros bytes dos seus
        # respectivos cabeçalhos. Esses cabeçalhos têm início logo após o
        # o cabeçalho IP. Logo basta utilizar o valor de ip_header_length
        # para obter o início dos cabeçalhos TCP e UDP.
        # O valor em bytes é decodificado utilizando o método
        # int.from_bytes(), sabendo que a ordem dos bytes é big endian.
        source_port = int.from_bytes(
            raw_packet[ip_header_length:ip_header_length+2], 'big')
        dest_port = int.from_bytes(
            raw_packet[ip_header_length+2:ip_header_length+4], 'big')

        # Se o protocolo de aplicação é conhecido
        # (a partir da porta de destino)
        # incrementar o número de pacotes recebidos desse protocolo
        # no histograma.
        if dest_port in port_protocol_map:
            index_of_protocol = list(port_protocol_map.keys()).index(dest_port)
            hist[second, index_of_protocol] += 1     

        # Salvando no arquivo res.txt e mostrando no console
        # Utilizando tabulate para mostrar as informações do cabeçalho
        table = tabulate([[
            f'{source_ip}:{source_port}',
            f'{dest_ip}:{dest_port}',
            f'{captured_at}',
            f'{transport_protocol_str}',
            f'{port_protocol_map.get(dest_port, "Unknown")}'
        ]], headers=[
            'Source IP:Port',
            'Destination IP:Port',
            'Captured At',
            'Transport Protocol',
            'Application Protocol'
        ])
        print('\n' + table)
        file_txt.write('\n' + table)

        # Tentando decodificar os dados utilizando ASCII.
        # Caso não consiga, é mostrado o valor bruto.
        try:
            data = raw_data.decode('ascii')
            print('\n' + data)
            file_txt.write('\n' + data)
        except:
            print('\n' + str(raw_data))
            file_txt.write('\n' + str(raw_data))
except KeyboardInterrupt:
    pass

file_txt.close()
# Ignorando quantidade de pacotes igual a 0.
plt.plot(t, np.ma.masked_where(hist == 0, hist), '.-')
plt.legend(port_protocol_map.values())
plt.xlabel = 'Time (s)'
plt.ylabel = 'Quantidade de pacotes'
plt.title = 'Histograma de pacotes recebidos'
plt.show()