import csv
import speech_recognition as sr
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from PIL import Image
import datetime
import time
import requests
import copy

#PUNTO 1
def lectura_archivo()->list:
	""" Obj: Lee el archivo denuncias_bis y devuelve la informacion en una lista
		Pre: Archivo a leer
		Post: Lista con las lineas del archivo
	"""
	denuncias:list=[]
	try:
		with open ("denuncias_bis.csv") as file:
			reader=csv.reader(file,delimiter=",")            
			next(reader)
			for linea in reader:
				denuncias.append(linea)
	except IOError:
		print("\nSe produjo un error en la lectura del archivo" )

	return denuncias

#TERMINA PUNTO1

def obtener_datos_Brutos(datos_Brutos: list, timestamps: list, latitud: list, longitud: list, rutas_audios: list, rutas_fotos: list)->None:
	""" Obj: Crea "sub-listas" con cada campo de la matriz de datos obtenida a partir del archivo original  
		Pre: Lista con los datos brutos de las infracciones, 5 listas donde recopilar la informacion
		Post: 5 listas con los datos descompuestos de la matriz principal 
	"""
	for registro in range(len(datos_Brutos)):
		timestamps.append(datos_Brutos[registro][0])
		latitud.append(datos_Brutos[registro][2])
		longitud.append(datos_Brutos[registro][3])
		rutas_audios.append(datos_Brutos[registro][6])
		rutas_fotos.append(datos_Brutos[registro][4])

#PUNTO 2

def obtener_timestamp(lista_timestamp:list)->list:
	"""Obj: Convertir un serie de numeros str a una fecha timestamp
	   Pre: Recibe una lista con timestamps en formato str
	   Post: Devuelve una lista con timestamps en formato datetime
	"""
	lista_fechas: list = []	
	for valores in lista_timestamp:
		valores = datetime.datetime.fromtimestamp(float(valores))
		lista_fechas.append(valores)
	return lista_fechas

def obtener_direccion(latitud:str,longitud:str)->str:
	""" Obj: Consigue una unica direccion mediante el uso de Geopy a partir de las coordenadas geograficas 
		Pre: 2 strings, uno con la latitud y el otro con la longitud de interes
		Post: 1 string con la direccion del lugar de interes 
	"""    
	geolocator= Nominatim(user_agent="TP2")
	try:
		direccion_de_infraccion=(str(geolocator.reverse(str(latitud)+","+str(longitud))))
	except TimeoutError:
		print("\nNo se pudo acceder al proveedor para obtener los datos")
	return direccion_de_infraccion

def crear_lista_direcciones(latitud:list,longitud:list)->list:
	""" Obj: Genera una lista de str:direcciones mediante el uso de Geopy 
		Pre: 2 listas de strings, una con las latitudes y otra con las longitudes
		Post: 1 lista con direcciones de los lugares
	"""	      
	direcciones:list=[]
	for registro in range (len(latitud)):
		direccion_de_infraccion:str=str(obtener_direccion(latitud[registro],longitud[registro]))
		direcciones.append(direccion_de_infraccion)

	return direcciones

def conseguir_coordenadas(direccion:str)->list:
	""" Obj: Consigue las coordenadas geograficas de una direccion especificada 
		Pre: 1 string con la direccion solicitada
		Post: 1 lista cuyos elementos son las [lat,long] de la direccion
		"""	
	geolocator= Nominatim(user_agent="TP2")
	try:
		lat=float(geolocator.geocode(direccion).point.latitude)
		lon=float(geolocator.geocode(direccion).point.longitude)
		coordenadas:list=[lat,lon]
	except TimeoutError: 
		print ("\nHubo un error al conseguir los datos, verifique su conexion.")
	except:
		print( "\nNo se pudo localizar la dirección.")       
	return coordenadas

def mostrar_patente(ruta_imagen)->str:
	""" Obj: Recibe una ruta de foto y devuelve la patente en caso de encontrar un automovil  
		Pre: 1 Lista con rutas para las imagenes 
		Post: 1 string con la patente
	"""
	try:
		with open(ruta_imagen, 'rb') as fp:
			response = requests.post(
			'https://api.platerecognizer.com/v1/plate-reader/',
			files=dict(upload=fp), 
			headers={'Authorization': 'Token 15ca3097b892584724d956a3feed60f32614585c'}) #Este Token se obtiene al registrarse en la web
			for key, value in (response.json()).items():
				if key == "results":
					for valores in value: 
						patente: str = valores['plate']
						return patente
	except IOError:
		print("\nNo se encontró la ruta del archivo.")

