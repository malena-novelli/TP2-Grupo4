import csv

def lectura_archivo(archivo:str)->list:
    denuncias:list=[]
    try:
        with open (archivo) as file:
            reader=csv.reader(file,delimiter=",")            
            next(reader)
            for linea in reader:
                denuncias.append(linea)
    except IOError:
        print("se produjo un error en la lectura del archivo" )

    return(denuncias)

def escribir_archivo(denuncias_procesadas:list):
    try:
        with open ("denuncias_procesadas.csv","w",newline="") as new_file:
            writer=csv.writer(new_file,delimiter=",")
            header:list=["Timestamp","Teléfono", "Dirección","patente", "descripción texto","descripción audio"] 
            writer.writerow(header)
            writer.writerows(denuncias_procesadas)
    except:
        print("Se produjo un error al generar el archivo")
