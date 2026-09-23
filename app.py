from flask import Flask, request, send_file, send_from_directory
from flask import render_template
import models
import excel
import logging
import traceback
from logging.handlers import RotatingFileHandler
import os, time
from pathlib import Path
import io
import tracemalloc
import subprocess
from werkzeug.middleware.proxy_fix import ProxyFix

tracemalloc.start()

logging.basicConfig(
    filename='./log/errores.log',
    level=logging.ERROR,
    format='%(asctime)s - %(message)s'
)

handler = RotatingFileHandler('./log/errores.log', maxBytes=5*1024*1024, backupCount=3)
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.ERROR)

EXTENSIONES_PERMITIDAS = {".xlsx", ".xls"}
OUTPUT_DIR = os.path.abspath("output")

def extension_valida(filename):
    return os.path.splitext(filename)[1].lower() in EXTENSIONES_PERMITIDAS

def pesos(valor):
    valor = valor or 0
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # tamaño maximo subida de archivo 50 MB
app.jinja_env.filters['pesos'] = pesos
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_for=1, x_host=1, x_prefix=1)

def memoria():
    current, peak = tracemalloc.get_traced_memory()

    return (
        f"RAM tracemalloc: "
        f"{current / 1024**2:.1f} MB | "
        f"pico: {peak / 1024**2:.1f} MB"
    )

FILAS_POR_HOJA = 35
FILAS_COSTO = 10
FILAS_COMPOSICION = 10

def paginar_sueldo(conceptos):
    """
    chunk, es_primera, es_ultima_sueldo, mostrar_footer, solo_composicion
    """
    total = len(conceptos)
    paginas = []
    idx = 0
    es_primera = True

    while idx < total:
        capacidad = FILAS_POR_HOJA - FILAS_COSTO if es_primera else FILAS_POR_HOJA
        restante = total - idx

        if restante <= capacidad:
            chunk = conceptos[idx: idx + restante]
            mostrar_footer = (capacidad - restante) >= FILAS_COMPOSICION
            paginas.append({
                "chunk": chunk, "es_primera": es_primera,
                "es_ultima_sueldo": True, "mostrar_footer": mostrar_footer,
                "solo_composicion": False,
            })
            idx += restante
        else:
            chunk = conceptos[idx: idx + capacidad]
            paginas.append({
                "chunk": chunk, "es_primera": es_primera,
                "es_ultima_sueldo": False, "mostrar_footer": False,
                "solo_composicion": False,
            })
            idx += capacidad

        es_primera = False

    if not paginas:
        paginas.append({
            "chunk": [], "es_primera": True, "es_ultima_sueldo": True,
            "mostrar_footer": (FILAS_POR_HOJA - FILAS_COSTO) >= FILAS_COMPOSICION,
            "solo_composicion": False,
        })

    if not paginas[-1]["mostrar_footer"]:
        paginas.append({
            "chunk": [], "es_primera": False, "es_ultima_sueldo": False,
            "mostrar_footer": True, "solo_composicion": True,
        })

    return paginas

@app.get("/")
def index():
    return render_template("index.html")

@app.route('/debug-headers')
def debug_headers():
    return {
        'X-Forwarded-Proto': request.headers.get('X-Forwarded-Proto'),
        'X-Forwarded-Host': request.headers.get('X-Forwarded-Host'),
        'request.scheme': request.scheme,
        'request.url_root': request.url_root,
    }


@app.get("/upload")
def upload_get():
    message = "Metodo invalido"
    return render_template("error.html", message = message), 400

