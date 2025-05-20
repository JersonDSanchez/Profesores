from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import csv
import io
import psycopg2
from config import Config
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.config.from_object(Config)

def get_db_connection():
    try:
        conn = Config.get_connection()
        return conn
    except Error as e:
        print(f"Error de conexión a MySQL: {e}")
        return None
    
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('sidebar'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Por favor ingrese usuario y contraseña', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        if not conn:
            flash('Error de conexión a la base de datos', 'error')
            return render_template('login.html')

        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            query = "SELECT * FROM usuarios WHERE nombre_usuario = %s AND contrasena = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()

            if user:
                # Guardamos directamente el tipo de usuario como entero (0 o 1)
                session['username'] = user['nombre_usuario']
                session['user_type'] = user['tipo_usuario']  # Aquí está el cambio importante
                return redirect(url_for('sidebar'))
            else:
                flash('Credenciales incorrectas', 'error')
        except Exception as e:
            print(f"Error en la consulta: {e}")
            flash('Error interno del servidor', 'error')
        finally:
                cursor.close()
                conn.close()

    return render_template('login.html')

@app.route('/sidebar')
def sidebar():
    editar_id = request.args.get('editar_id', type=int)
    filtro_nombre = request.args.get('nombre', '')
    filtro_genero = request.args.get('genero')
    filtro_categoria = request.args.get('categoria')
    filtro_grado = request.args.get('grado')
    filtro_numero_trabajador = request.args.get('numero_trabajador', '')

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
    SELECT p.id_profesor, p.numero_trabajador, p.nombre_completo, g.nombre AS genero,
           p.rfc, p.curp, c.nombre AS categoria, ga.nombre AS grado_academico,
           p.antiguedad_unam, p.antiguedad_carrera, p.correo, p.numero_casa,
           p.numero_celular, p.direccion
    FROM profesores p
    JOIN genero g ON p.fk_id_genero = g.id_genero
    JOIN categoria_profesor c ON p.fk_id_categoria_profesor = c.id_categoria_profesor
    JOIN grado_academico ga ON p.fk_id_grado_academico = ga.id_grado_academico
    WHERE 1=1
    """
    filtros = []
    valores = []

    if filtro_nombre:
        filtros.append("AND p.nombre_completo LIKE %s")
        valores.append(f"%{filtro_nombre}%")

    if filtro_genero:
        filtros.append("AND p.fk_id_genero = %s")
        valores.append(filtro_genero)

    if filtro_categoria:
        filtros.append("AND p.fk_id_categoria_profesor = %s")
        valores.append(filtro_categoria)

    if filtro_grado:
        filtros.append("AND p.fk_id_grado_academico = %s")
        valores.append(filtro_grado)

    if filtro_numero_trabajador:
        filtros.append("AND p.numero_trabajador LIKE %s")
        valores.append(f"%{filtro_numero_trabajador}%")

    query += " ".join(filtros)
    cursor.execute(query, valores)
    profesores = cursor.fetchall()

    # Catálogos
    cursor.execute("SELECT * FROM genero")
    generos = cursor.fetchall()

    cursor.execute("SELECT * FROM categoria_profesor")
    categorias = cursor.fetchall()

    cursor.execute("SELECT * FROM grado_academico")
    grados_academicos = cursor.fetchall()

    profesor_editar = None
    if editar_id:
        cursor.execute("SELECT * FROM profesores WHERE id_profesor = %s", (editar_id,))
        profesor_editar = cursor.fetchone()

    # Datos para gráficas
    cursor.execute("""
        SELECT g.nombre AS etiqueta, COUNT(*) AS cantidad
        FROM profesores p
        JOIN genero g ON p.fk_id_genero = g.id_genero
        GROUP BY g.nombre
    """)
    datos_genero = cursor.fetchall()

    cursor.execute("""
        SELECT c.nombre AS etiqueta, COUNT(*) AS cantidad
        FROM profesores p
        JOIN categoria_profesor c ON p.fk_id_categoria_profesor = c.id_categoria_profesor
        GROUP BY c.nombre
    """)
    datos_categoria = cursor.fetchall()

    cursor.execute("""
        SELECT ga.nombre AS etiqueta, COUNT(*) AS cantidad
        FROM profesores p
        JOIN grado_academico ga ON p.fk_id_grado_academico = ga.id_grado_academico
        GROUP BY ga.nombre
    """)
    datos_grado = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("side-bar.html",
        profesores=profesores,
        generos=generos,
        categorias=categorias,
        grados_academicos=grados_academicos,
        profesor_editar=profesor_editar,
        datos_genero=datos_genero,
        datos_categoria=datos_categoria,
        datos_grado=datos_grado
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Ruta para ver todos los profesores
@app.route('/profesores')
def listar_profesores():
    if 'username' not in session:
        flash('Por favor inicie sesión primero', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    profesores = []
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT p.*, g.nombre AS genero, c.nombre AS categoria, ga.nombre AS grado
                FROM profesor p
                JOIN genero g ON p.fk_id_genero = g.id_genero
                JOIN categoria_profesor c ON p.fk_id_categoria_profesor = c.id_categoria_profesor
                JOIN grado_academico ga ON p.fk_id_grado_academico = ga.id_grado_academico
            """)
            profesores = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    return render_template('profesores/listar_profesores.html', profesores=profesores)

