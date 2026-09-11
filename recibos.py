import sys

def main():
    print("Iniciando...")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        main()
    else:
        print("Uso: python recibos.py recibos_listado.xlsx recibos_para_firmar.pdf")
else:
    print("Uso: python recibos.py recibos_listado.xlsx recibos_para_firmar.pdf")