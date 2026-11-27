"""Store images, in-game frame only (no drawing, text or shade; Modrinth rule 6.2, docs/store/README.md).

python3 store.py FRAME OUT_DIR  → icon-ingame.png (512), icon-ingame-400.png, banner-store.jpg (1920×640)
docs/media: the pack's own gallery/strike.jpg (an Incoming cruise missile salvo hits a village at dusk); icon centred
on the fireball (1010, 380) at zoom 1.8, banner centred (960, 400)."""
import os, sys
from PIL import Image
from compose import crop, save

if __name__ == '__main__':
    frame, out = sys.argv[1:3]
    icon = crop(frame, 512, 512, 1010, 380, zoom=1.8)
    save(icon, os.path.join(out, 'icon-ingame.png'))
    save(icon.resize((400, 400), Image.LANCZOS), os.path.join(out, 'icon-ingame-400.png'))
    save(crop(frame, 1920, 640, 960, 400), os.path.join(out, 'banner-store.jpg'))
