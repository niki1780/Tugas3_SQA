import pytest
from app import app, targets, validate_nama, validate_nominal, validate_tanggal, hitung_total
from datetime import datetime, timedelta

@pytest.fixture
def client():
    """Setup test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Bersihkan data targets sebelum setiap test
        targets.clear()
        yield client

# TEST VALIDATE NAMA
def test_validate_nama_kosong():
    valid, msg = validate_nama("")
    assert valid == False
    assert "wajib diisi" in msg

def test_validate_nama_valid():
    valid, msg = validate_nama("Budi Santoso")
    assert valid == True
    assert msg == "Budi Santoso"

def test_validate_nama_karakter_special():
    valid, msg = validate_nama("Budi@Santoso")
    assert valid == False
    assert "hanya boleh huruf" in msg

def test_validate_nama_max_length():
    # Test nama lebih dari 50 karakter
    valid, msg = validate_nama("A" * 51)
    assert valid == False
    assert "maksimal 50 karakter" in msg

# TEST VALIDATE NOMINAL
def test_validate_nominal_huruf():
    valid, msg = validate_nominal("abc")
    assert valid == False
    assert "harus berupa angka" in msg

def test_validate_nominal_kurang_dari_minimal():
    valid, msg = validate_nominal("50000")
    assert valid == False
    assert "minimal Rp 100.000" in msg

def test_validate_nominal_lebih_dari_maksimal():
    valid, msg = validate_nominal("200000000")
    assert valid == False
    assert "maksimal Rp 100.000.000" in msg

def test_validate_nominal_valid():
    valid, msg = validate_nominal("500000")
    assert valid == True
    assert msg == 500000

# TEST VALIDATE TANGGAL
def test_validate_tanggal_format_salah():
    valid, msg = validate_tanggal("01-01-2025")
    assert valid == False
    assert "Format tanggal tidak valid" in msg

def test_validate_tanggal_kemarin():
    kemarin = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    valid, msg = validate_tanggal(kemarin)
    assert valid == False
    assert "tidak boleh kurang dari hari ini" in msg

def test_validate_tanggal_lebih_1_tahun():
    tahun_depan = (datetime.now() + timedelta(days=366)).strftime('%Y-%m-%d')
    valid, msg = validate_tanggal(tahun_depan)
    assert valid == False
    assert "tidak boleh lebih dari 1 tahun" in msg

def test_validate_tanggal_valid():
    besok = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    valid, msg = validate_tanggal(besok)
    assert valid == True

# TEST HITUNG TOTAL
def test_hitung_total_premium_12_bulan():
    hasil = hitung_total(1000000, 12, 'Premium', False, 'Gadget')
    assert hasil['diskon'] == 10000
    assert hasil['biaya_asuransi'] == 0
    assert hasil['total'] == 990000  # 1jt - 10rb

def test_hitung_total_reguler_12_bulan():
    hasil = hitung_total(1000000, 12, 'Reguler', False, 'Gadget')
    assert hasil['diskon'] == 0
    assert hasil['biaya_asuransi'] == 0
    assert hasil['total'] == 1000000

def test_hitung_total_dengan_asuransi():
    hasil = hitung_total(1000000, 6, 'Reguler', True, 'Gadget')
    assert hasil['biaya_asuransi'] == 50000  # 5% dari 1jt
    assert hasil['total'] == 1050000  # 1jt + 50rb

def test_hitung_total_asuransi_dana_darurat():
    hasil = hitung_total(1000000, 6, 'Reguler', True, 'Dana Darurat')
    assert hasil['error_asuransi'] == True
    assert hasil['biaya_asuransi'] == 0  # Asuransi tidak dihitung

def test_hitung_total_premium_asuransi():
    hasil = hitung_total(2000000, 12, 'Premium', True, 'Liburan')
    assert hasil['diskon'] == 10000
    assert hasil['biaya_asuransi'] == 100000  # 5% dari 2jt
    assert hasil['total'] == 2090000  # 2jt + 100rb - 10rb

# TEST ROUTES / (INDEX)
def test_index_page(client):
    """Test halaman index"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Buat Target Tabungan Impian" in response.data
    assert b"FintechGo!" in response.data

# TEST ROUTES /create (POST)
def test_create_target_success(client):
    response = client.post('/create', data={
        'nama': 'Beli Laptop',
        'kategori': 'Gadget',
        'nominal': '5000000',
        'jangka_waktu': '12',
        'tanggal_mulai': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'status': 'Premium',
        'asuransi': 'on'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert len(targets) == 1
    assert targets[0]['nama'] == 'Beli Laptop'
    assert b"Target Berhasil Dibuat" in response.data

def test_create_target_nama_kosong(client):
    response = client.post('/create', data={
        'nama': '',
        'kategori': 'Gadget',
        'nominal': '5000000',
        'jangka_waktu': '12',
        'tanggal_mulai': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'status': 'Reguler'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert len(targets) == 0  # Target tidak bertambah
    assert b"wajib diisi" in response.data

def test_create_target_nominal_kurang(client):
    response = client.post('/create', data={
        'nama': 'Test',
        'kategori': 'Gadget',
        'nominal': '50000',  # Kurang dari 100rb
        'jangka_waktu': '12',
        'tanggal_mulai': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'status': 'Reguler'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert len(targets) == 0
    assert b"minimal Rp 100.000" in response.data

def test_create_target_asuransi_dana_darurat(client):
    response = client.post('/create', data={
        'nama': 'Darurat',
        'kategori': 'Dana Darurat',
        'nominal': '1000000',
        'jangka_waktu': '6',
        'tanggal_mulai': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'status': 'Reguler',
        'asuransi': 'on'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert len(targets) == 0
    assert b"Asuransi tidak tersedia" in response.data

# TEST ROUTES /list
def test_list_targets_empty(client):
    response = client.get('/list')
    assert response.status_code == 200
    assert b"Belum ada target" in response.data

def test_list_targets_with_data(client):
    # Tambah data dulu
    targets.append({
        'nama': 'Test Target',
        'kategori': 'Gadget',
        'nominal': 1000000,
        'jangka_waktu': 12,
        'tanggal_mulai': '01/01/2025',
        'status': 'Reguler',
        'asuransi': False,
        'setoran': 83333,
        'total': 1000000,
        'diskon': 0,
        'biaya_asuransi': 0
    })
    response = client.get('/list')
    assert response.status_code == 200
    assert b"Test Target" in response.data
    assert b"Daftar Target Tabungan" in response.data