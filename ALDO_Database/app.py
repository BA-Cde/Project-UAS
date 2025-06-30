from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
database_db = SQLAlchemy(app)

class Mahasiswa(database_db.Model):
    id = database_db.Column(database_db.Integer, primary_key=True)
    nama = database_db.Column(database_db.String(100))
    nim = database_db.Column(database_db.String(20))
    jurusan = database_db.Column(database_db.String(100))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mahasiswa')
def mahasiswa_ui():
    data = Mahasiswa.query.all()
    return render_template('mahasiswa.html', mahasiswa=data)

@app.route('/cuaca')
def cuaca_ui():
    return render_template('cuaca.html')

@app.route('/kalkulator')
def kalkulator_ui():
    return render_template('kalkulator.html')

@app.route('/nilai-tukar')
def nilai_tukar_ui():
    return render_template('nilai_tukar.html')


@app.route('/api/mahasiswa', methods=['GET'])
def get_mahasiswa():
    data = Mahasiswa.query.all()
    result = []
    for m in data:
        result.append({'id': m.id, 'nama': m.nama, 'nim': m.nim, 'jurusan': m.jurusan})
    return jsonify(result)


@app.route('/api/mahasiswa', methods=['POST'])
def add_mahasiswa():
    data = request.json
    mhs = Mahasiswa(nama=data['nama'], nim=data['nim'], jurusan=data['jurusan'])
    database_db.session.add(mhs)
    database_db.session.commit()
    return jsonify({'id': mhs.id, 'nama': mhs.nama, 'nim': mhs.nim, 'jurusan': mhs.jurusan}), 201

@app.route('/api/mahasiswa/<int:id>', methods=['GET'])
def get_mahasiswa_by_id(id):
    mhs = Mahasiswa.query.get(id)
    if mhs:
        return jsonify({'id': mhs.id, 'nama': mhs.nama, 'nim': mhs.nim, 'jurusan': mhs.jurusan})
    return jsonify({'error': 'Mahasiswa not found'}), 404

# PUT mahasiswa by ID
@app.route('/api/mahasiswa/<int:id>', methods=['PUT'])
def update_mahasiswa(id):
    mhs = Mahasiswa.query.get(id)
    if not mhs:
        return jsonify({'error': 'Mahasiswa not found'}), 404

    data = request.json
    mhs.nama = data.get('nama', mhs.nama)
    mhs.nim = data.get('nim', mhs.nim)
    mhs.jurusan = data.get('jurusan', mhs.jurusan)
    database_db.session.commit()

    return jsonify({'id': mhs.id, 'nama': mhs.nama, 'nim': mhs.nim, 'jurusan': mhs.jurusan})

@app.route('/api/mahasiswa/<int:id>', methods=['DELETE'])
def delete_mahasiswa(id):
    mhs = Mahasiswa.query.get(id)
    if mhs:
        database_db.session.delete(mhs)
        database_db.session.commit()
        return jsonify({'message': 'Mahasiswa deleted'}), 200
    return jsonify({'error': 'Mahasiswa not found'}), 404

# ---------------------- API CUACA ----------------------

@app.route('/api/cuaca', methods=['GET'])
def get_cuaca():
    kota = request.args.get('kota', 'Jakarta')
    api_key = os.getenv('WEATHER_API_KEY')
    url = f"http://api.openweathermap.org/data/2.5/weather?q={kota}&appid={api_key}&units=metric&lang=id"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        cuaca = {
            'kota': kota,
            'suhu': data['main']['temp'],
            'deskripsi': data['weather'][0]['description'],
            'kelembaban': data['main']['humidity'],
            'icon': data['weather'][0]['icon']
        }
        return jsonify(cuaca)
    return jsonify({'error': 'Kota tidak ditemukan'}), 404

# ---------------------- API KONVERSI SUHU ----------------------

@app.route('/api/konversi-suhu', methods=['POST'])
def konversi_suhu():
    data = request.json
    suhu = float(data['suhu'])
    dari = data['dari']
    ke = data['ke']
    
    if dari == ke:
        return jsonify({'hasil': suhu})
    
    if dari == 'celsius':
        if ke == 'fahrenheit':
            hasil = (suhu * 9/5) + 32
        elif ke == 'kelvin':
            hasil = suhu + 273.15
    elif dari == 'fahrenheit':
        if ke == 'celsius':
            hasil = (suhu - 32) * 5/9
        elif ke == 'kelvin':
            hasil = (suhu - 32) * 5/9 + 273.15
    elif dari == 'kelvin':
        if ke == 'celsius':
            hasil = suhu - 273.15
        elif ke == 'fahrenheit':
            hasil = (suhu - 273.15) * 9/5 + 32
    
    return jsonify({'hasil': round(hasil, 2)})


@app.route('/api/nilai-tukar', methods=['GET'])
def get_nilai_tukar():
    mata_uang = request.args.get('mata_uang', 'USD')
    url = f"https://api.exchangerate-api.com/v4/latest/{mata_uang}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return jsonify({
            'base': data['base'],
            'rates': {
                'IDR': data['rates']['IDR'],
                'JPY': data['rates']['JPY'],
                'EUR': data['rates']['EUR'],
                'USD': data['rates']['USD']
            }
        })
    return jsonify({'error': 'Mata uang tidak valid'}), 400


if __name__ == '__main__':
    with app.app_context():
        database_db.create_all()
    app.run(debug=True)
