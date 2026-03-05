/*
* @author Raquel Vega
* @version 1.0
*/
# -*- coding: utf-8 -*-
import simpy
import random
import statistics
import pandas as pd
import matplotlib.pyplot as plt

RANDOM_SEED = 42

def proceso(env, nombre, RAM, CPU, memoria_necesaria, instrucciones, velocidad_cpu, tiempos):
    """Simula el ciclo de vida de un proceso en el sistema operativo."""
    llegada = env.now
    
    # NEW -> READY: Solicitar memoria RAM
    yield RAM.get(memoria_necesaria)
    
    while instrucciones > 0:
        # READY -> RUNNING: Esperar CPU
        with CPU.request() as req:
            yield req
            
            # RUNNING: Ejecutar instrucciones (máximo velocidad_cpu por unidad de tiempo)
            ejecutar = min(instrucciones, velocidad_cpu)
            yield env.timeout(1)  # 1 unidad de tiempo en CPU
            instrucciones -= ejecutar
        
        # Después de usar el CPU
        if instrucciones <= 0:
            # TERMINATED
            break
        else:
            # Generar número al azar entre 1 y 21
            decision = random.randint(1, 21)
            if decision == 1:
                # WAITING (I/O)
                yield env.timeout(1)  # Simula tiempo en I/O
                # Regresa a READY
    
    # TERMINATED: Devolver memoria
    yield RAM.put(memoria_necesaria)
    
    tiempo_total = env.now - llegada
    tiempos.append(tiempo_total)


def generador_procesos(env, num_procesos, intervalo, RAM, CPU, velocidad_cpu, tiempos):
    """Genera procesos con distribución exponencial."""
    for i in range(num_procesos):
        memoria = random.randint(1, 10)
        instrucciones = random.randint(1, 10)
        env.process(proceso(env, f"Proceso_{i}", RAM, CPU, memoria, instrucciones, velocidad_cpu, tiempos))
        yield env.timeout(random.expovariate(1.0 / intervalo))


def correr_simulacion(num_procesos, intervalo, memoria_total, num_cpus, velocidad_cpu, seed=RANDOM_SEED):
    """Ejecuta una simulación con los parámetros dados."""
    random.seed(seed)
    tiempos = []
    
    env = simpy.Environment()
    RAM = simpy.Container(env, init=memoria_total, capacity=memoria_total)
    CPU = simpy.Resource(env, capacity=num_cpus)
    
    env.process(generador_procesos(env, num_procesos, intervalo, RAM, CPU, velocidad_cpu, tiempos))
    env.run()
    
    promedio = statistics.mean(tiempos) if tiempos else 0
    desviacion = statistics.stdev(tiempos) if len(tiempos) > 1 else 0
    
    return promedio, desviacion


