import argparse
import pysrt
import time
import concurrent.futures
from pydub import AudioSegment
import os

out = "output"

def exportarAudio(a,b):
    a.export(b, format="mp3")
    

def ejecutarWhisper(a,calidad,idioma):
    comando = 'whisper '+a+' --output_dir '+out+' --output_format srt --language '+idioma+' --task translate --model '+calidad+' --device cuda'
    print(comando)
    inicio = time.time()
    os.system(comando)
    fin = time.time()
    duracion = fin - inicio
    print("El proceso tardo ", str(duracion/60), " minutos.")

def joinSubtitule(segment_duration,filenameSplit):
    #unificamos los subtitulos
    lista_subtitulos = [os.path.join(out, f) for f in os.listdir(out) if f.endswith('.srt')]
    subtitulos_unificados = pysrt.SubRipFile()
    tiempo_inicio = 0
    numero_inicio = 1
    for sub in lista_subtitulos:
        subtitulos = pysrt.open(sub)
        for subtitulo in subtitulos:
            subtitulo.index = numero_inicio
            subtitulo.start.milliseconds  += tiempo_inicio
            subtitulo.end.milliseconds  += tiempo_inicio
            subtitulos_unificados.append(subtitulo)
            numero_inicio += 1
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

filenameWithExtension = os.path.basename(filename)
filenameSplit = os.path.splitext(filenameWithExtension)[0]

if(all_exec or onlyWhisper):
    with concurrent.futures.ThreadPoolExecutor() as ejecutor:
        # Guardar cada segmento en un archivo separado
        for i, segment in enumerate(segments):
            # Construir el nombre del archivo de salida
            output_filename = out+"/"+filenameSplit+"-"+str(i)+".mp3"
            listaAudios.append(output_filename)
            ejecutor.submit(exportarAudio,segment,output_filename)
else:
    print("No se ejecuta fase dividir audios")

if(all_exec or onlyWhisper):
#Ejecutamos whisper
    for subAudio in listaAudios:
        #ejecutor.submit(ejecutarWhisper,subAudio,calidad,idioma)
        ejecutarWhisper(subAudio,calidad,idioma)
else:
    print("No se ejecuta fase whisper")

if(all_exec or onlySubtitule):
    joinSubtitule(segment_duration,filenameSplit)
else:
    print("No se ejecuta fase subtitulos")