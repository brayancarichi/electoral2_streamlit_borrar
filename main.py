'''''
import sqlite3
import pandas as pd
import os


def crear_base_datos_sqlite():
    """Crear base de datos SQLite (no necesita instalación)"""
    # Eliminar si existe para empezar fresco
    if os.path.exists('elecciones_nl_2021.db'):
        os.remove('elecciones_nl_2021.db')

    conn = sqlite3.connect('elecciones_nl_2021.db')
    cur = conn.cursor()

    # Crear tabla
    cur.execute("""
        CREATE TABLE resultados_electorales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato_id VARCHAR(100) UNIQUE NOT NULL,
            anno INTEGER NOT NULL,
            nombre_candidato VARCHAR(300) NOT NULL,
            numero_de_votos INTEGER,
            division_territorial VARCHAR(150),
            nombre_normalizado VARCHAR(300),
            partido_ci VARCHAR(150),
            tipo_eleccion VARCHAR(20) NOT NULL CHECK (tipo_eleccion IN ('MUNICIPAL', 'DIPUTADO', 'GOBERNADOR')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Crear índices
    cur.execute("CREATE INDEX idx_tipo_eleccion ON resultados_electorales(tipo_eleccion)")
    cur.execute("CREATE INDEX idx_partido ON resultados_electorales(partido_ci)")
    cur.execute("CREATE INDEX idx_division ON resultados_electorales(division_territorial)")

    conn.commit()
    conn.close()
    print("✅ Base de datos SQLite creada: elecciones_nl_2021.db")


def cargar_datos_sqlite():
    """Cargar datos a SQLite"""
    conn = sqlite3.connect('elecciones_nl_2021.db')

    archivos = {
        'candidatos_ayuntamientos_con_id_anno_2021.csv': 'MUNICIPAL',
        'candidatos_diputaciones_con_id_2021.csv': 'DIPUTADO',
        'candidatos_gobernador_con_id_anno_2021.csv': 'GOBERNADOR'
    }

    for archivo, tipo_eleccion in archivos.items():
        if os.path.exists(archivo):
            df = pd.read_csv(archivo)
            print(f"📖 Cargando {archivo}: {len(df)} registros")

            # Estandarizar columnas
            if 'municipio' in df.columns:
                df.rename(columns={'municipio': 'division_territorial'}, inplace=True)
            elif 'distrito' in df.columns:
                df.rename(columns={'distrito': 'division_territorial'}, inplace=True)
            elif 'nombre_distrito' in df.columns:
                df.rename(columns={'nombre_distrito': 'division_territorial'}, inplace=True)

            # Limpiar votos
            df['numero_de_votos'] = df['numero_de_votos'].astype(str).str.replace(',', '').astype(int)
            df['tipo_eleccion'] = tipo_eleccion

            # Insertar datos
            df.to_sql('resultados_electorales', conn, if_exists='append', index=False)
            print(f"✅ {archivo} cargado: {len(df)} registros")
        else:
            print(f"⚠️ Archivo {archivo} no encontrado")

    conn.close()


def consultas_sqlite():
    """Ejecutar consultas en SQLite"""
    conn = sqlite3.connect('elecciones_nl_2021.db')

    consultas = {
        'Total por tipo de elección': """
            SELECT tipo_eleccion, COUNT(*) as candidatos, SUM(numero_de_votos) as total_votos
            FROM resultados_electorales 
            GROUP BY tipo_eleccion ORDER BY total_votos DESC;
        """,

        'Top 10 candidatos': """
            SELECT tipo_eleccion, nombre_candidato, partido_ci, numero_de_votos
            FROM resultados_electorales 
            ORDER BY numero_de_votos DESC LIMIT 10;
        """
    }

    for nombre, consulta in consultas.items():
        print(f"\n🔍 {nombre}:")
        print("-" * 50)
        df = pd.read_sql_query(consulta, conn)
        print(df)

    conn.close()


# EJECUCIÓN COMPLETA
print("🚀 INICIANDO PROCESO CON SQLite...")
crear_base_datos_sqlite()
cargar_datos_sqlite()
consultas_sqlite()
print("\n🎯 PROCESO COMPLETADO!")
print("📊 Base de datos creada: elecciones_nl_2021.db")

'''''

import sqlite3
import pandas as pd
import os


