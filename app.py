import time
import requests
import threading
import random
import csv
import os
from flask import Flask, render_template, jsonify, send_file
from datetime import datetime

# Funktion zur Abruf von Live-Preisen von Coinbase
def get_btc_price():
    try:
        response = requests.get('https://api.coinbase.com/v2/prices/BTC-USD/spot', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return float(data['data']['amount'])  # Aktueller Preis
        else:
            print(f"Fehler: API-Antwortstatus {response.status_code}")
            return None
    except Exception as e:
        print(f"Fehler beim Abrufen der Preise: {e}")
        return None

# Esoterisches Signal generieren
def esoteric_signal():
    return random.random() > 0.7

# Trading-Logik
class TradingBot:
    def __init__(self, initial_capital=10000, interval=60):
        self.capital = initial_capital  # Anfangskapital in USD
        self.btc_held = 0
        self.trades = []
        self.interval = interval  # Handelsintervall in Sekunden
        self.running = False
        self.daily_profit_loss = []  # Täglicher Gewinn/Verlust
        self.start_time = time.time()  # Startzeit des Bots
        self.current_date = datetime.now().date()  # Aktuelles Datum

    def start(self):
        self.running = True
        backoff_time = 10  # Starte mit einer Wartezeit von 10 Sekunden

        while self.running:
            current_price = get_btc_price()
            if current_price is None:
                print(f"Fehler beim Abrufen des Preises. Warte {backoff_time} Sekunden...")
                time.sleep(backoff_time)
                backoff_time = min(backoff_time * 2, 60)  # Erhöhe die Wartezeit bis maximal 60 Sekunden
                continue

            backoff_time = 10  # Setze die Wartezeit zurück, wenn die Anfrage erfolgreich war

            print(f"Aktueller BTC-Preis: {current_price:.2f} USD")

            if esoteric_signal():  # Kaufsignal
                if self.capital > 0:
                    btc_to_buy = self.capital / current_price
                    self.btc_held += btc_to_buy
                    self.capital = 0
                    trade = {'Type': 'Buy', 'Price': current_price, 'Amount': btc_to_buy, 'Timestamp': time.time()}
                    self.trades.append(trade)
                    self.save_trade_to_csv(trade)
                    print(f"Kaufte {btc_to_buy:.4f} BTC bei {current_price:.2f} USD")
                else:
                    print("Nicht genug Kapital zum Kaufen.")
            
            else:  # Verkaufssignal
                if self.btc_held > 0:
                    self.capital += self.btc_held * current_price
                    trade = {'Type': 'Sell', 'Price': current_price, 'Amount': self.btc_held, 'Timestamp': time.time()}
                    self.trades.append(trade)
                    self.save_trade_to_csv(trade)
                    self.btc_held = 0
                    print(f"Verkaufte {trade['Amount']:.4f} BTC bei {current_price:.2f} USD")
                else:
                    print("Kein BTC zum Verkaufen vorhanden.")

            # Aktuelles Portfolio ausgeben
            portfolio_value = self.capital + (self.btc_held * current_price)
            print(f"Aktueller Portfolio-Wert: {portfolio_value:.2f} USD")

            # Täglicher Gewinn/Verlust berechnen
            self.calculate_daily_profit_loss(current_price)

            # Überprüfe, ob der Tag gewechselt hat
            self.check_new_day()

            # Warte das angegebene Intervall
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def save_trade_to_csv(self, trade):
        # Speichere den Trade in einer CSV-Datei basierend auf dem aktuellen Datum
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"trades_{date_str}.csv"
        fieldnames = ['Type', 'Price', 'Amount', 'Timestamp']

        # Überprüfe, ob die Datei bereits existiert
        file_exists = os.path.isfile(filename)

        with open(filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(trade)

    def calculate_daily_profit_loss(self, current_price):
        # Berechne den Gesamtgewinn/Verlust und den täglichen Prozentsatz
        portfolio_value = self.capital + (self.btc_held * current_price)
        profit_loss = portfolio_value - 10000  # Startkapital
        percentage_profit = (profit_loss / 10000) * 100
        self.daily_profit_loss.append({
            'Timestamp': time.time(),
            'ProfitLoss': profit_loss,
            'PercentageProfit': percentage_profit
        })

    def check_new_day(self):
        # Überprüfe, ob der Tag gewechselt hat
        current_date = datetime.now().date()
        if current_date != self.current_date:
            self.current_date = current_date
            print(f"Neuer Tag: {current_date}. Archiviere Trades...")

    def get_portfolio_value(self, current_price):
        return self.capital + (self.btc_held * current_price)

# Flask-Webanwendung
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    current_price = get_btc_price()
    if current_price is None:
        return jsonify({"error": "Fehler beim Abrufen des Preises"}), 500

    portfolio_value = bot.get_portfolio_value(current_price)
    daily_profit_loss = bot.daily_profit_loss[-1] if bot.daily_profit_loss else {"ProfitLoss": 0, "PercentageProfit": 0}

    return jsonify({
        "btc_price": current_price,
        "portfolio_value": portfolio_value,
        "daily_profit_loss": daily_profit_loss["ProfitLoss"],
        "percentage_profit": daily_profit_loss["PercentageProfit"]
    })

@app.route('/download/<date>')
def download_trades(date):
    # Lade die CSV-Datei für das angegebene Datum herunter
    filename = f"trades_{date}.csv"
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({"error": "Die angeforderte Datei existiert nicht."}), 404

# Hauptprogramm
if __name__ == "__main__":
    bot = TradingBot(initial_capital=10000, interval=60)

    # Starte den Bot in einem separaten Thread
    bot_thread = threading.Thread(target=bot.start, daemon=True)
    bot_thread.start()

    # Starte die Flask-App
    app.run(debug=True)