# -------------------------------
# Recolección de resultados
# -------------------------------
def recolectar_resultados():
    cantidades = [25, 50, 100, 150, 200]
    registros = []

    # TAREA 1: Configuración base
    for n in cantidades:
        prom, desv = correr_simulacion(n, intervalo=10, memoria_total=100, num_cpus=1, velocidad_cpu=3)
        registros.append({
            "tarea": "T1_base",
            "etiqueta": "Base (int=10, RAM=100, CPU=1, vel=3)",
            "procesos": n, "intervalo": 10, "ram": 100, "cpus": 1, "vel": 3,
            "promedio": prom, "desv": desv
        })

    # TAREA 2: Intervalos más rápidos
    for intervalo in [10, 5, 1]:
        for n in cantidades:
            prom, desv = correr_simulacion(n, intervalo=intervalo, memoria_total=100, num_cpus=1, velocidad_cpu=3)
            registros.append({
                "tarea": "T2_intervalos",
                "etiqueta": f"int={intervalo}",
                "procesos": n, "intervalo": intervalo, "ram": 100, "cpus": 1, "vel": 3,
                "promedio": prom, "desv": desv
            })

    # TAREA 3a: Memoria incrementada a 200
    for intervalo in [10, 5, 1]:
        for n in cantidades:
            prom, desv = correr_simulacion(n, intervalo=intervalo, memoria_total=200, num_cpus=1, velocidad_cpu=3)
            registros.append({
                "tarea": "T3a_ram200",
                "etiqueta": f"int={intervalo}, RAM=200",
                "procesos": n, "intervalo": intervalo, "ram": 200, "cpus": 1, "vel": 3,
                "promedio": prom, "desv": desv
            })

    # TAREA 3b: CPU más rápido (6 instrucciones/ut)
    for intervalo in [10, 5, 1]:
        for n in cantidades:
            prom, desv = correr_simulacion(n, intervalo=intervalo, memoria_total=100, num_cpus=1, velocidad_cpu=6)
            registros.append({
                "tarea": "T3b_cpu6",
                "etiqueta": f"int={intervalo}, vel=6",
                "procesos": n, "intervalo": intervalo, "ram": 100, "cpus": 1, "vel": 6,
                "promedio": prom, "desv": desv
            })

    # TAREA 3c: 2 CPUs (velocidad normal)
    for intervalo in [10, 5, 1]:
        for n in cantidades:
            prom, desv = correr_simulacion(n, intervalo=intervalo, memoria_total=100, num_cpus=2, velocidad_cpu=3)
            registros.append({
                "tarea": "T3c_2cpus",
                "etiqueta": f"int={intervalo}, CPUs=2",
                "procesos": n, "intervalo": intervalo, "ram": 100, "cpus": 2, "vel": 3,
                "promedio": prom, "desv": desv
            })
    return pd.DataFrame(registros)


# -------------------------------
# Gráficas
# -------------------------------
def plot_lineas_por_etiqueta(df, titulo, archivo=None):
    """
    Dibuja promedio vs procesos con barras de error (desv) para cada 'etiqueta' dentro del subconjunto df.
    """
    etiquetas = sorted(df['etiqueta'].unique(), key=lambda s: (len(s), s))
    plt.figure(figsize=(8, 5))
    for et in etiquetas:
        parcial = df[df['etiqueta'] == et].sort_values('procesos')
        plt.errorbar(
            parcial['procesos'], parcial['promedio'], yerr=parcial['desv'],
            marker='o', capsize=4, linewidth=2, label=et
        )
    plt.title(titulo)
    plt.xlabel("Número de procesos")
    plt.ylabel("Tiempo total promedio por proceso")
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend(title="Configuración", frameon=True)
    plt.tight_layout()
    if archivo:
        plt.savefig(archivo, dpi=150)
    plt.show()


def plot_todas(df):
    # TAREA 1
    df_t1 = df[df['tarea'] == 'T1_base']
    plot_lineas_por_etiqueta(df_t1, "Tarea 1: Configuración base", "tarea1_base.png")

    # TAREA 2
    df_t2 = df[df['tarea'] == 'T2_intervalos']
    plot_lineas_por_etiqueta(df_t2, "Tarea 2: Intervalos (más rápidos)", "tarea2_intervalos.png")

    # TAREA 3a
    df_t3a = df[df['tarea'] == 'T3a_ram200']
    plot_lineas_por_etiqueta(df_t3a, "Tarea 3a: RAM incrementada a 200", "tarea3a_ram200.png")

    # TAREA 3b
    df_t3b = df[df['tarea'] == 'T3b_cpu6']
    plot_lineas_por_etiqueta(df_t3b, "Tarea 3b: CPU más rápido (6 instr/ut)", "tarea3b_cpu6.png")

    # TAREA 3c
    df_t3c = df[df['tarea'] == 'T3c_2cpus']
    plot_lineas_por_etiqueta(df_t3c, "Tarea 3c: 2 CPUs (velocidad normal)", "tarea3c_2cpus.png")


def main():
    # Recolecta resultados en un DataFrame
    df = recolectar_resultados()
    # Muestra una vista previa tabular (opcional)
    print(df.head(10).to_string(index=False))
    # Genera y guarda todas las gráficas
    plot_todas(df)


if __name__ == "__main__":

    main()
