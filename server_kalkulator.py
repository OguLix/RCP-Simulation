import math
from xmlrpc.server import SimpleXMLRPCServer

def tambah(a, b):
    return a + b

def kali(a, b):
    return a * b

def bagi(a, b):
    if b == 0:
        raise ValueError("Pembagian dengan nol")
    return a / b

# --- L1.1 ---
def pangkat(a, b):
    return a ** b

def akar(x):
    if x < 0:
        raise ValueError("Akar bilangan negatif tidak didukung")
    return math.sqrt(x)

# --- L1.2 ---
def statistik(daftar):
    return {"min": min(daftar), "max": max(daftar), "rata2": sum(daftar) / len(daftar)}

# --- L1.3 ---
def info_tipe(x):
    return f"server menerima tipe {type(x).__name__}: {x!r}"

server = SimpleXMLRPCServer(("0.0.0.0", 8000), allow_none=True, logRequests=True)
server.register_introspection_functions()
for f in (tambah, kali, bagi, pangkat, akar, statistik, info_tipe):
    server.register_function(f, f.__name__)
print("Server XML-RPC berjalan di port 8000...")
server.serve_forever()