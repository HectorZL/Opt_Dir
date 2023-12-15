import subprocess
import os
import tkinter as tk
from tkinter import filedialog
import pickle
from tqdm import tqdm
from datetime import datetime
from hurry.filesize import size  # Puedes instalar esto con `pip install hurry.filesize`

def compress_video(original_path, output_path, crf=50):
    """Compresión de video usando ffmpeg con un Factor de Tasa Constante (CRF) específico."""
    cmd = ['ffmpeg', '-hide_banner', '-i', original_path, '-c:v', 'libx264', '-preset', 'fast', '-crf', str(crf), '-c:a', 'aac', '-strict', 'experimental', output_path]

    try:
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        for line in process.stderr:
            # Buscar la línea que contiene el progreso
            if "time=" in line and "bitrate=" in line:
                print("\r" + line.strip(), end='', flush=True)
        process.communicate()

        if process.returncode == 0:
            print(f"\rCompresión exitosa: {original_path} -> {output_path}")
        else:
            print(f"\rError al comprimir {original_path}: Error en FFmpeg.")
    except Exception as e:
        print(f"\rError al comprimir {original_path}: {e}")

def compress_videos_in_folder(folder_path, crf=18, resume_file='compression_resume.pkl'):
    """Compresión de todos los videos en una carpeta dada."""
    resume_state = {'current_index': 0, 'total_files': 0}

    # Verificar si hay un estado de compresión previo y cargarlo si existe
    if os.path.exists(resume_file):
        with open(resume_file, 'rb') as file:
            resume_state = pickle.load(file)

    files_to_compress = [file for file in os.listdir(folder_path) if file.lower().endswith('.mp4')]

    # Si hay archivos para comprimir, reanudar la compresión desde la última posición
    if resume_state['total_files'] > 0 and resume_state['current_index'] < resume_state['total_files']:
        files_to_compress = files_to_compress[resume_state['current_index']:]

    # Contar archivos totales
    total_files = len(files_to_compress)

    # Inicializar variables para el tiempo y el peso total
    total_time_start = datetime.now()
    total_size_before = sum(os.path.getsize(os.path.join(folder_path, file)) for file in files_to_compress)

    # Realizar la compresión con barra de progreso y ETA
    with tqdm(total=total_files, desc="Compresión de videos", dynamic_ncols=True, miniters=1) as pbar:
        for index, file in enumerate(files_to_compress, start=resume_state['current_index']):
            original_path = os.path.join(folder_path, file)
            compressed_path = os.path.join(folder_path, f"{os.path.splitext(file)[0]}_compressed.mp4")

            # Verificar si el archivo ya está comprimido
            if os.path.exists(compressed_path):
                pbar.update(1)  # Actualizar la barra de progreso
                continue

            compress_video(original_path, compressed_path, crf)

            # Actualizar el estado de compresión
            resume_state['current_index'] = index + 1
            resume_state['total_files'] = total_files

            with open(resume_file, 'wb') as file:
                pickle.dump(resume_state, file)

            # Actualizar la barra de progreso
            pbar.update(1)

    # Calcular el tiempo total de procesamiento
    total_time_elapsed = datetime.now() - total_time_start

    # Calcular el peso total después de la compresión
    total_size_after = sum(os.path.getsize(os.path.join(folder_path, f"{os.path.splitext(file)[0]}_compressed.mp4")) for file in files_to_compress)

    # Mostrar información final
    print("\n--- Información final ---")
    print(f"Número total de archivos: {total_files}")
    print(f"Tiempo total de procesamiento: {total_time_elapsed}")
    print(f"Hora actual: {datetime.now()}")
    print(f"Peso total antes de la compresión: {size(total_size_before)}")
    print(f"Peso total después de la compresión: {size(total_size_after)}")

# Seleccionar una carpeta utilizando el cuadro de diálogo de archivos de Tkinter
root = tk.Tk()
root.withdraw()
folder_path = filedialog.askdirectory(title="Selecciona la carpeta de videos")

# Verificar si el usuario seleccionó una carpeta
if folder_path:
    compress_videos_in_folder(folder_path)
else:
    print("No se seleccionó ninguna carpeta.")
