from flask import Flask, request, render_template, send_file
import barcode
from barcode.writer import ImageWriter
import csv
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)

# Configuración de la base de datos PostgreSQL
DB_CONFIG = {
    "dbname": "rifa_db",
    "user": "rifa",
    "password": "rifa_puertas_abiertas",
    "host": "localhost",
    "port": "5432"
}

# Archivo CSV para almacenar los códigos
data_file = "codigos_registrados.csv"
if not os.path.exists(data_file):
    with open(data_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Carnet", "Codigo", "Fecha"])

# Crear tabla en PostgreSQL si no existe
def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS codigos (
            id SERIAL PRIMARY KEY,
            carnet VARCHAR(50) UNIQUE NOT NULL,
            codigo VARCHAR(50) NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        carnet = request.form.get("carnet")
        if not carnet:
            return "Error: Debe ingresar un número de carnet", 400

        # Generar código de barras
        code128 = barcode.get_barcode_class("code128")
        barcode_instance = code128(carnet, writer=ImageWriter())
        barcode_path = f"static/barcodes/{carnet}.png"
        barcode_instance.save(barcode_path)

        # Guardar en CSV
        with open(data_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([carnet, carnet, datetime.now()])

        # Guardar en PostgreSQL
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("INSERT INTO codigos (carnet, codigo) VALUES (%s, %s) ON CONFLICT (carnet) DO NOTHING", (carnet, carnet))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("Error al guardar en la base de datos:", e)

        return render_template("resultado.html", carnet=carnet, barcode_path=barcode_path)

    return render_template("index.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
