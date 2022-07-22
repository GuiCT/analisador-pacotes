from dataclasses import dataclass
import socket
import datetime

# Dataclass que armazena as informações de um pacote.
@dataclass
class Packet:
  source_ip, dest_ip : str
  source_port, dest_port : int
  transport_protocol : str
  application_protocol : str
  # Momento em que o pacote foi capturado.
  # útil para montar a linha do tempo posteriormente.
  captured_at : datetime.datetime


# Criando socket RAW, capaz de receber todos os pacotes
# é necessário executar o script com permissões de Administrador.
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
# Encontrando host a partir de socket.gethostbyname()
# O parâmetro é o nome do host dado por socket.gethostname()
HOST = socket.gethostbyname(socket.gethostname())
# Realizando o bind do socket RAW ao host
# Sockets RAW não precisam ser bindados a uma porta específica.
s.bind((HOST, 0))
# Lista contendo todos os pacotes capturados
packets = list()
# Capturando pacotes enquanto o script não é interrompido
try:
  while True:
    pass
except KeyboardInterrupt:
  pass