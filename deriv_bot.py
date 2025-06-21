
import websocket, json, time, threading
import streamlit as st
from datetime import datetime
from estrategia_famped import analisar_ticks_famped

class DerivBot:
    def __init__(self, token, symbol, stake, use_martingale, factor, target_profit, stop_loss, selected_ticks, percento_entrada):
        self.token = token
        self.symbol = symbol
        self.stake_inicial = stake
        self.stake_atual = stake
        self.use_martingale = use_martingale
        self.factor = factor
        self.target_profit = target_profit
        self.stop_loss = stop_loss
        self.selected_ticks = selected_ticks
        self.percento_entrada = percento_entrada
        self.logs = []
        self.resultados = []
        self.lucro_acumulado = 0
        self.running = True
        self.ticks = []

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {msg}"
        self.logs.append(log_msg)
        st.session_state['log_status'] = "\n".join(self.logs[-12:])

    def receber_ticks(self):
        ws = websocket.WebSocket()
        ws.connect("wss://ws.deriv.com/websockets/v3")
        ws.send(json.dumps({
            "authorize": self.token
        }))
        ws.send(json.dumps({
            "ticks": self.symbol
        }))
        try:
            while self.running:
                response = json.loads(ws.recv())
                if "tick" in response:
                    ultimo_digito = int(str(response["tick"]["quote"])[-1])
                    self.ticks.append(ultimo_digito)
                    if len(self.ticks) > self.selected_ticks:
                        self.ticks.pop(0)
        except Exception as e:
            self.log(f"Erro nos ticks: {str(e)}")
        finally:
            ws.close()

    def run_interface(self):
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://ws.deriv.com/websockets/v3")
            ws.send(json.dumps({
                "authorize": self.token
            }))
            auth_response = json.loads(ws.recv())
            if "error" in auth_response:
                st.error("❌ Token inválido")
                return
            self.log(f"✅ Conectado | Conta: {'Real' if auth_response['authorize']['is_virtual']==0 else 'Demo'}")

            while self.running:
                if len(self.ticks) < self.selected_ticks:
                    self.log(f"⏳ Aguardando... {len(self.ticks)}/{self.selected_ticks} ticks recebidos.")
                    time.sleep(1)
                    continue

                self.log(f"📊 Dígitos analisados: {self.ticks[-self.selected_ticks:]}")
                entrada_info = analisar_ticks_famped(self.ticks, self.percento_entrada)
                entrada = entrada_info['entrada']
                estrategia = entrada_info['estrategia']

                if entrada == "ESPERAR":
                    self.log("⏳ Aguardando oportunidade...")
                    time.sleep(1)
                    continue

                contract_type = "DIGITOVER"
                barrier = 3

                proposal = {
                    "buy": 1,
                    "price": round(self.stake_atual, 2),
                    "parameters": {
                        "amount": round(self.stake_atual, 2),
                        "basis": "stake",
                        "contract_type": contract_type,
                        "currency": "USD",
                        "duration": 1,
                        "duration_unit": "t",
                        "symbol": self.symbol,
                        "barrier": str(barrier)
                    },
                    "passthrough": {},
                    "req_id": 1
                }

                ws.send(json.dumps(proposal))
                result = json.loads(ws.recv())

                if "buy" not in result:
                    self.log("❌ Erro ao operar: 'proposal'")
                    continue

                contract_id = result["buy"]["contract_id"]
                self.log(f"🟢 Entrada realizada ({estrategia}): OVER 3 | Stake: ${self.stake_atual:.2f}")

                # Aguardar resultado
                while True:
                    response = json.loads(ws.recv())
                    if "transaction_id" in response.get("passthrough", {}):
                        continue
                    if "contract_id" in response.get("subscription", {}):
                        continue
                    if "proposal_open_contract" in response:
                        if response["proposal_open_contract"]["is_sold"]:
                            profit = float(response["proposal_open_contract"]["profit"])
                            resultado = "WIN" if profit > 0 else "LOSS"
                            self.log(f"🏁 Resultado: {resultado} | Lucro: ${profit:.2f}")
                            self.resultados.append((datetime.now().strftime("%H:%M:%S"), resultado, self.stake_atual))
                            self.lucro_acumulado += profit

                            if resultado == "WIN":
                                self.stake_atual = self.stake_inicial
                                self.ticks.clear()
                            elif resultado == "LOSS" and self.use_martingale:
                                self.stake_atual *= self.factor
                            break
        except Exception as e:
            self.log(f"❌ Erro geral: {str(e)}")
        finally:
            ws.close()
