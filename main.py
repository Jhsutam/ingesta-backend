# archivo: main.py
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
import json
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

def cliente_existe(nit: str) -> dict:
    response = supabase.table("clientes").select("*").eq("nit", nit).execute()
    if response.
        return response.data[0]
    return None

def generar_backup(cliente_data: dict, experiencias_ list, nit: str):
    backup_data = {"cliente": cliente_data, "experiencias": experiencias_data}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"/tmp/backup_{nit}_{timestamp}.json"
    with open(backup_filename, 'w') as f:
        json.dump(backup_data, f, indent=4, default=str)
    return backup_filename

def obtener_experiencias_existentes(id_cliente: int) -> list:
    response = supabase.table("experiencias").select("*").eq("id_cliente", id_cliente).execute()
    return response.data

def actualizar_cliente_y_experiencias(cliente_id: int, nuevos_datos):
    # Actualizar cliente
    supabase.table("clientes").update(nuevos_datos["cliente"]).eq("id_cliente", cliente_id).execute()
    # Eliminar experiencias antiguas
    supabase.table("experiencias").delete().eq("id_cliente", cliente_id).execute()
    # Insertar nuevas experiencias
    for exp in nuevos_datos["experiencias"]:
        exp["id_cliente"] = cliente_id
        supabase.table("experiencias").insert(exp).execute()

@app.route('/api/v1/registrar-cliente', methods=['POST'])
def registrar_cliente():
    try:
        # --- 1. OBTENER LOS ARCHIVOS DE LA SOLICITUD ---
        file_rut = request.files['rut']
        file_camara = request.files['camara']
        file_rup = request.files['rup']
        file_experiencia = request.files['experiencia']

        # --- 2. EXTRAER EL NIT DEL NOMBRE DEL ARCHIVO ---
        rut_filename = secure_filename(file_rut.filename)
        nit = rut_filename.split('_')[0] # Obtiene "830070095-1" de "830070095-1_rut.pdf"

        # --- 3. GUARDAR LOS ARCHIVOS TEMPORALMENTE ---
        ruta_rut = os.path.join(app.config['UPLOAD_FOLDER'], rut_filename)
        file_rut.save(ruta_rut)
        
        ruta_camara = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file_camara.filename))
        file_camara.save(ruta_camara)
        
        ruta_rup = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file_rup.filename))
        file_rup.save(ruta_rup)
        
        ruta_experiencia = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file_experiencia.filename))
        file_experiencia.save(ruta_experiencia)

        # --- 4. PROCESAR LOS ARCHIVOS Y EXTRAER DATOS (SIMULADO) ---
        # En la versión final, aquí irá el código que parsea los PDFs y el Excel.
        datos = {
            "cliente": {
                "razon_social": f"INSTITUCIÓN DE EJEMPLO - {nit}",
                "nit": nit,
                "tipo_entidad": "Simulada para PRUEBA",
                "pais": "Colombia",
                "fecha_constitucion": "2000-01-01",
                "rut_url": secure_filename(os.path.basename(ruta_rut)),
                "certificado_existencia_url": secure_filename(os.path.basename(ruta_camara))
            },
            "experiencias": [
                {"nombre_proyecto": "Proyecto de Prueba", "entidad_contratante": "ENTIDAD DE PRUEBA", "valor_contrato": 1000000.00, "fecha_inicio": "2023-01-01", "fecha_fin": "2023-12-31", "tipo_experiencia": "RUP"}
            ]
        }

        # --- 5. LÓGICA DE REGISTRO/ACTUALIZACIÓN (Sprint 3) ---
        cliente_existente = cliente_existe(nit)
        if cliente_existente is None:
            # Registrar nuevo cliente
            cliente_resp = supabase.table("clientes").insert(datos["cliente"]).execute()
            id_cliente = cliente_resp.data[0]["id_cliente"]
            for exp in datos["experiencias"]:
                exp["id_cliente"] = id_cliente
                supabase.table("experiencias").insert(exp).execute()
            return jsonify({"status": "success", "message": "Institución registrada con éxito."})
        else:
            # Generar backup y actualizar
            experiencias_actuales = obtener_experiencias_existentes(cliente_existente["id_cliente"])
            generar_backup(cliente_existente, experiencias_actuales, nit)
            actualizar_cliente_y_experiencias(cliente_existente["id_cliente"], datos)
            return jsonify({"status": "success", "message": "Institución actualizada con éxito."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
