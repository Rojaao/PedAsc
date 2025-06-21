import streamlit as st
import time
import threading
from deriv_bot import DerivBot

# Configurações da página
st.set_page_config(page_title="Robô Famped", layout="centered")
st.title("🤖 Robô Famped - Estratégia Over 3 baseada em ticks")

# Campos de entrada
token = st.text_input("🎯 Token da Deriv", type="password")
symbol = st.selectbox("Símbolo", ["R_100", "R_10"])
stake = st.number_input("Stake Inicial", min_value=0.35, step=0.01, value=0.35)
use_martingale = st.checkbox("Usar Martingale", value=True)
factor = st.number_input("Fator de Martingale", min_value=1.0, step=0.1, value=2.0)
target_profit = st.number_input("Meta de Lucro", min_value=0.0, value=10.0, step=0.5)
stop_loss = st.number_input("Stop Loss", min_value=0.0, value=10.0, step=0.5)
selected_ticks = st.selectbox("Analisar últimos ticks", [33, 50, 100, 200])
percentual_minimo = st.selectbox("Percentual mínimo <4 para entrada", [40, 65, 70, 80])

# Placeholders
if "placeholder_logs" not in st.session_state:
    st.session_state.placeholder_logs = st.empty()
if "placeholder_lucro" not in st.session_state:
    st.session_state.placeholder_lucro = st.empty()

# Bot & estado
if "bot" not in st.session_state:
    st.session_state.bot = None
if "running" not in st.session_state:
    st.session_state.running = False

# Função para iniciar o robô
def iniciar_robo():
    # Inicializa bot e threads
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
    st.session_state.bot = bot
    st.session_state.running = True
    # Inicia thread de run_interface (decisão + operação)
    threading.Thread(target=bot.run_interface, daemon=True).start()
    # Inicia thread de ticks (embutido em run_interface, mas caso queira separado apenas:
    # threading.Thread(target=bot.receber_ticks, daemon=True).start()
    # A thread interna run_interface já chama receber_ticks.
    # Não iniciamos threads que chamem st.* diretamente.
    # UI será atualizada pelo loop abaixo.

# Botão para iniciar/parar
if not st.session_state.running:
    if st.button("🚀 Iniciar Robô"):
        if not token:
            st.error("Informe o token antes de iniciar.")
        else:
            iniciar_robo()
else:
    if st.button("🛑 Parar Robô"):
        # Para o bot
        st.session_state.bot.running = False
        st.session_state.running = False
        st.success("Robô parado pelo usuário.")

# Loop de atualização da interface
# Usamos st.experimental_rerun em delay para atualizar continuamente
if st.session_state.running and st.session_state.bot is not None:
    bot = st.session_state.bot
    # Exibir lucro acumulado
    lucro = bot.lucro_acumulado
    if lucro >= 0:
        st.session_state.placeholder_lucro.success(f"💰 Lucro acumulado: +${lucro:.2f}")
    else:
        st.session_state.placeholder_lucro.error(f"📉 Lucro acumulado: -${abs(lucro):.2f}")

    # Exibir últimos logs
    # Logs são strings, já com timestamp no início
    logs_para_mostrar = bot.logs[-12:] if len(bot.logs) >= 12 else bot.logs
    st.session_state.placeholder_logs.text("\n".join(logs_para_mostrar))

    # Para manter atualização periódica:
    time.sleep(2)
    st.experimental_rerun()
else:
    # Se não rodando, pode exibir mensagem inicial ou logs anteriores
    if st.session_state.bot is not None and bot.logs:
        # exibe última situação
        st.session_state.placeholder_logs.text("\n".join(st.session_state.bot.logs[-12:]))
    else:
        st.session_state.placeholder_logs.text("Aguardando início do robô...")
    st.session_state.placeholder_lucro.text("")
