import sqlite3
import pandas as pd
import os
import xml.etree.ElementTree as ET
import re

# --- CONFIGURACIÓN CRÍTICA ---
DB_NAME = "contratos_menores.db"
MAX_SIZE_MB = 23.8  # Dejamos un margen para que GitHub lo acepte sin problemas

def inicializar_db():
    """Crea la base de datos con la estructura completa requerida."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS licitaciones') # Limpiamos para asegurar estructura
    cursor.execute('''
        CREATE TABLE licitaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            importe REAL,
            adjudicatario TEXT,
            comunidad TEXT,
            provincia TEXT,
            fecha TEXT,
            enlace TEXT
        )
    ''')
    conn.commit()
    conn.close()

def extraer_fecha(nombre):
    """Extrae la fecha del nombre del archivo para ordenar."""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', nombre)
    return match.group(1) if match else "0000-00-00"

def ejecutar_scraper():
    inicializar_db()
    
    # 1. Listar y ordenar archivos de 2026 (De más reciente a más antiguo)
    archivos = [f for f in os.listdir('.') if f.endswith('.atom')]
    archivos.sort(key=extraer_fecha, reverse=True) 
    
    if not archivos:
        print("No se han encontrado archivos .atom")
        return

    conn = sqlite3.connect(DB_NAME)
    print(f"🚀 Procesando archivos de 2026 (Priorizando los más recientes)...")

    for archivo in archivos:
        fecha_archivo = extraer_fecha(archivo)
        registros = []
        
        try:
            tree = ET.parse(archivo)
            root = tree.getroot()
            # Namespace universal para buscar etiquetas sin errores
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                titulo = entry.find('{http://www.w3.org/2005/Atom}title').text
                
                # Importe, Adjudicatario y Ubicación usando búsqueda profunda {*}
                importe_elem = entry.find('.//{*}TotalAmount')
                importe = float(importe_elem.text) if importe_elem is not None else 0.0
                
                adj_elem = entry.find('.//{*}PartyName/{*}Name')
                adjudicatario = adj_elem.text if adj_elem is not None else "N/A"
                
                comu_elem = entry.find('.//{*}CountrySubentity')
                comunidad = comu_elem.text if comu_elem is not None else "Desconocida"
                
                prov_elem = entry.find('.//{*}CityName')
                provincia = prov_elem.text if prov_elem is not None else "Ver detalle"
                
                link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
                enlace = link_elem.attrib['href'] if link_elem is not None else ""

                registros.append((titulo, importe, adjudicatario, comunidad, provincia, fecha_archivo, enlace))

            # Insertamos los datos de este archivo
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT INTO licitaciones (titulo, importe, adjudicatario, comunidad, provincia, fecha, enlace)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', registros)
            conn.commit()
            
            # --- CONTROL DE TAMAÑO ---
            conn.execute("VACUUM") # Compacta el archivo para medir el peso REAL en disco
            peso_actual = os.path.getsize(DB_NAME) / (1024 * 1024)
            
            if peso_actual >= MAX_SIZE_MB:
                print(f"🛑 Límite de seguridad alcanzado: {peso_actual:.2f} MB.")
                print(f"Se han guardado los contratos más recientes hasta la fecha: {fecha_archivo}")
                break
                
        except Exception as e:
            print(f"Error en {archivo}: {e}")

    conn.close()
    print(f"✅ Base de datos finalizada: {os.path.getsize(DB_NAME)/(1024*1024):.2f} MB")

if __name__ == "__main__":
    ejecutar_scraper()