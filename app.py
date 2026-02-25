from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
import re

app = Flask(__name__)
app.secret_key = 'rahasia'  # untuk flash messages

# Simulasi penyimpanan sementara (list of dict)
targets = []

def validate_nama(nama):
    """Validasi field Nama Target"""
    if not nama:
        return False, "Nama target wajib diisi."
    if len(nama) > 50:
        return False, "Nama target maksimal 50 karakter."
    if not re.match(r'^[a-zA-Z0-9\s]+$', nama):
        return False, "Nama target hanya boleh huruf, angka, dan spasi."
    return True, nama

def validate_nominal(nominal_str):
    """Validasi field Target Nominal"""
    try:
        nominal = int(nominal_str)
    except ValueError:
        return False, "Target nominal harus berupa angka."
    if nominal < 100000:
        return False, "Target nominal minimal Rp 100.000."
    if nominal > 100000000:
        return False, "Target nominal maksimal Rp 100.000.000."
    return True, nominal

def validate_tanggal(tanggal_str):
    """Validasi field Tanggal Mulai (format YYYY-MM-DD dari input date)"""
    try:
        tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
    except ValueError:
        return False, "Format tanggal tidak valid."
    
    hari_ini = datetime.now().date()
    max_tanggal = hari_ini + timedelta(days=365)
    
    if tanggal < hari_ini:
        return False, "Tanggal mulai tidak boleh kurang dari hari ini."
    if tanggal > max_tanggal:
        return False, "Tanggal mulai tidak boleh lebih dari 1 tahun ke depan."
    return True, tanggal

def hitung_total(nominal, jangka_waktu, status, asuransi, kategori):
    """
    Menghitung setoran bulanan, diskon, biaya asuransi, dan total komitmen.
    Prioritas: Jika asuransi dan kategori Dana Darurat, maka error dan tidak ada diskon/biaya.
    """
    setoran_bulanan_int = nominal // jangka_waktu  # pembulatan ke bawah
    setoran_bulanan_float = nominal / jangka_waktu
    
    diskon = 0
    biaya_asuransi = 0
    error_asuransi = False
    
    # Cek error asuransi terlebih dahulu
    if asuransi and kategori == 'Dana Darurat':
        error_asuransi = True
    else:
        if status == 'Premium' and jangka_waktu == 12:
            diskon = 10000
        if asuransi:  # dan kategori bukan Dana Darurat
            biaya_asuransi = int(nominal * 0.05)  # 5%
    
    total = nominal + biaya_asuransi - diskon
    
    return {
        'setoran_bulanan_int': setoran_bulanan_int,
        'setoran_bulanan_float': round(setoran_bulanan_float, 2),
        'diskon': diskon,
        'biaya_asuransi': biaya_asuransi,
        'total': total,
        'error_asuransi': error_asuransi
    }

@app.route('/')
def index():
    """Halaman form pembuatan target"""
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create():
    """Memproses form dan membuat target baru"""
    # Ambil data dari form
    nama = request.form.get('nama', '').strip()
    kategori = request.form.get('kategori')
    nominal_str = request.form.get('nominal', '').strip()
    jangka_waktu = request.form.get('jangka_waktu')
    tanggal_str = request.form.get('tanggal_mulai')
    status = request.form.get('status', 'Reguler')
    asuransi = request.form.get('asuransi') == 'on'
    
    # Validasi nama
    valid_nama, msg_nama = validate_nama(nama)
    if not valid_nama:
        flash(msg_nama, 'error')
        return redirect(url_for('index'))
    
    # Validasi nominal
    valid_nominal, result_nominal = validate_nominal(nominal_str)
    if not valid_nominal:
        flash(result_nominal, 'error')
        return redirect(url_for('index'))
    nominal = result_nominal
    
    # Validasi jangka waktu
    if jangka_waktu not in ['3', '6', '12']:
        flash("Jangka waktu tidak valid.", 'error')
        return redirect(url_for('index'))
    jangka_waktu = int(jangka_waktu)
    
    # Validasi tanggal
    valid_tanggal, result_tanggal = validate_tanggal(tanggal_str)
    if not valid_tanggal:
        flash(result_tanggal, 'error')
        return redirect(url_for('index'))
    tanggal_mulai = result_tanggal
    
    # Hitung total dan cek error asuransi
    hasil = hitung_total(nominal, jangka_waktu, status, asuransi, kategori)
    
    if hasil['error_asuransi']:
        flash("Asuransi tidak tersedia untuk kategori Dana Darurat.", 'error')
        return redirect(url_for('index'))
    
    # Simpan target ke daftar (simulasi database)
    target_baru = {
        'nama': nama,
        'kategori': kategori,
        'nominal': nominal,
        'jangka_waktu': jangka_waktu,
        'tanggal_mulai': tanggal_mulai.strftime('%d/%m/%Y'),
        'status': status,
        'asuransi': asuransi,
        'setoran': hasil['setoran_bulanan_int'],
        'total': hasil['total'],
        'diskon': hasil['diskon'],
        'biaya_asuransi': hasil['biaya_asuransi']
    }
    targets.append(target_baru)
    
    # Tampilkan halaman hasil
    return render_template('result.html', target=target_baru)

@app.route('/list')
def list_targets():
    """Halaman daftar semua target yang telah dibuat"""
    return render_template('list.html', targets=targets)

if __name__ == '__main__':
    app.run(debug=True)