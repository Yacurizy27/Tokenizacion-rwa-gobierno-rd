import random

numero = random.randint(1, 100)

while True:
    intento = int(input("Adivina el número: "))

    if intento < numero:
        print("Más alto")
    elif intento > numero:
        print("Más bajo")
    else:
        print("¡Correcto!")
        break
