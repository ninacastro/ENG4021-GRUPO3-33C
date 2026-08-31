#Funções Calculadora 
def calcula_soma(x,y):
  return x + y

def calcula_subtração(x,y):
  return x - y

def calcula_multiplicação(x,y):
  return x * y

def calcula_divisão(x,y):
  return x / y

def calcula_resto(x,y):
  return x % y

def calcula_percentual(x,y):
  return x / 100 * y 

def calcula_divisão_inteira(x,y):
  return x//y

def calcula_potenciação(x,y):
  return x**y

def calcula_radiciação(x,y):
  return x**(1/y)


#Bloco Principal
valor1= float(input("Escolha o 1º valor: "))
valor2= float(input("Escolha o 2º valor: "))
operação= int(input("Escolha uma das operações abaixo: "
                    "1- Adição\n"
                    "2- Subtração\n"
                    "3- Multiplicação\n"
                    "4- Divisão\n"
                    "5- Resto\n"
                    "6- Percentual\n"
                    "7- Divisão inteira\n"
                    "8- Potenciação\n"
                    "9- Radiciação\n"
                    "0- Sair do Programa\n"))
if operação == 0:
  print()
if operação == 1:
  print(calcula_soma(valor1, valor2))
if operação == 2:
  print(calcula_subtração(valor1, valor2))
if operação == 3:
  print(calcula_multiplicação(valor1, valor2))
if operação == 4:
  print(calcula_divisão(valor1, valor2))
if operação == 5:
  print(calcula_resto(valor1, valor2))
if operação == 6:
  print(calcula_percentual(valor1, valor2))
if operação == 7:
  print(calcula_divisão_inteira(valor1, valor2))
if operação == 8:
  print(calcula_potenciação(valor1, valor2))
if operação == 9:
  print(calcula_radiciação(valor1, valor2))


