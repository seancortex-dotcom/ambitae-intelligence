import xml.etree.ElementTree as ET
import sqlite3
import glob
import os

# Diccionario para traducir códigos de región (NUTS) a nombres legibles
MAPA_REGIONES = {
    'ES11': 'Galicia', 'ES12': 'Asturias', 'ES13': 'Cantabria', 'ES21': 'País Vasco',
    'ES22': 'Navarra', 'ES23': 'La Rioja', 'ES24': 'Aragón', 'ES30': 'Madrid',
    'ES41': 'Castilla y León', 'ES42': 'Castilla-La Mancha', 'ES43': 'Extremadura',
    'ES51': 'Cataluña', 'ES52': 'C. Valenciana', 'ES53': 'Islas Baleares',
    'ES61': 'Andalucía', 'ES62': 'Murcia', 'ES63': 'Ceuta', 'ES64': 'Melilla',
    'ES70': 'Canarias'
}

directorio_actual = os.path.dirname(os.path.abspath(__file__))
ruta_bd = os.path.join(directorio_actual, 'contratos_menores.db')
conexion = sqlite3.connect(ruta_bd)
cursor = conexion.cursor()

# Creamos la tabla con UBICACIÓN y CP
cursor.execute('''
    CREATE TABLE IF NOT EXISTS licitaciones (
        id_expediente TEXT PRIMARY KEY,
        titulo TEXT,
        importe REAL,
        adjudicatario TEXT,
        fecha TEXT,
        enlace TEXT,
        comunidad TEXT,
        cp TEXT,
        archivo_origen TEXT
    )
''')
conexion.commit()

archivos_encontrados = glob.glob(os.path.join(directorio_actual, '*.atom'))
total_guardados = 0

print(f"🚀 Procesando {len(archivos_encontrados)} archivos...")

for archivo_atom in archivos_encontrados:
    nombre_archivo = os.path.basename(archivo_atom)
    try:
        tree = ET.parse(archivo_atom)
        root = tree.getroot()
        batch_contratos = []

        for entry in root.findall('.//*'):
            if entry.tag.endswith('entry'):
                d = {
                    'id': 'Desconocido', 'titulo': 'Sin título', 'importe': 0.0,
                    'adj': 'Desconocido', 'fecha': 'Sin fecha', 'link': 'Sin enlace',
                    'comu': 'Desconocida', 'cp': '00000'
                }
                
                en_ganador = False
                for child in entry.iter():
                    tag = child.tag.split('}')[-1]
                    
                    if tag == 'ContractFolderID': d['id'] = child.text
                    elif tag == 'title' and d['titulo'] == "Sin título": d['titulo'] = child.text
                    elif tag == 'TaxExclusiveAmount': 
                        try: d['importe'] = float(child.text)
                        except: pass
                    elif tag == 'id' and 'contrataciondelestado' in (child.text or ''): d['link'] = child.text
                    elif tag == 'AwardDate': d['fecha'] = child.text
                    elif tag == 'WinningParty': en_ganador = True
                    elif tag == 'Name' and en_ganador: 
                        d['adj'] = child.text
                        en_ganador = False
                    # --- EXTRACCIÓN DE UBICACIÓN ---
                    elif tag == 'CountrySubentityCode': # Código de región
                        code = child.text[:4] if child.text else ''
                        d['comu'] = MAPA_REGIONES.get(code, "Otras / Servicios Centrales")
                    elif tag == 'Postcode': d['cp'] = child.text

                if 0 < d['importe'] < 15000.00:
                    batch_contratos.append((d['id'], d['titulo'], d['importe'], d['adj'], d['fecha'], d['link'], d['comu'], d['cp'], nombre_archivo))

        cursor.executemany('INSERT OR IGNORE INTO licitaciones VALUES (?,?,?,?,?,?,?,?,?)', batch_contratos)
        conexion.commit()
        total_guardados += len(batch_contratos)
        print(f"  ✅ {nombre_archivo}: +{len(batch_contratos)} contratos.")

    except Exception as e:
        print(f"  ❌ Error en {nombre_archivo}: {e}")

print(f"\n✨ ¡Listo! {total_guardados} contratos con ubicación guardados en la base de datos.")
conexion.close()