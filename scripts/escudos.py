"""Descarga los escudos que falten desde la web de la federación y les quita el fondo blanco
exterior (solo el blanco que toca los bordes; los blancos de dentro del escudo se conservan).
Para añadir un club: pon aquí su archivo y la URL de su escudo en la RFCF."""
from pathlib import Path
import io
import numpy as np
import requests
from PIL import Image
from scipy import ndimage

RAIZ = Path(__file__).resolve().parent.parent / "escudos"
BASE = "https://ffcantabria.filesnovanet.es/pnfg/pimg/Clubes/"
ESCUDOS = {
    "cayon.png": BASE + "00100_0000662597_Escudo_Ayto_Vectorial_2.jpg",
    "arenas-iguna.png": BASE + "00100_0000656454_Escudo_escuelas_deportivas.png",
    "at-cueto.png": BASE + "00100_0000000020_1024_at_espana_de_cueto.jpg",
    "velarde.png": BASE + "00100_0000694008_ESCUDOVELARDE.jpg",
    "rayo-santa-cruz.png": BASE + "00100_0000646432_IMG_20200918_002055_861.jpg",
    "san-felices.png": BASE + "00100_0000719810_Escudo_vectorizado.jpg",
}
UMBRAL = 232


def quitar_fondo(im):
    a = np.array(im.convert("RGBA")).astype(np.int32)
    rgb, alfa = a[..., :3], a[..., 3]
    blanco = ((rgb.min(axis=2) >= UMBRAL) & ((rgb.max(axis=2) - rgb.min(axis=2)) <= 18)) | (alfa < 10)
    etq, _ = ndimage.label(blanco)
    borde = set(np.unique(np.concatenate([etq[0], etq[-1], etq[:, 0], etq[:, -1]]))) - {0}
    fondo = np.isin(etq, list(borde))
    nueva = alfa.copy()
    nueva[fondo] = 0
    anillo = ndimage.binary_dilation(fondo, iterations=2) & ~fondo
    suave = np.clip((255 - rgb.min(axis=2)) * 255 // 75, 0, 255)
    nueva[anillo] = np.minimum(nueva[anillo], suave[anillo])
    a[..., 3] = nueva
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    caja = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if caja:
        out = out.crop(caja)
    if max(out.size) > 600:
        out.thumbnail((600, 600))
    return out


def main():
    RAIZ.mkdir(exist_ok=True)
    for nombre, url in ESCUDOS.items():
        destino = RAIZ / nombre
        if destino.exists():
            continue
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            quitar_fondo(Image.open(io.BytesIO(r.content))).save(destino, optimize=True)
            print(f"Escudo guardado: {nombre}")
        except Exception as e:  # un escudo que falla no debe parar la actualización
            print(f"No se pudo descargar {nombre}: {e}")


if __name__ == "__main__":
    main()
