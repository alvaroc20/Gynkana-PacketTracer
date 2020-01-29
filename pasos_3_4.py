import socket
import operator, ast
import http.client
import time
import struct
import sys

binOps = {
ast.Add: operator.add,
ast.Sub: operator.sub,
ast.Mult: operator.mul,
ast.Div: operator.floordiv,
ast.Mod: operator.mod
}


def arithmeticEval(t):
    # La función arithmeticEval ha sido seleccionada de la siguiente URL:
    # http://stackoverflow.com/questions/20748202/valueerror-malformed-string-when-using-ast-literal-eval
    # Autor: poke

    node = ast.parse(t, mode='eval')

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Str):
            return node.t
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return binOps[type(node.op)](_eval(node.left), _eval(node.right))
        else:
            raise Exception('Unsupported type {}'.format(node))

    return _eval(node.body)

    #Esta función ha sido tomada de la siguiente URL:
    #https://bitbucket.org/arco_group/python-net/src/tip/raw/icmp_checksum.py?fileviewer=file-view-default

def checksum(source_string):

         countTo = (int(len(source_string)/2))*2
         sum = 0
         count = 0
       
        
         loByte = 0
         hiByte = 0
         while count < countTo:
             if (sys.byteorder == "little"): 
                 loByte = source_string[count]
                 hiByte = source_string[count + 1]
             else:
                 loByte = source_string[count + 1]
                 hiByte = source_string[count]
             sum = sum + (hiByte * 256 + loByte)
             count += 2
       
         
         if countTo < len(source_string): 
             loByte = source_string[len(source_string)-1]
             sum += loByte
       
         sum &= 0xffffffff 
       
         sum = (sum >> 16) + (sum & 0xffff)    
         sum += (sum >> 16)                    
         answer = ~sum & 0xffff              
         answer = socket.htons(answer)
       
         return answer    

#funcion que crea el socket TPC, se conecta al servidor de la gyncana de la ESI,
#recibe las instrucciones para la siguiente etapa y las devuelve para la siguiente funcion
def step_0TCP():
     ginkana = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     ginkana.connect(('atclab.esi.uclm.es', 2000))
     primer_mensaje = (ginkana.recv(1024)).decode('utf-8')
     ginkana.close()
     return (primer_mensaje)


#funcion que crea un socket UDP y se conecta con el codigo de la etapa anterior
#devuelve las instrucciones para la siguiente etapa
def step_1UDP():
     port_1 = 23456
     servidorUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
     servidorUDP.bind(('', port_1))
     UDP_iden = step_0TCP()[:5]
     mensaje = "{} {}".format(UDP_iden, port_1)
     servidorUDP.sendto(mensaje.encode('utf-8'), ('atclab.esi.uclm.es', 2000))
     segundo_mensaje = (servidorUDP.recv(1024)).decode('utf-8')
     servidorUDP.close()
     return (segundo_mensaje)

#etapa 2 donde se calculan todas las expresiones recibidas y se envia el resultado entre parentesis
#cuando se deje de recibir un abierto (parentesis, corchete o llave)
#es que se han terminado de recibir expresiones y se envian las instrucciones para la siguiente etapa
#para todo ello se utiliza conexion TCP

def step_2Arit():
    socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket2.connect(('atclab.esi.uclm.es', int(step_1UDP()[:5])))

    Infinito = True
    while Infinito:
        exparentizada = socket2.recv(1024).decode()
        if not exparentizada[0] in ('(', '[', '{'):
            socket2.close
            Infinito = False
        else:
            exparentizada = comprobarBalanceo(exparentizada, socket2)
            exparentizada = reemplazar(exparentizada, ('[', ']', '{', '}'), ('(', ')', '(', ')'))

            result = arithmeticEval(exparentizada)
            resultadoEnviar = "(" + str(result) + ")"
            socket2.send(resultadoEnviar.encode())

    return (exparentizada.split()[0])

#funcion que reemplaza todo a parentesis

def reemplazar(cadena, vector, nuevovector):
    for a, b in zip(vector, nuevovector):
        cadena = cadena.replace(a, b)
    return cadena

#funcion que calcula si existen el mismo numero de abiertos (parentesis, corchetes y llaves) que de cerrados
def comprobarBalanceo(cadena, socket2):
    bucleinfinito = True
    while bucleinfinito:
        opens = 0
        close = 0
        for caracter in cadena:
            if caracter in ('(', '[', '{'):
                opens += 1
            if caracter in (')', ']', '}'):
                close += 1

        if opens != close:
            reconectar = socket2.recv(1024).decode()
            cadena = cadena + reconectar
        else:
            bucleinfinito = False
    return cadena

#etapa 3 para descargar un fichero que coincide con el codigo recibido de la etapa anterior
#deacargado mediante una conexion http.client
def step_3():

    Enlace = step_2Arit().split()[0]
    connection = http.client.HTTPConnection('atclab.esi.uclm.es',5000)
    connection.request('GET', "/"+Enlace,"")
    response = connection.getresponse()
    mensaje3 = response.read().decode()    
    connection.close()
    return(mensaje3)

#etapa 4 donde se envia un paquete sin  codigo checksum, para posteriormente enviarlo con
#codigo cheksum y asi poder comprobar que se ha recibdo el paquete completo
#los datos se reciben a partir del campo 28 del ICMP
#PARA ESTA ETAPA SE NECESITAN PERMISOS DE ADMINISTRADOR YA QUE UTILIZA ICMP RAW
def step_4Checksum(): 

    codigo = step_3().split()[0]    
    
    Checksum = 0
    ICMP_ECHO = 8
    ID = 3030
    Sequence = 0

    data, header = completarCabecera(Checksum, ICMP_ECHO, ID, Sequence, codigo)
    
    packet = header + bytes(data,'ascii')
    
    Socket_ICMP = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    Socket_ICMP.sendto(packet, (socket.gethostbyname('atclab.esi.uclm.es'), 32))
    Socket_ICMP.recv (512)
    mensaje = Socket_ICMP.recv(2048)[28:] 
    
    print (mensaje.decode())
    Socket_ICMP.close()

    return (mensaje.decode())

#funcion para enviar los paquetes con y sin checksum
def completarCabecera(Checksum, ICMP_ECHO, ID, Sequence, codigo):
    header = struct.pack("!BBHHH", ICMP_ECHO, 0, Checksum, ID, Sequence)
    data = str(time.clock()) + codigo
    Checksum = checksum(header + bytes(data, 'ascii'))
    header = struct.pack("!BBHHH", ICMP_ECHO, 0, Checksum, ID, Sequence)
    return data, header


step_4Checksum()


