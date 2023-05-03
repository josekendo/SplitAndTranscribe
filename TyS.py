import argparse
import pysrt
import time
import concurrent.futures
from pydub import AudioSegment
import os

out = "output"
allTime = 0
listOfDelete = []

def extract_number(file_name):
    fileName = file_name.split("-")[-1]
    fileName = fileName.replace(".srt","")
    return int(fileName)

def exportarAudio(a,b):
    a.export(b, format="mp3")

def ejecutarWhisper(pathMP3,calidad,idioma):
    global allTime 
    filenameWithExtension = os.path.basename(pathMP3)
    filenameSplit = os.path.splitext(filenameWithExtension)[0]
    futureSTR = out + "/" + filenameSplit + ".srt"
    if not os.path.exists(futureSTR):
        comando = 'whisper \"'+pathMP3+'\" --output_dir '+out+' --output_format srt --language '+idioma+' --task translate --model '+calidad+' --device cuda'
        print(comando)
        inicio = time.time()
        os.system(comando)
        fin = time.time()
        duracion = fin - inicio
        allTime += duracion/60
        print("El proceso tardo ", str(duracion/60), " minutos.")
    else:
        print("Fase Whisper -> Ya existe: "+futureSTR+" se omite.")

def joinSubtitule(segment_duration,filenameSplit):
    #unificamos los subtitulos
    lista_subtitulos = [os.path.join(out, f) for f in os.listdir(out) if f.endswith('.srt')]
    lista_subtitulos = sorted(lista_subtitulos, key=extract_number)
    subtitulos_unificados = pysrt.SubRipFile()
    tiempo_inicio = 0
    numero_inicio = 1
    anterior = ""
    for sub in lista_subtitulos:
        subtitulos = pysrt.open(sub)
        print("Uniendo -> "+sub)
        for subtitulo in subtitulos:
            texto = str(subtitulo.text)
            texto = texto.lower()
            if not texto in listOfDelete and not anterior.lower() == texto:
                subtitulo.index = numero_inicio
                subtitulo.start.milliseconds  += tiempo_inicio
                subtitulo.end.milliseconds  += tiempo_inicio
                subtitulos_unificados.append(subtitulo)
                numero_inicio += 1
                anterior = subtitulo.text
        tiempo_inicio += segment_duration

    ruta_archivo_unificado = os.path.join(out, filenameSplit+'.srt')
    subtitulos_unificados.save(ruta_archivo_unificado, encoding='utf-8')

# Configurar los argumentos de línea de comandos
parser = argparse.ArgumentParser(description='Divide un archivo de audio en segmentos de 10 minutos.')
parser.add_argument('filename', type=str, help='Nombre del archivo de audio que se desea dividir.')
parser.add_argument('minutes', type=int, help='Tiempo en el que desea dividir los audios en minutos.')
parser.add_argument('calidad', type=str, help='Calidad de la traduccion (small, medium,large).')
parser.add_argument('idioma', type=str, help='Idioma de la traduccion (small, medium,large).')

parser.add_argument('-fw',type=str,help="Traduce solo el audio pasado.")
parser.add_argument('-fs',type=str,help="Fase union de subtitulos.")  
parser.add_argument('-fc',type=str,help="Fase corte audio.")  
parser.add_argument('-out',type=str,help="out directory.")  
parser.add_argument('-dic',type=str,help="dictionary for delete.")

# Obtener los argumentos de línea de comandos
args = parser.parse_args()

onlyWhisper = False
onlySubtitule = False

# Nombre del archivo de audio que se desea dividir
filename = args.filename
minutos = args.minutes
calidad = args.calidad
idioma = args.idioma
fase_whisper = args.fw 
fase_subs = args.fs

if str(fase_whisper) != "None":
    onlyWhisper = True

if str(fase_subs) != "None":
    onlySubtitule = True

if str(args.out) != "None":
    out = args.out

all_exec = onlyWhisper == False and onlySubtitule == False

# Asegurarse de que el directorio de salida exista
if not os.path.exists(out):
    os.makedirs(out)

# Duración de cada segmento en milisegundos (10 minutos en milisegundos)
segment_duration = minutos * 60 * 1000

audio = AudioSegment.from_file(filename)

# Dividir el archivo de audio en segmentos de la duración especificada
segments = audio[::segment_duration]

listaAudios = []

if(str(args.dic) != "None"):
    with open(str(args.dic), 'r') as file:
        listOfDelete = [line.strip() for line in file]
        listOfDelete = [s.lower() for s in listOfDelete]
    print("Load dictionary for delete ocurrences.")

filenameWithExtension = os.path.basename(filename)
filenameSplit = os.path.splitext(filenameWithExtension)[0]

if(all_exec):
    print("--- Begin Phase Split Audio ---")
    with concurrent.futures.ThreadPoolExecutor() as ejecutor:
        # Guardar cada segmento en un archivo separado
        for i, segment in enumerate(segments):
            output_filename = out+"/"+filenameSplit+"-"+str(i)+".mp3"
            if not os.path.exists(output_filename):
            # Construir el nombre del archivo de salida
                ejecutor.submit(exportarAudio,segment,output_filename)
            else:
                print("Fase dividir audios -> Ya existe: "+output_filename + "se omite.")
            listaAudios.append(output_filename)
    print("--- End Phase ---")
else:
    print("No se ejecuta fase dividir audios")

if(all_exec or onlyWhisper):
    print("--- Begin Phase Transcription ---")
#Ejecutamos whisper
    for subAudio in listaAudios:
        #ejecutor.submit(ejecutarWhisper,subAudio,calidad,idioma)
        ejecutarWhisper(subAudio,calidad,idioma)
    print(" El tiempo total de transcripcion es:" + str(allTime))
    print("--- End Phase ---")
else:
    print("No se ejecuta fase whisper")

if(all_exec or onlySubtitule):
    print("--- Begin Phase Union Transcriptions ---")
    joinSubtitule(segment_duration,filenameSplit)
    print("--- End Phase ---")
else:
    print("No se ejecuta fase subtitulos")