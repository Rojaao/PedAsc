import streamlit as st
import time
import threading
from deriv_bot import DerivBot

st.set_page_config(page_title="Robô Famped", layout="centered")
st.title("🤖 Robô Famped - Estratégia Over 3 baseada em ticks")

if "log_status" not in st.session_state:
    st.session_state.log_status = "🔄 Iniciando robô..."

if "logs" not in st.session_state:
    st.session_state.logs = []

# Campos da interface
token = st.text_input("🔑 Token da Deriv", type="password")
symbol = st.selectbox("Símbolo", ["R_100", "R_10"])
stake = st.number_input("💰 Stake Inicial", value=0.35, step=0.01)
use_martingale = st.checkbox("🎯 Ativar Martingale")
factor = st.number_input("📈 Fator Martingale", value=2.0, step=0.1)
target_profit = st.number_input("🏆 Meta de Lucro", value=5.0)
stop_loss = st.number_input("🛑 Limite de Perda", value=5.0)
selected_ticks = st.selectbox("📊 Analisar últimos Ticks", [33, 50, 100, 200])
percento = st.selectbox("📌 Porcentagem mínima de acerto para entrar", [40, 65, 70, 80])

log_area = st.empty()

if st.button("▶️ Iniciar Robô"):
    st.session_state.logs.append("🔄 Robô iniciado...")

    bot = DerivBot(
        token=token,
        symbol=symbol,
        stake=stake,
        use_martingale=use_martingale,
        factor=factor,
        target_profit=target_profit,
        stop_loss=stop_loss,
        selected_ticks=selected_ticks,
        percento_entrada=percento
    )

    # Armazena a referência do bot na sessão
    st.session_state.bot = bot

    # Inicia thread
    threading.Thread(target=bot.run_interface, daemon=True).start()

    # Loop para exibir logs dinamicamente na interface
    for _ in range(3000):  # tempo ~2h de execução
        if hasattr(bot, "logs"):
            st.session_state.logs = bot.logs
            log_area.text("\n".join(st.session_state.logs[-12:]))
    # Mostrar lucro acumulado em verde ou vermelho
    lucro = bot.lucro_acumulado if hasattr(bot, "lucro_acumulado") else 0
    if lucro >= 0:
        st.success(f"💰 Lucro acumulado: +${lucro:.2f}")
    else:
        st.error(f"💸 Lucro acumulado: -${abs(lucro):.2f}")

        
    # Histórico de operações com horário
    if hasattr(bot, "resultados"):
        st.subheader("📜 Histórico de Operações")
        for entrada in reversed(bot.resultados[-20:]):
            hora, resultado, stake_usado = entrada
            cor = "✅" if resultado == "WIN" else "❌"
            st.write(f"{cor} {hora} — Resultado: {resultado} — Stake: ${stake_usado:.2f}")

        time.sleep(2)