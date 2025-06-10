from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    dong = request.form.get('dong')
    if not dong:
        return jsonify({'error': '법정동을 입력하세요'})
    
    # FastAPI 서버에 요청
    response = requests.get(f'http://localhost:8000/getbubjungdong?dong={dong}')
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