# Ruta para agregar todos los profesores
@app.route('/agregar_profesor', methods=['POST'])
def agregar_profesor():
    numero_trabajador = request.form['numero_trabajador']
    nombre_completo = request.form['nombre_completo']
    fk_id_genero = request.form['fk_id_genero']
    rfc = request.form['rfc']
    curp = request.form['curp']
    fk_id_categoria_profesor = request.form['fk_id_categoria_profesor']
    fk_id_grado_academico = request.form['fk_id_grado_academico']
    antiguedad_unam = request.form['antiguedad_unam']
    antiguedad_carrera = request.form['antiguedad_carrera']
    correo = request.form['correo']
    numero_casa = request.form['numero_casa']
    numero_celular = request.form['numero_celular']
    direccion = request.form['direccion']

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO profesores (
            numero_trabajador, nombre_completo, fk_id_genero, rfc, curp,
            fk_id_categoria_profesor, fk_id_grado_academico, antiguedad_unam,
            antiguedad_carrera, correo, numero_casa, numero_celular, direccion
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    valores = (
        numero_trabajador, nombre_completo, fk_id_genero, rfc, curp,
        fk_id_categoria_profesor, fk_id_grado_academico, antiguedad_unam,
        antiguedad_carrera, correo, numero_casa, numero_celular, direccion
    )
    cursor.execute(query, valores)
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('sidebar'))

# Ruta para editar un profesor
@app.route('/profesores/editar/<int:id>')
def editar_profesor(id):
    conn = get_db_connection()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('sidebar'))

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Obtener profesor por id
        cursor.execute("SELECT * FROM profesores WHERE id_profesor = %s", (id,))
        profesor = cursor.fetchone()

        # Obtener catálogos para los dropdowns
        cursor.execute("SELECT * FROM genero")
        generos = cursor.fetchall()
        cursor.execute("SELECT * FROM categoria_profesor")
        categorias = cursor.fetchall()
        cursor.execute("SELECT * FROM grado_academico")
        grados_academicos = cursor.fetchall()

        return render_template(
            "profesores/editar_profesor.html", 
            profesor=profesor, 
            generos=generos, 
            categorias=categorias, 
            grados_academicos=grados_academicos
        )
    except Exception as e:
        print(f"Error al editar profesor: {e}")
        flash('Error al cargar el formulario de edición', 'danger')
        return redirect(url_for('sidebar'))
    finally:
        cursor.close()
        conn.close()

