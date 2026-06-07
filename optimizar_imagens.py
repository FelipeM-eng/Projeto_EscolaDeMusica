"""
Script de optimização de imagens — executa uma vez.
Redimensiona para máx 1200px e comprime para JPEG 85%.
Guarda os originais em static/escola_musica/images/originais/
"""

import os
import shutil

try:
    from PIL import Image
except ImportError:
    print("Pillow não instalado. Corre: pip install Pillow")
    exit(1)

PASTA_IMAGENS  = os.path.join('static', 'escola_musica', 'images')
PASTA_BACKUP   = os.path.join(PASTA_IMAGENS, 'originais')
LARGURA_MAX    = 1200
QUALIDADE      = 85
EXTENSOES      = ('.jpg', '.jpeg', '.png', '.webp')

# Cria pasta de backup
os.makedirs(PASTA_BACKUP, exist_ok=True)

resultados = []

for nome_ficheiro in os.listdir(PASTA_IMAGENS):
    caminho = os.path.join(PASTA_IMAGENS, nome_ficheiro)

    # Ignora pastas e ficheiros não-imagem
    if not os.path.isfile(caminho):
        continue
    if not nome_ficheiro.lower().endswith(EXTENSOES):
        continue

    tamanho_antes = os.path.getsize(caminho) / 1024 / 1024  # MB

    # Faz backup do original
    shutil.copy2(caminho, os.path.join(PASTA_BACKUP, nome_ficheiro))

    try:
        with Image.open(caminho) as img:
            # Converte para RGB (necessário para guardar como JPEG)
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')

            largura_original, altura_original = img.size

            # Só redimensiona se for maior que o máximo
            if largura_original > LARGURA_MAX:
                ratio      = LARGURA_MAX / largura_original
                nova_altura = int(altura_original * ratio)
                img        = img.resize(
                    (LARGURA_MAX, nova_altura),
                    Image.LANCZOS
                )
                redimensionada = True
            else:
                redimensionada = False

            # Guarda com compressão
            # Força extensão .jpg para consistência
            nome_base   = os.path.splitext(nome_ficheiro)[0]
            nome_output = nome_base + '.jpg'
            caminho_out = os.path.join(PASTA_IMAGENS, nome_output)

            img.save(
                caminho_out,
                'JPEG',
                quality=QUALIDADE,
                optimize=True,
                progressive=True
            )

            # Remove o original se o nome mudou (ex: .png → .jpg)
            if nome_output != nome_ficheiro:
                os.remove(caminho)

        tamanho_depois = os.path.getsize(caminho_out) / 1024 / 1024
        poupanca       = (1 - tamanho_depois / tamanho_antes) * 100

        resultados.append({
            'nome':        nome_ficheiro,
            'antes':       tamanho_antes,
            'depois':      tamanho_depois,
            'poupanca':    poupanca,
            'redim':       redimensionada,
        })

        print(
            f"✓ {nome_ficheiro:<40} "
            f"{tamanho_antes:.1f}MB → {tamanho_depois:.1f}MB "
            f"(-{poupanca:.0f}%)"
            f"{' [redim]' if redimensionada else ''}"
        )

    except Exception as e:
        print(f"✗ ERRO em {nome_ficheiro}: {e}")

# Resumo final
print("\n" + "═" * 60)
total_antes  = sum(r['antes']  for r in resultados)
total_depois = sum(r['depois'] for r in resultados)
poupanca_total = (1 - total_depois / total_antes) * 100 if total_antes else 0

print(f"Total antes:  {total_antes:.1f} MB")
print(f"Total depois: {total_depois:.1f} MB")
print(f"Poupança:     {poupanca_total:.0f}%")
print(f"\nOriginais guardados em: {PASTA_BACKUP}")
print("Script concluído.")