def crear_lista_patentes(lista:list)->list:
	""" Obj: Crea una lista con las patentes a partir de una lista de rutas  
		Pre: Lista de datos con las rutas de las fotos
		Post: Lista con las patentes de las fotografias
	"""
	patentes: list = []
	for i in lista:
		patentes.append(mostrar_patente(i))
	return patentes

def obtener_descripcion_audio(rutas_audios:list)->list:
	""" Obj: Crea una lista con los textos de los audios a partir de sus rutas  
		Pre: Lista de datos con las rutas de audio
		Post: Lista con los textos contenidos en los audios
	"""
	descripciones: list = []
	for ruta in range(len(rutas_audios)):
		r = sr.Recognizer()
		with sr.AudioFile(rutas_audios[ruta]) as source:
			audio = r.record(source)
		try:
			descripcion: str = r.recognize_google(audio, language ='es_AR')
			descripciones.append(descripcion)
			
		except sr.UnknownValueError:
			print("\nNo fue posible entender el audio.")
		except IOError:
			print("\nNo se encontró el archivo deseado.")

	return descripciones

def compaginar_datos_Procesados(datos_Brutos:list, fecha:list, direccion:list, patentes:list, descripciones_audios:list)->list:
	""" Obj: Crea una lista a partir de los datos recopilados en las sub listas procesadas  
		Pre: Sub listas con los datos a integrarse en la matriz
		Post: 1 lista con toda la informacion procesada y compaginada 
	"""
	datos_procesados: list = copy.deepcopy(datos_Brutos)
	for i in range(len(datos_Brutos)):
		datos_procesados[i][0] = fecha[i]
		datos_procesados[i][2] = direccion[i]
		datos_procesados[i][3] = patentes[i]
		datos_procesados[i][4] = datos_Brutos[i][5]
		datos_procesados[i][5] = descripciones_audios[i]
		datos_procesados[i].pop(6)
	return datos_procesados

def escribir_archivo(denuncias_procesadas:list)->None:
	""" Obj: Toma una lista y la vuelca en un archivo creandolo o sobreescribiendolo 
		Pre: Una lista con los datos a escribir
		Post: Un archivo nuevo llamado ("denuncias procesadas") 
	"""
	try:
		with open ("denuncias_procesadas.csv","w",newline="") as new_file:
			writer=csv.writer(new_file,delimiter=",")
			header:list=["Fecha","Teléfono", "Dirección", "Patente", "Descripción texto","Descripción audio"] 
			writer.writerow(header)
			writer.writerows(denuncias_procesadas)
	except:
		print("\nSe produjo un error al generar el archivo")
#TERMINA PUNTO 2

#PUNTO 3
def infracciones_estadios(infracciones:list)->None:
	""" Obj: Decide si las infracciones se cometieron a un radio de 1 km respecto a los estadios, muestra aquellas que lo estuvieron. 
		Pre: Lista de infracciones ya procesadas con direcciones
		Post: Muestra por pantalla una lista de infracciones en el area indicada
		"""	
	infracciones_bombonera:list=[]
	infracciones_monumental:list=[]
	bombonera:list=conseguir_coordenadas("estadio Alberto J. Armando")
	monumental:list=conseguir_coordenadas("estadio Monumental")
	
	for registro in range (len(infracciones)):
		coord_infraccion:list=conseguir_coordenadas(infracciones[registro][2])
		if (geodesic(bombonera, coord_infraccion).kilometers<1):
			infracciones_bombonera.append(infracciones[registro])
		elif (geodesic(monumental, coord_infraccion).kilometers<1):
			infracciones_monumental.append(infracciones[registro])
	
	print ("\nLas siguientes infracciones se produjeron en las inmediaciones del estadio 'Alberto J. Armando'")
	for item in infracciones_bombonera:
		print(f"\n{item}")
	print ("\nLas siguientes infracciones se produjeron en las inmediaciones del estadio 'Mas Monumental'")
	for item in infracciones_monumental:
		print(f"\n{item}")
#TERMINA PUNTO 3

#PUNTO 4
def delimitar_zona_centro ()->list:
	""" Obj: Recupera las coordenadas geograficas de la zona centrica y las empaqueta como lista de listas 
		Pre: Sin parametros previo
		Post: 1 lista de listas cuyos elementos son las [lat,long] de las esquinas de la zona centrica
	"""	
	coordenadas_esquina_a:list=conseguir_coordenadas("Av. Callao & Av. Rivadavia")
	coordenadas_esquina_b:list=conseguir_coordenadas("Av. Callao & Av. Córdoba")
	coordenadas_esquina_c:list=conseguir_coordenadas("Av. Leandro N. Alem & Av. Córdoba")
	coordenadas_esquina_d:list=conseguir_coordenadas("Av. Rivadavia 100, Monserrat, Buenos Aires")
	
	zona_centro:list=[coordenadas_esquina_a,coordenadas_esquina_b,coordenadas_esquina_c,coordenadas_esquina_d]
	return zona_centro

