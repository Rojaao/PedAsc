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

with st.sidebar:
    token = st.text_input("🎯 Token da API", type="password")
    symbol = st.selectbox("Símbolo", ["R_100", "R_10"])
    stake = st.number_input("💵 Stake inicial", min_value=0.35, value=0.35, step=0.01)
    use_martingale = st.checkbox("🎲 Usar Martingale", value=True)
    factor = st.number_input("🔁 Fator Martingale", min_value=1.0, value=2.0, step=0.1)
    target_profit = st.number_input("🎯 Meta de Lucro", value=5.0, step=0.5)
    stop_loss = st.number_input("⛔ Limite de Perda", value=5.0, step=0.5)
    selected_ticks = st.selectbox("📈 Analisar últimos N ticks", [33, 50, 100, 200])
    percento_entrada = st.selectbox("🎯 Critério para entrada (<4)", [40, 65, 70, 80])

if st.button("🚀 Iniciar Robô"):
    stframe = st.empty()
        log_area = st.empty()

        bot = DerivBot(token, symbol, stake, use_martingale, factor, target_profit, stop_loss, selected_ticks, percento_entrada)

    def atualizar_status():
        while True:
            if hasattr(bot, "logs"):
                st.session_state.logs = bot.logs[-100:]
            if hasattr(bot, "lucro_acumulado"):
                lucro = bot.lucro_acumulado
                if lucro >= 0:
                    st.empty().success(f"💰 Lucro acumulado: +${lucro:.2f}")
                else:
                    st.empty().error(f"💸 Lucro acumulado: -${abs(lucro):.2f}")
            log_area.text("\n".join(st.session_state.logs[-12:]))
            time.sleep(2)

    threading.Thread(target=atualizar_status, daemon=True).start()
    threading.Thread(target=bot.receber_ticks, daemon=True).start()
    threading.Thread(target=bot.run_interface, daemon=True).start()

    st.subheader("📜 Histórico de Operações")
    st.write("As últimas entradas aparecerão abaixo...")
