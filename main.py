# main.py
from flask import Flask, request, jsonify
from flask_cors import CORS
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
CORS(app)  # Habilita CORS para todas las rutas
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

def cliente_existe(nit: str) -> dict:
    """Verifica si un cliente con el NIT dado ya existe en la BD."""
    response = supabase.table("clientes").select("*").eq("nit", nit).execute()
    if response.data:
        return response.data[0]
    return None

def generar_backup(cliente_ dict, experiencias_ list, nit: str):
    """Genera un archivo JSON con el backup del cliente existente."""
    backup_data = {"cliente": cliente_data, "experiencias": experiencias_data}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"/tmp/backup_{nit}_{timestamp}.json"
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=4, ensure_ascii=False, default=str)

def obtener_experiencias_existentes(id_cliente: int) -> list:
    """Obtiene todas las experiencias del cliente para el backup."""
    response = supabase.table("experiencias").select("*").eq("id_cliente", id_cliente).execute()
    return response.data

def actualizar_cliente_y_experiencias(cliente_id: int, nuevos_datos):
    """Actualiza el cliente y reemplaza sus experiencias."""
    # Actualizar datos del cliente
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
        # 1. Validar que los 4 archivos estén presentes
        file_rut = request.files.get('rut')
        file_camara = request.files.get('camara')
        file_rup = request.files.get('rup')
        file_experiencia = request.files.get('experiencia')
        
        if not all([file_rut, file_camara, file_rup, file_experiencia]):
            return jsonify({"status": "error", "message": "Faltan uno o más archivos requeridos."}), 400

        # 2. Extraer el NIT del nombre del RUT
        rut_filename = secure_filename(file_rut.filename)
        nit_match = rut_filename.split('_')[0]  # Ej: "830070095-1" de "830070095-1_rut.pdf"
        if not nit_match or len(nit_match) < 5:
            return jsonify({"status": "error", "message": "Nombre del RUT inválido. Debe ser {NIT}_rut.pdf"}), 400
        nit = nit_match

        # 3. Guardar archivos temporalmente (solo para simulación futura)
        # NOTA: Esto es placeholder. En versión final, aquí se parsearán los PDF/Excel.
        # Por ahora, usamos datos simulados.

        # 4. DATOS SIMULADOS (reemplazar con lógica de parsing real más adelante)
        datos_simulados = {
            "cliente": {
                "razon_social": f"INSTITUCIÓN EJEMPLO - {nit}",
                "nit": nit,
                "tipo_entidad": "Entidad de prueba",
                "pais": "Colombia",
                "fecha_constitucion": "2000-01-01",
                "rut_url": rut_filename,
                "certificado_existencia_url": secure_filename(file_camara.filename)
            },
            "experiencias": [
                {
                    "nombre_proyecto": "Proyecto de prueba",
                    "entidad_contratante": "Entidad pública",
                    "valor_contrato": 1000000.00,
                    "fecha_inicio": "2023-01-01",
                    "fecha_fin": "2023-12-31",
                    "tipo_experiencia": "RUP"
                }
            ]
        }

        # 5. Lógica de registro/actualización (Sprint 3)
        cliente_existente = cliente_existe(nit)
        if cliente_existente is None:
            # Registrar nuevo cliente
            cliente_resp = supabase.table("clientes").insert(datos_simulados["cliente"]).execute()
            id_cliente = cliente_resp.data[0]["id_cliente"]
            for exp in datos_simulados["experiencias"]:
                exp["id_cliente"] = id_cliente
                supabase.table("experiencias").insert(exp).execute()
            return jsonify({"status": "success", "message": "Institución registrada con éxito."})
        else:
            # Actualizar cliente existente + backup
            experiencias_actuales = obtener_experiencias_existentes(cliente_existente["id_cliente"])
            generar_backup(cliente_existente, experiencias_actuales, nit)
            actualizar_cliente_y_experiencias(cliente_existente["id_cliente"], datos_simulados)
            return jsonify({"status": "success", "message": "Institución actualizada con éxito."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Punto de entrada necesario para Google Cloud Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