# Ruta para actualizar profesor
@app.route('/profesores/actualizar/<int:id>', methods=['POST'])
def actualizar_profesor(id):
    conn = get_db_connection()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('sidebar'))

    try:
        datos = (
            request.form['numero_trabajador'],
            request.form['nombre_completo'],
            request.form['fk_id_genero'],
            request.form['rfc'],
            request.form['curp'],
            request.form['fk_id_categoria_profesor'],
            request.form['fk_id_grado_academico'],
            request.form['antiguedad_unam'],
            request.form['antiguedad_carrera'],
            request.form['correo'],
            request.form['numero_casa'],
            request.form['numero_celular'],
            request.form['direccion'],
            id
        )
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE profesores SET
                numero_trabajador = %s,
                nombre_completo = %s,
                fk_id_genero = %s,
                rfc = %s,
                curp = %s,
                fk_id_categoria_profesor = %s,
                fk_id_grado_academico = %s,
                antiguedad_unam = %s,
                antiguedad_carrera = %s,
                correo = %s,
                numero_casa = %s,
                numero_celular = %s,
                direccion = %s
            WHERE id_profesor = %s
        """, datos)
        conn.commit()
        flash('Profesor actualizado correctamente', 'success')
    except Exception as e:
        print(f"Error al actualizar profesor: {e}")
        flash('Error al actualizar profesor', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('sidebar'))

# Ruta para eliminar un profesor
@app.route('/profesores/eliminar/<int:id>')
def eliminar_profesor(id):
    conn = get_db_connection()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('sidebar'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profesores WHERE id_profesor = %s", (id,))
        conn.commit()
        flash('Profesor eliminado correctamente', 'success')
    except Exception as e:
        print(f"Error al eliminar profesor: {e}")
        flash('Error al eliminar profesor', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('sidebar'))

@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    username = request.form.get('username')
    password = request.form.get('password')
    tipo_usuario = request.form.get('tipo_usuario')  # "0" o "1"

    if not username or not password or tipo_usuario is None:
        flash("Por favor completa todos los campos", "danger")
        return redirect(url_for('sidebar'))  # Cambiar a donde corresponda

    try:
        tipo_usuario_int = int(tipo_usuario)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para evitar duplicados (opcional)
        cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s", (username,))
        if cursor.fetchone():
            flash("El nombre de usuario ya existe", "warning")
            cursor.close()
            conn.close()
            return redirect(url_for('sidebar'))

        query = "INSERT INTO usuarios (nombre_usuario, contrasena, tipo_usuario) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, password, tipo_usuario_int))
        conn.commit()

        cursor.close()
        conn.close()

        flash("Usuario agregado correctamente", "success")
        return redirect(url_for('sidebar'))

    except Exception as e:
        flash(f"Error al agregar usuario: {e}", "danger")
        return redirect(url_for('sidebar'))
    
@app.route('/exportar_profesores')
def exportar_profesores():
    filtro_nombre = request.args.get('nombre', '')
    filtro_genero = request.args.get('genero')
    filtro_categoria = request.args.get('categoria')
    filtro_grado = request.args.get('grado')
    filtro_numero_trabajador = request.args.get('numero_trabajador', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT p.id_profesor, p.numero_trabajador, p.nombre_completo, g.nombre AS genero,
           p.rfc, p.curp, c.nombre AS categoria, ga.nombre AS grado_academico,
           p.antiguedad_unam, p.antiguedad_carrera, p.correo, p.numero_casa,
           p.numero_celular, p.direccion
    FROM profesores p
    JOIN genero g ON p.fk_id_genero = g.id_genero
    JOIN categoria_profesor c ON p.fk_id_categoria_profesor = c.id_categoria_profesor
    JOIN grado_academico ga ON p.fk_id_grado_academico = ga.id_grado_academico
    WHERE 1=1
    """
    filtros = []
    valores = []

    if filtro_nombre:
        filtros.append("AND p.nombre_completo LIKE %s")
        valores.append(f"%{filtro_nombre}%")

    if filtro_genero:
        filtros.append("AND p.fk_id_genero = %s")
        valores.append(filtro_genero)

    if filtro_categoria:
        filtros.append("AND p.fk_id_categoria_profesor = %s")
        valores.append(filtro_categoria)

    if filtro_grado:
        filtros.append("AND p.fk_id_grado_academico = %s")
        valores.append(filtro_grado)

    if filtro_numero_trabajador:
        filtros.append("AND p.numero_trabajador LIKE %s")
        valores.append(f"%{filtro_numero_trabajador}%")

    query += " ".join(filtros)
    cursor.execute(query, valores)
    rows = cursor.fetchall()

    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([i[0] for i in cursor.description])  # encabezados
    writer.writerows(rows)

    cursor.close()
    conn.close()

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=profesores.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/profesores/importar', methods=['POST'])
def importar_profesores():
    if session.get('user_type') != 1:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('sidebar'))

    archivo = request.files.get('archivo_csv')
    if not archivo:
        flash('No se seleccionó ningún archivo.', 'warning')
        return redirect(url_for('sidebar'))

    if not archivo.filename.endswith('.csv'):
        flash('Solo se permiten archivos CSV.', 'warning')
        return redirect(url_for('sidebar'))

    try:
        stream = io.StringIO(archivo.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Preparar query de inserción
        query = """
            INSERT INTO profesores (
                numero_trabajador, nombre_completo, fk_id_genero, rfc, curp,
                fk_id_categoria_profesor, fk_id_grado_academico, antiguedad_unam,
                antiguedad_carrera, correo, numero_casa, numero_celular, direccion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        registros_insertados = 0
        for row in csv_reader:
            valores = (
                row['numero_trabajador'],
                row['nombre_completo'],
                row['fk_id_genero'],
                row['rfc'],
                row['curp'],
                row['fk_id_categoria_profesor'],
                row['fk_id_grado_academico'],
                row['antiguedad_unam'],
                row['antiguedad_carrera'],
                row['correo'],
                row['numero_casa'],
                row['numero_celular'],
                row['direccion']
            )
            cursor.execute(query, valores)
            registros_insertados += 1

        conn.commit()
        flash(f'Se importaron {registros_insertados} profesores correctamente.', 'success')
    except Exception as e:
        print(f"Error al importar CSV: {e}")
        flash('Ocurrió un error al importar el archivo.', 'danger')
    finally:
            cursor.close()
            conn.close()

    return redirect(url_for('sidebar'))

@app.route('/graficas')
def graficas():
    if 'username' not in session:
        flash('Por favor inicie sesión primero', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Consulta para contar por género
    cursor.execute("""
        SELECT g.nombre AS categoria, COUNT(*) AS total
        FROM profesores p
        JOIN genero g ON p.fk_id_genero = g.id_genero
        GROUP BY p.fk_id_genero
    """)
    datos_genero = cursor.fetchall()
    
    # Consulta para contar por categoría
    cursor.execute("""
        SELECT c.nombre AS categoria, COUNT(*) AS total
        FROM profesores p
        JOIN categoria_profesor c ON p.fk_id_categoria_profesor = c.id_categoria_profesor
        GROUP BY p.fk_id_categoria_profesor
    """)
    datos_categoria = cursor.fetchall()
    
    # Consulta para contar por grado académico
    cursor.execute("""
        SELECT ga.nombre AS categoria, COUNT(*) AS total
        FROM profesores p
        JOIN grado_academico ga ON p.fk_id_grado_academico = ga.id_grado_academico
        GROUP BY p.fk_id_grado_academico
    """)
    datos_grado = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Enviamos los datos a la plantilla
    return render_template('graficas.html',
                           datos_genero=datos_genero,
                           datos_categoria=datos_categoria,
                           datos_grado=datos_grado)
    
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
