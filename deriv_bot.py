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
        self.logs = []            # lista de strings de log: "[HH:MM:SS] Mensagem"
        self.resultados = []      # lista de tuplas (hora, "WIN"/"LOSS", stake_usado)
        self.lucro_acumulado = 0.0
        self.running = True
        self.ticks = []           # lista de últimos dígitos recebidos

    def log(self, msg: str):
        """Acumula log em self.logs, com timestamp. Não chama Streamlit aqui."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {msg}"
        self.logs.append(log_msg)
        # Opcional: limitar tamanho para não crescer demais
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

    def receber_ticks(self):
        """Thread que coleta ticks e popula self.ticks."""
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089")
            # Autorizar, se necessário:
            ws.send(json.dumps({"authorize": self.token}))
            _ = ws.recv()  # descartar resposta de authorize
            # Enviar subscription de ticks:
            ws.send(json.dumps({"ticks": self.symbol}))
            while self.running:
                response = ws.recv()
                if not response:
                    continue
                data = json.loads(response)
                if "tick" in data:
                    # último dígito:
                    try:
                        ultimo_digito = int(str(data["tick"]["quote"])[-1])
                    except:
                        continue
                    self.ticks.append(ultimo_digito)
                    # manter só últimos selected_ticks
                    if len(self.ticks) > self.selected_ticks:
                        # descartamos o mais antigo
                        self.ticks.pop(0)
        except Exception as e:
            self.log(f"Erro nos ticks: {e}")
        finally:
            try:
                ws.close()
            except:
                pass

    def fazer_operacao(self):
        """Thread ou chamada interna que realiza uma operação quando há oportunidade."""
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089")
            # Autentica
            ws.send(json.dumps({"authorize": self.token}))
            auth_resp = ws.recv()
            if not auth_resp:
                self.log("❌ Erro: sem resposta de auth")
                ws.close()
                return
            auth = json.loads(auth_resp)
            if "error" in auth:
                self.log("❌ Token inválido")
                ws.close()
                return

            # Enviar proposta DIGITOVER barrier=3
            proposal_req = {
                "proposal": 1,
                "amount": round(self.stake_atual, 2),
                "basis": "stake",
                "contract_type": "DIGITOVER",
                "currency": "USD",
                "duration": 1,
                "duration_unit": "t",
                "symbol": self.symbol,
                "barrier": 3
            }
            ws.send(json.dumps(proposal_req))
            resp = ws.recv()
            if not resp:
                self.log("❌ Erro: sem resposta de proposal")
                ws.close()
                return
            data = json.loads(resp)
            if "error" in data:
                self.log(f"❌ Erro na proposal: {data['error']}")
                ws.close()
                return
            if "proposal" not in data or "id" not in data["proposal"]:
                self.log("❌ Erro: resposta inesperada da Deriv (sem campo 'proposal')")
                ws.close()
                return
            proposal_id = data["proposal"]["id"]

            # Enviar buy
            buy_req = {"buy": proposal_id, "price": round(self.stake_atual, 2)}
            ws.send(json.dumps(buy_req))
            resp2 = ws.recv()
            if not resp2:
                self.log("❌ Erro: sem resposta de buy")
                ws.close()
                return
            data2 = json.loads(resp2)
            if "error" in data2:
                self.log(f"❌ Erro no buy: {data2['error']}")
                ws.close()
                return
            if "buy" not in data2 or "contract_id" not in data2["buy"]:
                self.log("❌ Erro ao operar: resposta sem campo 'buy'")
                ws.close()
                return
            contract_id = data2["buy"]["contract_id"]
            self.log(f"🟢 Entrada realizada: DIGITOVER barrier=3 | Stake: ${self.stake_atual:.2f}")

            # Aguardar resultado
            while self.running:
                resp3 = ws.recv()
                if not resp3:
                    continue
                data3 = json.loads(resp3)
                # Quando contrato for vendido, aparece em "proposal_open_contract"
                if "proposal_open_contract" in data3:
                    poc = data3["proposal_open_contract"]
                    if poc.get("is_sold"):
                        profit = float(poc.get("profit", 0))
                        resultado = "WIN" if profit > 0 else "LOSS"
                        self.log(f"🏁 Resultado: {resultado} | Lucro: ${profit:.2f}")
                        # armazenar histórico
                        hora = datetime.now().strftime("%H:%M:%S")
                        self.resultados.append((hora, resultado, self.stake_atual))
                        self.lucro_acumulado += profit
                        # ajuste stake e ticks
                        if resultado == "WIN":
                            self.stake_atual = self.stake_inicial
                            self.ticks.clear()
                        else:
                            # LOSS
                            if self.use_martingale:
                                self.stake_atual = round(self.stake_atual * self.factor, 2)
                        break
                # senão, continua aguardando
            ws.close()
        except Exception as e:
            self.log(f"❌ Exceção em operação: {e}")
        finally:
            try:
                ws.close()
            except:
                pass

    def run_interface(self):
        """
        Thread principal de decisão: 
        Aguarda ticks suficientes, analisa, faz operação se condição atendida.
        """
        # Iniciar thread de ticks separada
        thread_ticks = threading.Thread(target=self.receber_ticks, daemon=True)
        thread_ticks.start()

        # Ciclo de decisão
        while self.running:
            # Aguardar ticks suficientes
            if len(self.ticks) < self.selected_ticks:
                # Apenas log de progresso, mas sem chamar Streamlit
                self.log(f"⏳ Aguardando... {len(self.ticks)}/{self.selected_ticks} ticks recebidos.")
                time.sleep(1)
                continue

            # Mostrar quais dígitos estão sendo analisados
            self.log(f"📊 Dígitos analisados: {self.ticks[-self.selected_ticks:]}")
            # Chama a função de análise da estratégia
            entrada_info = analisar_ticks_famped(self.ticks, self.percento_entrada)
            entrada = entrada_info.get("entrada", "ESPERAR")
            # Se o analisar_ticks_famped retornar "ENTRAR" ou "DIGITOVER", entramos:
            if entrada in ("DIGITOVER", "ENTRAR", "OVER3"):
                self.log(f"🔎 Condição atendida ({entrada_info}). Iniciando operação...")
                # faz operação
                self.fazer_operacao()
            else:
                # aguarda nova chance
                # opcional: mostrar percentual atual
                abaixo_de_4 = sum(1 for d in self.ticks if d < 4)
                perc = round((abaixo_de_4 / len(self.ticks)) * 100, 2)
                self.log(f"🔍 Aguardando oportunidade... ({perc}% < 4)")
                time.sleep(1)
                continue

            # Verificar stops externos?
            # Exemplo: se lucro_acumulado atingir target_profit, pode parar:
            if self.lucro_acumulado >= self.target_profit:
                self.log("🎯 Meta de lucro atingida. Parando o robô.")
                self.running = False
                break
            if self.lucro_acumulado <= -abs(self.stop_loss):
                self.log("🛑 Stop Loss atingido. Parando o robô.")
                self.running = False
                break
            # observação: o laço recomeça após cada operação automaticamente

        # Quando sair do loop:
        self.log("⚙️ Robô parado.")
