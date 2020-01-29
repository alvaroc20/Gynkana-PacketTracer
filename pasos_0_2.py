import socket
import operator, ast
import http.client

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


def step_0TCP():
    ginkana = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ginkana.connect(('atclab.esi.uclm.es', 2000))
    primer_mensaje = (ginkana.recv(1024)).decode('utf-8')
    print (primer_mensaje)
    ginkana.close()
    return (primer_mensaje)


def step_1UDP():
    port_1 = 23456
    servidorUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidorUDP.bind(('', port_1))
    UDP_iden = step_0TCP()[:5]
    mensaje = "{} {}".format(UDP_iden, port_1)
    servidorUDP.sendto(mensaje.encode('utf-8'), ('atclab.esi.uclm.es', 2000))
    segundo_mensaje = (servidorUDP.recv(1024)).decode('utf-8')
    print (mensaje)
    servidorUDP.close()
    return (segundo_mensaje)


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


def reemplazar(cadena, vector, nuevovector):
    for a, b in zip(vector, nuevovector):
        cadena = cadena.replace(a, b)
    return cadena


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


def step_3():
    Enlace = step_2Arit().split()[0]
    connection = http.client.HTTPConnection('atclab.esi.uclm.es', 5000)
    connection.request('GET', "/" + Enlace, "")
    response = connection.getresponse()
    mensaje3 = response.read().decode()
    print(mensaje3)
    connection.close()
    return (mensaje3)


step_3()