def crear_base_datos_sqlite():
    """Crear base de datos SQLite (no necesita instalación)"""
    # Cambiar el nombre a 2024
    if os.path.exists('elecciones_nl_2024.db'):
        os.remove('elecciones_nl_2024.db')

    conn = sqlite3.connect('elecciones_nl_2024.db')
    cur = conn.cursor()

    # Crear tabla
    cur.execute("""
        CREATE TABLE resultados_electorales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            casilla_id VARCHAR(100) NOT NULL,
            anno INTEGER NOT NULL,
            nombre_candidato VARCHAR(300) NOT NULL,
            numero_de_votos INTEGER,
            division_territorial VARCHAR(150),
            nombre_normalizado VARCHAR(300),
            partido_ci VARCHAR(150),
            tipo_eleccion VARCHAR(20) NOT NULL CHECK (tipo_eleccion IN ('MUNICIPAL', 'DIPUTADO', 'GOBERNADOR')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Crear índices
    cur.execute("CREATE INDEX idx_tipo_eleccion ON resultados_electorales(tipo_eleccion)")
    cur.execute("CREATE INDEX idx_partido ON resultados_electorales(partido_ci)")
    cur.execute("CREATE INDEX idx_division ON resultados_electorales(division_territorial)")
    cur.execute("CREATE INDEX idx_casilla_id ON resultados_electorales(casilla_id)")

    conn.commit()
    conn.close()
    print("✅ Base de datos SQLite creada: elecciones_nl_2024.db")


def cargar_datos_sqlite():
    """Cargar datos a SQLite"""
    conn = sqlite3.connect('elecciones_nl_2024.db')

    archivos = {
        '/Users/brayanalfredomurillogutierrez/Desktop/TRABAJO/Base_datos_electoral/Informacion/Modificada/2024/Ayuntamientos/ayuntamientos_con_id_anno_2024.csv': 'MUNICIPAL',
        '/Users/brayanalfredomurillogutierrez/Desktop/TRABAJO/Base_datos_electoral/Informacion/Modificada/2024/Diputaciones/diputaciones_con_id_anno_2024.csv': 'DIPUTADO'
        # Agregar 'gobernador_con_id_anno_2024.csv' si tienes ese archivo
    }

    for archivo, tipo_eleccion in archivos.items():
        if os.path.exists(archivo):
            df = pd.read_csv(archivo)
            print(f"📖 Cargando {archivo}: {len(df)} registros")

            # Estandarizar columnas - usar 'casilla_id' en lugar de 'candidato_id'
            if 'municipio' in df.columns:
                df.rename(columns={'municipio': 'division_territorial'}, inplace=True)
            elif 'distrito' in df.columns:
                df.rename(columns={'distrito': 'division_territorial'}, inplace=True)

            # Limpiar votos - manejar valores como "1,132" y "Registro cancelado"
            def limpiar_votos(voto):
                if isinstance(voto, str):
                    if voto.replace(',', '').isdigit():
                        return int(voto.replace(',', ''))
                    elif 'Registro cancelado' in voto:
                        return 0
                    else:
                        # Intentar extraer números de strings como "1,132"
                        try:
                            return int(voto.replace(',', ''))
                        except:
                            return 0
                elif pd.isna(voto):
                    return 0
                else:
                    return int(voto)

            df['numero_de_votos'] = df['numero_de_votos'].apply(limpiar_votos)
            df['tipo_eleccion'] = tipo_eleccion

            # Insertar datos
            df.to_sql('resultados_electorales', conn, if_exists='append', index=False)
            print(f"✅ {archivo} cargado: {len(df)} registros")
        else:
            print(f"⚠️ Archivo {archivo} no encontrado")

    conn.close()


def consultas_sqlite():
    """Ejecutar consultas en SQLite"""
    conn = sqlite3.connect('elecciones_nl_2024.db')

    consultas = {
        'Total por tipo de elección': """
            SELECT tipo_eleccion, COUNT(*) as candidatos, SUM(numero_de_votos) as total_votos
            FROM resultados_electorales 
            GROUP BY tipo_eleccion ORDER BY total_votos DESC;
        """,

        'Top 10 candidatos más votados': """
            SELECT tipo_eleccion, nombre_candidato, partido_ci, division_territorial, numero_de_votos
            FROM resultados_electorales 
            ORDER BY numero_de_votos DESC LIMIT 10;
        """,

        'Partidos con más votos totales': """
            SELECT partido_ci, SUM(numero_de_votos) as total_votos, COUNT(*) as candidatos
            FROM resultados_electorales 
            GROUP BY partido_ci 
            ORDER BY total_votos DESC;
        """,

        'Resultados por municipio (elecciones municipales)': """
            SELECT division_territorial, COUNT(*) as candidatos, SUM(numero_de_votos) as total_votos
            FROM resultados_electorales 
            WHERE tipo_eleccion = 'MUNICIPAL'
            GROUP BY division_territorial 
            ORDER BY total_votos DESC
            LIMIT 15;
        """,

        'Resultados por distrito (elecciones de diputados)': """
            SELECT division_territorial, COUNT(*) as candidatos, SUM(numero_de_votos) as total_votos
            FROM resultados_electorales 
            WHERE tipo_eleccion = 'DIPUTADO'
            GROUP BY division_territorial 
            ORDER BY total_votos DESC;
        """
    }

    for nombre, consulta in consultas.items():
        print(f"\n🔍 {nombre}:")
        print("-" * 80)
        df = pd.read_sql_query(consulta, conn)
        print(df.to_string(index=False))

    conn.close()


def consultas_avanzadas():
    """Consultas más específicas sobre los datos"""
    conn = sqlite3.connect('elecciones_nl_2024.db')

    print("\n📊 ANÁLISIS AVANZADO:")
    print("=" * 80)

    # Ganadores por municipio
    print("\n🏆 GANADORES POR MUNICIPIO (Elecciones Municipales):")
    ganadores_municipio = """
        WITH ranked_candidates AS (
            SELECT 
                division_territorial,
                nombre_candidato,
                partido_ci,
                numero_de_votos,
                ROW_NUMBER() OVER (PARTITION BY division_territorial ORDER BY numero_de_votos DESC) as rank
            FROM resultados_electorales 
            WHERE tipo_eleccion = 'MUNICIPAL'
        )
        SELECT division_territorial as municipio, nombre_candidato, partido_ci, numero_de_votos
        FROM ranked_candidates 
        WHERE rank = 1
        ORDER BY numero_de_votos DESC
        LIMIT 20;
    """
    df_ganadores = pd.read_sql_query(ganadores_municipio, conn)
    print(df_ganadores.to_string(index=False))

    # Ganadores por distrito (diputados)
    print("\n🏆 GANADORES POR DISTRITO (Elecciones de Diputados):")
    ganadores_distrito = """
        WITH ranked_candidates AS (
            SELECT 
                division_territorial,
                nombre_candidato,
                partido_ci,
                numero_de_votos,
                ROW_NUMBER() OVER (PARTITION BY division_territorial ORDER BY numero_de_votos DESC) as rank
            FROM resultados_electorales 
            WHERE tipo_eleccion = 'DIPUTADO'
        )
        SELECT division_territorial as distrito, nombre_candidato, partido_ci, numero_de_votos
        FROM ranked_candidates 
        WHERE rank = 1
        ORDER BY numero_de_votos DESC;
    """
    df_ganadores_distrito = pd.read_sql_query(ganadores_distrito, conn)
    print(df_ganadores_distrito.to_string(index=False))

    # Partidos dominantes por tipo de elección
    print("\n📈 PARTIDOS DOMINANTES POR TIPO DE ELECCIÓN:")
    partidos_dominantes = """
        SELECT 
            tipo_eleccion,
            partido_ci,
            COUNT(*) as candidatos_presentados,
            SUM(numero_de_votos) as total_votos,
            ROUND(AVG(numero_de_votos), 2) as promedio_votos_por_candidato
        FROM resultados_electorales 
        GROUP BY tipo_eleccion, partido_ci
        ORDER BY tipo_eleccion, total_votos DESC;
    """
    df_partidos = pd.read_sql_query(partidos_dominantes, conn)
    print(df_partidos.to_string(index=False))

    conn.close()


# EJECUCIÓN COMPLETA
print("🚀 INICIANDO PROCESO CON SQLite - ELECCIONES 2024...")
crear_base_datos_sqlite()
cargar_datos_sqlite()
consultas_sqlite()
consultas_avanzadas()
print("\n🎯 PROCESO COMPLETADO!")
print("📊 Base de datos creada: elecciones_nl_2024.db")
print("💾 Archivos procesados:")
print("   - ayuntamientos_con_id_anno_2024.csv")
print("   - diputaciones_con_id_anno_2024.csv")