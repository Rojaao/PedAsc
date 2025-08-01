import streamlit as st
import time
import threading
from deriv_bot import DerivBot

st.set_page_config(page_title="Robô Famped", layout="centered")
st.title("🤖 Robô Famped - Estratégia Over 3 baseada em ticks")

token = st.text_input("🎯 Token da Deriv", type="password")
symbol = st.selectbox("Símbolo", ["R_100", "R_10"])
stake = st.number_input("Stake Inicial", min_value=0.01, step=0.01, value=0.75)
use_martingale = st.checkbox("Usar Martingale", value=True)
factor = st.number_input("Fator de Martingale", min_value=1.0, step=0.1, value=2.0)
target_profit = st.number_input("Meta de Lucro", min_value=0.0, value=10.0, step=0.5)
stop_loss = st.number_input("Stop Loss", min_value=0.0, value=10.0, step=0.5)
selected_ticks = st.selectbox("Analisar últimos ticks", [33, 50, 100, 200])
percentual_minimo = st.selectbox("Percentual mínimo <4 para entrada", [40, 65, 70, 80])

if st.button("🚀 Debug: Mostrar Stake Corrente"):
    st.write(f"Stake atual (input): {stake}")

placeholder_logs = st.empty()
placeholder_lucro = st.empty()
placeholder_chart = st.empty()

if "bot" not in st.session_state:
    st.session_state.bot = None
if "running" not in st.session_state:
    st.session_state.running = False

def iniciar_robo():
    bot = DerivBot(
        token=token,
        symbol=symbol,
        stake=stake,
        use_martingale=use_martingale,
        factor=factor,
        target_profit=target_profit,
        stop_loss=stop_loss,
        selected_ticks=selected_ticks,
        percento_entrada=percentual_minimo
    )
    st.write(f"[DEBUG] Criando DerivBot com stake={stake}, use_martingale={use_martingale}")
    st.session_state.bot = bot
    st.session_state.running = True
    threading.Thread(target=bot.run_interface, daemon=True).start()

if not st.session_state.running:
    if st.button("🚀 Iniciar Robô"):
        if not token:
            st.error("Informe o token antes de iniciar")
        else:
            iniciar_robo()
else:
    if st.button("🛑 Parar Robô"):
        st.session_state.bot.running = False
        st.session_state.running = False
        st.success("Robô parado pelo usuário")

if st.session_state.running and st.session_state.bot:
    bot = st.session_state.bot
    for _ in range(1000):
        if not st.session_state.running:
            break
        lucro = bot.lucro_acumulado
        if lucro >= 0:
            placeholder_lucro.success(f"💰 Lucro acumulado: +${lucro:.2f}")
        else:
            placeholder_lucro.error(f"📉 Lucro acumulado: -${abs(lucro):.2f}")
        logs = bot.logs[-12:] if len(bot.logs) >= 12 else bot.logs
        placeholder_logs.text("\n".join(logs) if logs else "Aguardando ticks...")
        if hasattr(bot, "profits") and bot.profits:
            cum = 0.0
            evol = []
            for p in bot.profits:
                cum += p
                evol.append(cum)
            placeholder_chart.line_chart(evol)
        time.sleep(2)
    if st.session_state.running:
        st.session_state.running = False
        st.success("Execução de atualização concluída.")
else:
    if st.session_state.bot and st.session_state.bot.logs:
        placeholder_logs.text("\n".join(st.session_state.bot.logs[-12:]))
    else:
        placeholder_logs.text("Aguardando início do robô...")
    placeholder_lucro.text("")