@app.post("/upload")
def upload():
    print("upload: inicio", memoria())
    limpiar_html_previo()
    archivo = request.files.get("archivo")

    if archivo is None:
        message = "Seleccione un archivo"
        return render_template("error.html", message = message), 400

    if archivo.filename == "":
        message = "Seleccione un archivo valido"
        return render_template("error.html", message = message), 400

    if not extension_valida(archivo.filename):
        message = "El archivo debe ser xls, xlsx"
        return render_template("error.html", message = message), 400
    
    t0 = time.perf_counter()

    try:
        raw = excel.load_data(archivo)
    except Exception:
        logging.error(f"Error leyendo el Excel subido ({archivo.filename}):\n{traceback.format_exc()}")
        message = "El archivo no pudo ser leído. Verificá que sea un Excel válido."
        return render_template("error.html", message = message), 400

    t_excel = time.perf_counter()
    nombres_recibos = []
    recibos_con_error = []

    empresa = models.Empresa()

    t1 = time.perf_counter()
    try:
        empleados = excel.group_data(raw)
    except Exception:
        logging.error(f"Error procesando el Excel subido ({archivo.filename}):\n{traceback.format_exc()}")
        message = "El archivo no pudo ser procesado. Verificá los campos."
        return render_template("error.html", message = message), 400
    del raw
    t_group = time.perf_counter()

    t_avg_conceptos = []

    for e in empleados:
        try:
            t3 = time.perf_counter()
            empleado = models.Empleado(e)
            costo = models.Costo_empleador()
            costo.agregar(e["conceptos"])
            sueldo = models.Sueldo_bruto_empleado()
            sueldo.agregar(e["conceptos"])
            paginas = paginar_sueldo(sueldo.conceptos)
            recibo = models.Recibo(empresa, empleado, costo, sueldo, paginas)

            nombre_archivo = f"output/recibo_{e["legajo"]}.html"
            nombres_recibos.append({
                    "ruta" : nombre_archivo,
                    "legajo" : e["legajo"],
                    "nombre" : e["nombre"],
                    "cuil" : e["cuil"],
                    "tipo_liquidacion" : e["tipo_liquidacion"]
                })

            with open(nombre_archivo, "w", encoding="utf-8") as f:
                f.write(render_template("recibo.html", recibos=[recibo]))
            t_recibo = time.perf_counter()
            
            t_avg_conceptos.append((t_recibo - t3))
            print("upload: nuevo recibo", memoria())

            del empleado
            del costo
            del sueldo
            del recibo

        except Exception:
            legajo = e.get("legajo", "desconocido")
            recibos_con_error.append({
                "legajo": legajo,
                "error": traceback.format_exc()
            })
            logging.error(f"Error procesando legajo {legajo}:\n{traceback.format_exc()}")

    t_global = time.perf_counter()

    stats = {
        "recibos": len(nombres_recibos),
        "recibos_con_error": len(recibos_con_error),
        "carga_de_excel": round(t_excel - t0, 3),
        "procesamiento_de_excel": round(t_group - t1, 3),
        "procesamiento_de_recibo_promedio": round(sum(t_avg_conceptos)/len(t_avg_conceptos), 3),
        "procesamiento_total": round(t_global - t0, 3),
    }

    print(f"upload: fin", memoria())
    

    return render_template("generador.html", nombres_recibos=nombres_recibos, stats=stats)

@app.route("/output/<path:filename>")
def output_files(filename):
    return send_from_directory(OUTPUT_DIR, filename)

def limpiar_html_previo():
    print("limpiar_html_previo: inicio ", memoria())
    output_dir = Path("output").resolve()
    archivos_html = sorted(output_dir.glob("*.html"))
    if not archivos_html:
        print("limpiar_html_previo: fin ", memoria())
        return
    else:
        try:
            for archivo_html in archivos_html:
                archivo_html.unlink()
            print("limpiar_html_previo: fin ", memoria())
            return
        except OSError as e:
            logging.error(f"Error al limpiar recibos previos: ({e}):\n{traceback.format_exc()}")


@app.get("/convert")
def convert():
    print("convert: inicio ", memoria())
    output_dir = Path("output").resolve()
    pdf_dir = output_dir / "pdf_temp"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    archivos_html = sorted(output_dir.glob("*.html"))

    if not archivos_html:
        message = "No hay recibos pendientes de conversion"
        return render_template("error.html", message = message), 400

    # HTML → PDF
    for i, archivo_html in enumerate(archivos_html, 1):

        pdf_path = pdf_dir / f"{archivo_html.stem}.pdf"

        print(f"PDF {i}/{len(archivos_html)}: {archivo_html.name}")

        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}",
                archivo_html.as_uri(),
            ],
            check=True,
        )

        archivo_html.unlink()
    print("convert: pdfs listos ", memoria())

    # PDF → PDF final
    archivos_pdf = sorted(pdf_dir.glob("*.pdf"))

    pdf_final = output_dir / "recibos.pdf"

    subprocess.run(
        [
            r"c:\Program Files\qpdf 12.4.1\bin\qpdf.exe",
            "--empty",
            "--pages",
            *map(str, archivos_pdf),
            "--",
            str(pdf_final),
        ],
        check=True,
    )
    print("convert: pdf final listo ", memoria())

    # Limpiar PDFs temporales
    for archivo_pdf in archivos_pdf:
        archivo_pdf.unlink()

    pdf_dir.rmdir()

    pdf_bytes = pdf_final.read_bytes()
    pdf_final.unlink()

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="recibos.pdf",
    )