import websocket, json, time, threading
from datetime import datetime
from estrategia_famped import analisar_ticks_famped

class DerivBot:
    def __init__(self, token, symbol, stake, use_martingale, factor,
                 target_profit, stop_loss, selected_ticks, percento_entrada):
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
        self.profits = []
        self.lucro_acumulado = 0.0
        self.running = True
        self.ticks = []
        self.in_operation = False

    def log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {msg}"
        self.logs.append(log_msg)
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

    def receber_ticks(self):
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089")
            ws.send(json.dumps({"authorize": self.token}))
            _ = ws.recv()
            ws.send(json.dumps({"ticks": self.symbol}))
            while self.running:
                resp = ws.recv()
                if not resp:
                    continue
                data = json.loads(resp)
                if "tick" in data:
                    try:
                        ultimo_digito = int(str(data["tick"]["quote"])[-1])
                    except:
                        continue
                    self.ticks.append(ultimo_digito)
                    if len(self.ticks) > self.selected_ticks:
                        self.ticks.pop(0)
        except Exception as e:
            self.log(f"Erro nos ticks: {e}")
        finally:
            try:
                ws.close()
            except:
                pass

    def fazer_operacao(self):
        resultado = None
        profit = 0.0
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089")
            ws.send(json.dumps({"authorize": self.token}))
            auth_resp = ws.recv()
            if not auth_resp:
                self.log("❌ Erro: sem resposta de auth")
                ws.close()
                return "ERROR", 0.0
            auth = json.loads(auth_resp)
            if "error" in auth:
                self.log("❌ Token inválido")
                ws.close()
                self.running = False
                return "ERROR", 0.0

            proposal_req = {
                "proposal": 1,
                "amount": round(self.stake_atual, 2),
                "basis": "stake",
                "contract_type": "DIGITOVER",
                "currency": "USD",
                "duration": 1,
                "duration_unit": "t",
                "symbol": self.symbol,
                "barrier": "3"
            }
            ws.send(json.dumps(proposal_req))
            resp = ws.recv()
            self.log(f"DEBUG proposal response: {resp}")
            if not resp:
                self.log("❌ Erro: sem resposta de proposal")
                ws.close()
                return "ERROR", 0.0
            data = json.loads(resp)
            if "error" in data:
                self.log(f"❌ Erro na proposal: {data.get('error')}")
                ws.close()
                return "ERROR", 0.0
            if "proposal" not in data or "id" not in data["proposal"]:
                self.log("❌ Erro: resposta inesperada da Deriv (sem campo 'proposal')")
                ws.close()
                return "ERROR", 0.0
            proposal_id = data["proposal"]["id"]

            buy_req = {"buy": proposal_id, "price": round(self.stake_atual, 2)}
            ws.send(json.dumps(buy_req))
            resp2 = ws.recv()
            self.log(f"DEBUG buy response: {resp2}")
            if not resp2:
                self.log("❌ Erro: sem resposta de buy")
                ws.close()
                return "ERROR", 0.0
            data2 = json.loads(resp2)
            if "error" in data2:
                self.log(f"❌ Erro no buy: {data2.get('error')}")
                ws.close()
                return "ERROR", 0.0
            if "buy" not in data2 or "contract_id" not in data2["buy"]:
                self.log("❌ Erro ao operar: resposta sem campo 'buy'")
                ws.close()
                return "ERROR", 0.0
            contract_id = data2["buy"]["contract_id"]
            self.log(f"🟢 Entrada enviada: DIGITOVER barrier=3 | Stake: ${self.stake_atual:.2f} | Contract ID: {contract_id}")

            # Correct subscription: use proposal_open_contract:1 and contract_id field
            sub_req = {"proposal_open_contract": 1, "contract_id": contract_id}
            ws.send(json.dumps(sub_req))

            while self.running:
                resp3 = ws.recv()
                if not resp3:
                    continue
                data3 = json.loads(resp3)
                if "proposal_open_contract" in data3:
                    poc = data3["proposal_open_contract"]
                    if poc.get("is_sold"):
                        profit = float(poc.get("profit", 0))
                        resultado = "WIN" if profit > 0 else "LOSS"
                        self.log(f"🏁 Resultado: {resultado} | Lucro: ${profit:.2f}")
                        hora = datetime.now().strftime("%H:%M:%S")
                        self.resultados.append((hora, resultado, self.stake_atual, profit))
                        ws.close()
                        return resultado, profit
            ws.close()
        except Exception as e:
            self.log(f"❌ Exceção em operação: {e}")
        finally:
            try:
                ws.close()
            except:
                pass
        return "ERROR", 0.0

    def run_interface(self):
        thread_ticks = threading.Thread(target=self.receber_ticks, daemon=True)
        thread_ticks.start()

        while self.running:
            if len(self.ticks) < self.selected_ticks:
                self.log(f"⏳ Aguardando... {len(self.ticks)}/{self.selected_ticks} ticks recebidos.")
                time.sleep(1)
                continue

            self.log(f"📊 Dígitos analisados: {self.ticks[-self.selected_ticks:]}")

            if self.in_operation:
                time.sleep(1)
                continue

            entrada_info = analisar_ticks_famped(self.ticks, self.percento_entrada)
            entrada = entrada_info.get("entrada", "ESPERAR")
            if entrada == "DIGITOVER":
                self.log("🔎 Condição atendida. Iniciando operação...")
                self.in_operation = True
                while self.running:
                    resultado, profit = self.fazer_operacao()
                    if resultado not in ("WIN", "LOSS"):
                        break
                    self.profits.append(profit)
                    self.lucro_acumulado += profit
                    if resultado == "LOSS" and self.use_martingale:
                        new_stake = round(self.stake_atual * self.factor, 2)
                        self.log(f"🔄 LOSS detectado. Aplicando martingale: stake ajustada para ${new_stake:.2f}")
                        self.stake_atual = new_stake
                        continue
                    if resultado == "WIN":
                        self.stake_atual = self.stake_inicial
                    else:
                        self.stake_atual = self.stake_inicial
                    self.ticks.clear()
                    break
                self.in_operation = False
            else:
                abaixo_de_4 = sum(1 for d in self.ticks if d < 4)
                perc = round((abaixo_de_4 / len(self.ticks)) * 100, 2)
                self.log(f"🔍 Aguardando oportunidade... ({perc}% < 4)")
                time.sleep(1)
                continue

            if self.lucro_acumulado >= self.target_profit:
                self.log("🎯 Meta de lucro atingida. Parando o robô.")
                self.running = False
                break
            if self.lucro_acumulado <= -abs(self.stop_loss):
                self.log("🛑 Stop Loss atingido. Parando o robô.")
                self.running = False
                break

        self.log("⚙️ Robô parado.")