def infracciones_del_centro(infracciones_procesadas:list)->None:
	""" Obj: Decide si las infracciones se cometieron dentro de la zona indicada, muestra aquellas que lo estuvieron.  
		Pre: Lista de infracciones ya procesadas con direcciones
		Post: Muestra por pantalla una lista de infracciones en el area indicada
		"""	 
	zona_centro:list=delimitar_zona_centro()
	infracciones_zona_centro:list=[]

	for registro in range (len(infracciones_procesadas)):
		coordenadas_infraccion:list=conseguir_coordenadas(infracciones_procesadas[registro][2])
		lat:float=float(coordenadas_infraccion[0])        
		lon:float=float(coordenadas_infraccion[1])
		#la condicion del if basicamente pide que se encuentre dentro del rectangulo delimitado por las calles dadas
		if ((lat>(zona_centro[0][0]) and lat<(zona_centro[1][0])) and (lon>(zona_centro[1][1]) and lon<(zona_centro[2][1]))):
			infracciones_zona_centro.append(infracciones_procesadas[registro])
	print("\nLas siguientes infracciones se produjeron en zona centro: ")
	for registro in infracciones_zona_centro:
		print (f"\n{registro}")
#TERMINA PUNTO 4

#PUNTO 5
def patente_sospechosa()->None:
	"""Obj: Reconocer si un auto tiene pedido de captura
	   Pre: Recibe dos archivos, el primero que contenga patentes,fechas y direcciones. El segundo con patentes con pedido de captura
	   Post: Imprime por terminal la patente del auto, la fecha en que fue visto y en que direccion
	"""
	datos: list = []
	try:
		with open("denuncias_procesadas.csv", newline='') as archivo_csv:
			next(archivo_csv)
			csv_reader = csv.reader(archivo_csv, delimiter=',', skipinitialspace= True)
			for lineas in csv_reader:
				datos.append(lineas)
	except IOError:
		print("\nSe produjo un error en la lectura del archivo" )
	try:
		with open("robados.txt", "r") as archivo:
			patentes_buscada: list = []
			for linea in archivo:
				lineas = linea.rstrip("\n")
				patentes_buscada.append(lineas)
			patentes_buscada.pop(0)
	except IOError:
		print("\nSe produjo un error en la lectura del archivo" )

	patentes_alerta: dict = {}

	for informacion in datos:
		if informacion[3] in patentes_buscada:
			patentes_alerta[informacion[3]] = [informacion[0], informacion[2]]
	for key, valor in patentes_alerta.items():
		print(f'\nEl auto de patente {key} tiene pedido de captura. Visto el dia {valor[0]} en {valor[1]}.')
#TERMINA PUNTO 5

#PUNTO 6:
def mostrar_foto_patente(ruta_foto: str)->None:
	""" Obj: Mostrar la foto asociada a una dada ruta  
		Pre: String con Ruta de la foto
		Post: Muestra por pantalla la imagen asociada a la ruta indicada
	"""
	try: 
		print("\nLa imágen asociada a la patente indicada es la siguiente: ")
		im = Image.open(ruta_foto, 'r') 
		im.show()
	except IOError:
		print("\nNo se encontró el archivo de la foto asociada.")

def mostrar_mapa(lat: str, long: str)->None:
	""" Obj: Mostrar el mapa asociado a la direccion de una infraccion  
		Pre: 2 str, el primero indica latitud y el otro longitud de la infraccion
		Post: Muestra por pantalla el mapa asociado
	"""
	print("\nA continucación, un mapa con la ubicación del auto indicado, en el momento de la denuncia: ")
	
	map = Basemap(width=9000000,height=5000000,projection='lcc',
			resolution=None,lat_1=-30.,lat_2=-40,lat_0=-35,lon_0=-60.)
	plt.figure(figsize=(19,20))
	map.bluemarble()
	x, y = map(long, lat)
	map.plot(x,y,marker='o',color='Red',markersize=5)
	plt.show()

