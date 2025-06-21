
import matplotlib.pyplot as plt

def plot_resultados(resultados):
    fig, ax = plt.subplots()
    lucro_acumulado = [sum(resultados[:i+1]) for i in range(len(resultados))]
    ax.plot(lucro_acumulado, marker='o')
    ax.set_title("Histórico de Lucros")
    ax.set_ylabel("Lucro acumulado")
    ax.set_xlabel("Entradas")
    return fig
