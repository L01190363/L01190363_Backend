"""
ws_directorio.py  ·  Proyecto Integrador (Sesión 5)
Backend REST: Directorio de Materias y Docentes
Flask + mysql-connector-python + flask-cors
"""

import os
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite que el frontend (otro puerto/origen) consuma la API

# ------------------------------------------------------------
#  Configuración de conexión
#  Usa variables de entorno con valores por defecto que coinciden
#  con el contenedor MySQL de la guía de arranque rápido.
# ------------------------------------------------------------
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "contrasena"),
    "database": os.getenv("DB_NAME", "directorio"),
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
#  MATERIAS
# ============================================================

@app.get("/materias")
def listar_materias():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM materias ORDER BY id")
    filas = cur.fetchall()
    cur.close(); db.close()
    return jsonify(filas)


@app.get("/materias/<int:id>")
def obtener_materia(id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM materias WHERE id = %s", (id,))
    fila = cur.fetchone()
    cur.close(); db.close()
    if fila is None:
        return jsonify({"error": "Materia no encontrada"}), 404
    return jsonify(fila)


@app.post("/materias")
def crear_materia():
    data = request.get_json(silent=True) or {}
    clave    = data.get("clave")
    nombre   = data.get("nombre")
    creditos = data.get("creditos")

    if not clave or not nombre:
        return jsonify({"error": "clave y nombre son obligatorios"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            "INSERT INTO materias (clave, nombre, creditos) VALUES (%s, %s, %s)",
            (clave, nombre, creditos),
        )
        db.commit()
        cur.execute("SELECT * FROM materias WHERE id = %s", (cur.lastrowid,))
        return jsonify(cur.fetchone()), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": f"La clave '{clave}' ya existe"}), 409
    finally:
        cur.close(); db.close()


@app.put("/materias/<int:id>")
def actualizar_materia(id):
    data = request.get_json(silent=True) or {}
    clave    = data.get("clave")
    nombre   = data.get("nombre")
    creditos = data.get("creditos")

    if not clave or not nombre:
        return jsonify({"error": "clave y nombre son obligatorios"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM materias WHERE id = %s", (id,))
        if cur.fetchone() is None:
            return jsonify({"error": "Materia no encontrada"}), 404

        cur.execute(
            "UPDATE materias SET clave = %s, nombre = %s, creditos = %s WHERE id = %s",
            (clave, nombre, creditos, id),
        )
        db.commit()
        cur.execute("SELECT * FROM materias WHERE id = %s", (id,))
        return jsonify(cur.fetchone())
    except mysql.connector.IntegrityError:
        return jsonify({"error": f"La clave '{clave}' ya existe"}), 409
    finally:
        cur.close(); db.close()


@app.delete("/materias/<int:id>")
def eliminar_materia(id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM materias WHERE id = %s", (id,))
        if cur.fetchone() is None:
            return jsonify({"error": "Materia no encontrada"}), 404

        cur.execute("DELETE FROM materias WHERE id = %s", (id,))
        db.commit()
        return "", 204  # No Content
    except mysql.connector.IntegrityError:
        # La FK con RESTRICT bloquea el borrado si hay docentes asignados
        return jsonify({
            "error": "No se puede eliminar: hay docentes asignados a esta materia"
        }), 409
    finally:
        cur.close(); db.close()


# ============================================================
#  DOCENTES
# ============================================================

@app.get("/docentes")
def listar_docentes():
    db = get_db()
    cur = db.cursor(dictionary=True)
    # LEFT JOIN para traer también el nombre de la materia asignada
    cur.execute("""
        SELECT d.id, d.nombre, d.email, d.materia_id,
               m.nombre AS materia_nombre
        FROM docentes d
        LEFT JOIN materias m ON d.materia_id = m.id
        ORDER BY d.id
    """)
    filas = cur.fetchall()
    cur.close(); db.close()
    return jsonify(filas)


@app.post("/docentes")
def crear_docente():
    data = request.get_json(silent=True) or {}
    nombre     = data.get("nombre")
    email      = data.get("email")
    materia_id = data.get("materia_id")

    if not nombre or not email:
        return jsonify({"error": "nombre y email son obligatorios"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        # Validación de integridad referencial manual:
        # si mandan materia_id, comprobamos que exista antes de insertar.
        if materia_id is not None:
            cur.execute("SELECT id FROM materias WHERE id = %s", (materia_id,))
            if cur.fetchone() is None:
                return jsonify({"error": f"La materia_id {materia_id} no existe"}), 400

        cur.execute(
            "INSERT INTO docentes (nombre, email, materia_id) VALUES (%s, %s, %s)",
            (nombre, email, materia_id),
        )
        db.commit()
        cur.execute("SELECT * FROM docentes WHERE id = %s", (cur.lastrowid,))
        return jsonify(cur.fetchone()), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": f"El email '{email}' ya está registrado"}), 409
    finally:
        cur.close(); db.close()


@app.delete("/docentes/<int:id>")
def eliminar_docente(id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id FROM docentes WHERE id = %s", (id,))
    if cur.fetchone() is None:
        cur.close(); db.close()
        return jsonify({"error": "Docente no encontrado"}), 404

    cur.execute("DELETE FROM docentes WHERE id = %s", (id,))
    db.commit()
    cur.close(); db.close()
    return "", 204  # No Content


# ============================================================
#  Arranque
# ============================================================
if __name__ == "__main__":
    # host 0.0.0.0 para que el puerto sea accesible desde el Codespace
    app.run(host="0.0.0.0", port=5000, debug=True)
