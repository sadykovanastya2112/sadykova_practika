from flask import Flask, request, abort
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def payment_webhook():
    if request.is_json:
        json_data = request.get_json()
        print("\n🔔 Получен новый вебхук!")
        print(json_data)
        return 'OK', 200
    else:
        return 'Bad Request', 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)