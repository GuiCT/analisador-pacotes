from dataclasses import dataclass
import socket
import datetime

# Dataclass que armazena as informações de um pacote.


@dataclass(init=True)
class Packet:
    version: int
    source_ip: str
    dest_ip: str
    source_port: int
    dest_port: int
    transport_protocol: str
    application_protocol: str
    # Momento em que o pacote foi capturado.
    # útil para montar a linha do tempo posteriormente.
    captured_at: datetime.datetime
    # Dados do pacote, excluso os cabeçalhos.
    raw_data: bytes

    def print(self):
        print(f"{self.source_ip}:{self.source_port} -> {self.dest_ip}:{self.dest_port}")
        print(f"{self.transport_protocol} {self.application_protocol}")
        print(f"{self.captured_at}")
        print(f"{self.raw_data}")
        print("\n")


# Dict convertendo a porta de destino para a string
# que descreve o protocolo de aplicação
port_protocol_map = {
    21: 'FTP',
    22: 'SSH',
    23: 'TELNET',
    25: 'SMTP',
    53: 'DNS',
    67: 'DHCP',
    68: 'DHCP',
    80: 'HTTP',
    110: 'POP3',
    143: 'IMAP',
    443: 'HTTPS',

}

# Criando socket RAW, capaz de receber todos os pacotes
# é necessário executar o script com permissões de Administrador.
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
# Realizando o bind do socket RAW ao host
# Sockets RAW não precisam ser bindados a uma porta específica.
s.bind(('localhost', 0))
# Definindo opções do socket para incluir o cabeçalho IP
# (IP_HDRINCL)
# e receber todos os pacotes (SIO_RCVALL -> RCVALL_ON)
s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
# Lista contendo todos os pacotes capturados
packets = list()
# Capturando pacotes enquanto o script não é interrompido
try:
    while True:
        raw_packet, _ = s.recvfrom(65565)
        # Momento em que o pacote foi capturado
        captured_at = datetime.datetime.now()
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
        # Verificando se a porta de destino é de um protocolo de aplicação
        # desconhecido, se sim, o pacote será ignorado.
        if dest_port not in port_protocol_map:
            continue
        # Encapsulando os dados do pacote em um objeto Packet
        packet = Packet(
            version,
            source_ip,
            dest_ip,
            source_port,
            dest_port,
            transport_protocol_str,
            port_protocol_map.get(dest_port, 'UNKNOWN'),
            captured_at,
            raw_data
        )
        # Adicionando o pacote à lista de pacotes capturados
        packets.append(packet)
except KeyboardInterrupt:
    for packet in packets:
        packet.print()
