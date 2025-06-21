
def analisar_ticks_famped(ultimos_digitos, porcentagem_minima=65):
    total = len(ultimos_digitos)
    abaixo_de_4 = [d for d in ultimos_digitos if d < 4]
    porcentagem = (len(abaixo_de_4) / total) * 100

    if porcentagem >= porcentagem_minima:
        return {
            "entrada": "OVER 3",
            "estrategia": f"FAMPED ({round(porcentagem)}% < 4)"
        }
    else:
        return {
            "entrada": "ESPERAR",
            "estrategia": f"FAMPED ({round(porcentagem)}% < 4 - aguardando)"
        }
