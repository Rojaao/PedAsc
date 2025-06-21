
def analisar_ticks_famped(ultimos_digitos):
    # Cálculo de porcentagem de números abaixo de 4
    total = len(ultimos_digitos)
    abaixo_de_4 = [d for d in ultimos_digitos if d < 4]
    porcentagem = (len(abaixo_de_4) / total) * 100

    if porcentagem >= 65:
        return {
            "entrada": "OVER 3",
            "estrategia": "FAMPED (>=65% abaixo de 4)"
        }
    else:
        return {
            "entrada": "ESPERAR",
            "estrategia": "FAMPED (aguardando padrão)"
        }