def mostrar_infractor(datos_Brutos: list, datos_Procesados: list)->None:
	""" Obj: Muestra por pantalla la imagen y el mapa de una infraccion cometida por una patente indicada por el usuario  
		Pre: 2 listas, una con los datos sin procesar y otra con los mismos procesados
		Post: Muestra por pantalla la imagen del infractor y el mapa donde ocurrio 
	"""
	patente: str = input("\nIngrese la patente: ")
	for i in range(len(datos_Procesados)):
		if datos_Procesados[i][3] == patente:
			indice: int = i
		
	ruta_foto: str = datos_Brutos[indice][4]
	mostrar_foto_patente(ruta_foto)

	lat = datos_Brutos[indice][2]
	long = datos_Brutos[indice][3]
	mostrar_mapa(lat, long)
#TERMINA PUNTO 6

# PUNTO 7: 
def calcular_denuncias_mensuales(fechas:list)->list:
	"""Obj: Obtener una lista con denuncias mensuales
	   Pre: Recibe una lista de timestamps de tipo int
	   Post: Devuelve una lista de numeros segun la cantidad de denuncias por mes
	"""
	lista_fechas: list = []
	cant_denuncias: dict = {1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0,10:0,11:0,12:0}
	for fecha in fechas:
		mes = fecha.month #Transforma a numero de mes el datetime
		if mes in lista_fechas:
			cant_denuncias[mes] += 1
		else:
			lista_fechas.append(mes)
			cant_denuncias[mes] += 1
	eje_y: list = [cant_denuncias[1],cant_denuncias[2],cant_denuncias[3],cant_denuncias[4],
					cant_denuncias[5],cant_denuncias[6],cant_denuncias[7],cant_denuncias[8],
					cant_denuncias[9],cant_denuncias[10],cant_denuncias[11],cant_denuncias[12]]
	return eje_y

def graficar_denuncias_mensuales(eje_y:list)->None:
	"""Obj: Graficar las denuncias mensualmente en el año 2022
	   Pre: Recibe una lista de numeros
	   Post: Devuelve por terminal un grafico de barras
	"""
	x: list = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
	y: list = eje_y

	plt.bar(x,y,color = 'tab:purple')
	plt.xlabel('MESES', fontdict = {'fontsize':12, 'fontweight':'bold', 'color':'g'})
	plt.ylabel('DENUNCIAS', fontdict = {'fontsize':12, 'fontweight':'bold', 'color':'g'})
	plt.title('Denuncias registradas mensualmente', fontdict = {'fontsize':12, 'fontweight':'bold', 'color':'g'})
	plt.show()
#TERMINA PUNTO 7

#MENÚ
def menu(listaOpciones)->None:
	"""
	Pre: Se reciben 1 parámetros con la lista de opciones a ser mostradas
	Post: se retorna la opción seleccionada como entero.
	"""
	for i in range(0, len(listaOpciones)):
		print(i + 1, "- " + listaOpciones[i])

	op = int(input("\nElija una opción, 0 para salir: "))
	return op
#TERMINA MENÚ 

def main()->None:
	datos_Brutos: list = lectura_archivo()
	timestamps: list = []
	latitud: list = []
	longitud: list = []
	rutas_audios: list = []
	rutas_fotos: list = []
	obtener_datos_Brutos(datos_Brutos, timestamps, latitud, longitud, rutas_audios, rutas_fotos)
	
	fechas: list = obtener_timestamp(timestamps)
	direcciones: list = crear_lista_direcciones(latitud, longitud)
	patentes: list = crear_lista_patentes(rutas_fotos)
	descripciones_audios: list = obtener_descripcion_audio(rutas_audios)
	datos_Procesados: list = compaginar_datos_Procesados(datos_Brutos, fechas, direcciones ,patentes, descripciones_audios)
	
	eje_y: list = calcular_denuncias_mensuales(fechas)

	for item in datos_Procesados:
		if item[3]==None:
			datos_Procesados.pop(datos_Procesados.index(item))

	escribir_archivo(datos_Procesados)
	
	opciones = ["Mostrar infracciones en estadios", "Mostar infracciones en zona centro","Buscar patente sospechosa","Localizar infractor","Graficar denuncias mensuales"]

	op = menu(opciones)

	while op != 0:
		if op == 1:
			infracciones_estadios(datos_Procesados)
		elif op == 2:
			infracciones_del_centro(datos_Procesados)
		elif op == 3:
			patente_sospechosa()
		elif op == 4:
			mostrar_infractor(datos_Brutos, datos_Procesados)
		elif op == 5:
			graficar_denuncias_mensuales(eje_y)
		op = menu(opciones)

main()
