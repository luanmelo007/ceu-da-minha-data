"""
Execute uma vez para baixar e filtrar o catálogo estelar.
Gera o arquivo stars.csv que será commitado no repositório.
"""
import pandas as pd
import requests
import io

print("Baixando catálogo HYG...")

urls = [
    "https://raw.githubusercontent.com/astronexus/HYG-Database/master/hyg/v3/hyg_v3.csv",
    "https://raw.githubusercontent.com/astronexus/HYG-Database/master/hygdata_v3.csv",
]

df = None
for url in urls:
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        print(f"✅ Baixado de: {url}")
        break
    except Exception as e:
        print(f"❌ Falhou: {url} → {e}")

if df is None:
    print("Não foi possível baixar o catálogo.")
    exit(1)

# Filtra apenas colunas necessárias e magnitude <= 7.5
df = df[['ra', 'dec', 'mag']].dropna()
df = df[df['mag'] <= 7.5].reset_index(drop=True)
df.to_csv("stars.csv", index=False)

print(f"✅ stars.csv salvo com {len(df):,} estrelas!")
