# dashboard/app.py

from flask import Flask, jsonify, render_template_string
import json
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Agent Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0d1117; color: #e6edf3; font-family: monospace; padding: 20px; }
        h1 { color: #58a6ff; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
        .card {
            background: #161b22; border: 1px solid #30363d;
            border-radius: 8px; padding: 15px;
        }
        .card h3 { color: #8b949e; font-size: 12px; margin-bottom: 8px; }
        .card .value { font-size: 22px; font-weight: bold; }
        .BUY { color: #3fb950; }
        .SELL { color: #f85149; }
        .HOLD { color: #8b949e; }
        table { width: 100%; border-collapse: collapse; background: #161b22; border-radius: 8px; overflow: hidden; }
        th { background: #21262d; padding: 12px; text-align: left; color: #8b949e; font-size: 12px; }
        td { padding: 12px; border-top: 1px solid #30363d; }
        .chart-container { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 30px; }
        .refresh { color: #8b949e; font-size: 12px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🤖 Trading Agent Dashboard</h1>
    <p class="refresh" id="timer">Actualisation dans 60s</p>

    <div class="grid" id="cards"></div>

    <div class="chart-container">
        <canvas id="rsiChart" height="80"></canvas>
    </div>

    <table>
        <thead>
            <tr>
                <th>HEURE</th>
                <th>PAIRE</th>
                <th>PRIX</th>
                <th>RSI</th>
                <th>MACD</th>
                <th>SIGNAL</th>
            </tr>
        </thead>
        <tbody id="logs"></tbody>
    </table>

    <script>
        let rsiChart = null;

        async function loadData() {
            const res = await fetch("/api/logs");
            const data = await res.json();

            // Cards — dernière valeur par paire
            const latest = {};
            data.forEach(r => latest[r.symbol] = r);

            const cards = document.getElementById("cards");
            cards.innerHTML = "";
            Object.values(latest).forEach(r => {
                const icon = r.signal === "BUY" ? "🟢" : r.signal === "SELL" ? "🔴" : "⚪";
                cards.innerHTML += `
                    <div class="card">
                        <h3>${r.symbol}</h3>
                        <div class="value">${r.price} <small style="font-size:12px">USDT</small></div>
                        <div style="margin-top:8px">RSI: <b>${r.rsi}</b></div>
                        <div class="value ${r.signal}" style="font-size:16px;margin-top:8px">${icon} ${r.signal}</div>
                    </div>`;
            });

            // Table logs (50 derniers inversés)
            const tbody = document.getElementById("logs");
            tbody.innerHTML = "";
            [...data].reverse().slice(0, 50).forEach(r => {
                const icon = r.signal === "BUY" ? "🟢" : r.signal === "SELL" ? "🔴" : "⚪";
                tbody.innerHTML += `
                    <tr>
                        <td style="color:#8b949e">${r.timestamp}</td>
                        <td><b>${r.symbol}</b></td>
                        <td>${r.price}</td>
                        <td>${r.rsi}</td>
                        <td>${r.macd_diff}</td>
                        <td class="${r.signal}">${icon} ${r.signal}</td>
                    </tr>`;
            });

            // Graphique RSI par paire
            const symbols = [...new Set(data.map(r => r.symbol))];
            const colors = { BTCUSDT: "#f7931a", ETHUSDT: "#627eea", SOLUSDT: "#9945ff", BNBUSDT: "#f0b90b" };
            const labels = [...new Set(data.map(r => r.timestamp))].slice(-20);

            const datasets = symbols.map(sym => ({
                label: sym,
                data: data.filter(r => r.symbol === sym).slice(-20).map(r => r.rsi),
                borderColor: colors[sym],
                tension: 0.3,
                fill: false
            }));

            if (rsiChart) rsiChart.destroy();
            rsiChart = new Chart(document.getElementById("rsiChart"), {
                type: "line",
                data: { labels, datasets },
                options: {
                    plugins: { legend: { labels: { color: "#e6edf3" } } },
                    scales: {
                        x: { ticks: { color: "#8b949e" }, grid: { color: "#21262d" } },
                        y: {
                            ticks: { color: "#8b949e" }, grid: { color: "#21262d" },
                            min: 0, max: 100,
                            afterDataLimits: chart => {
                                chart.max = 100; chart.min = 0;
                            }
                        }
                    },
                    annotation: { annotations: {
                        overbought: { type: "line", yMin: 70, yMax: 70, borderColor: "#f85149", borderDash: [5,5] },
                        oversold: { type: "line", yMin: 30, yMax: 30, borderColor: "#3fb950", borderDash: [5,5] }
                    }}
                }
            });
        }

        // Countdown
        let seconds = 60;
        setInterval(() => {
            seconds--;
            document.getElementById("timer").textContent = `Actualisation dans ${seconds}s`;
            if (seconds <= 0) { seconds = 60; loadData(); }
        }, 1000);

        loadData();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/logs")
def logs():
    log_file = "logs/trades.json"
    if not os.path.exists(log_file):
        return jsonify([])
    with open(log_file, "r") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)