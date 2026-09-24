"""Keep reviewed sign art inside object silhouettes; restore crop surroundings.

Reuses imagegen rasters from v3/v4. Masks perform compositing only.
Run before building root, 026-gas-gate and 027-junkgate.
"""
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scene_assets import ROOT

JOBS = [
    ('label', None, (340,330,550,560), [
        [(59,68),(129,61),(133,64),(137,160),(132,167),(66,173),(61,170),(55,74)]]),
    ('surplus', None, (1690,180,2120,480), [
        [(58,77),(364,49),(367,163),(174,204),(163,187),(153,180),
         (144,186),(135,214),(62,230)]]),
    ('signs', '026-gas-gate', (1060,475,1250,820), [
        [(53,62),(126,53),(127,138),(52,147)],
        [(59,164),(117,156),(119,284),(59,288)]]),
    ('lettering', '027-junkgate', (140,20,965,445), [
        [(304,59),(565,89),(536,137),(275,108)],
        [(105,102),(716,168),(718,259),(104,217)],
        [(246,308),(623,333),(623,384),(245,373)]]),
]

def main():
    review = ROOT/'reviews/sign-boundaries-v8'
    review.mkdir(exist_ok=True, parents=True)
    report = []
    for key, room, box, polygons in JOBS:
        folder = ROOT/'locations'/room if room else ROOT
        destination = folder/'custom-remaster-v1.png' if room else ROOT/'scene/custom-remaster-v1.png'
        backup = review/((room or '010-dumpster')+'-before.png')
        if not backup.exists():
            Image.open(destination).save(backup)
        current = Image.open(destination).convert('RGB')
        size = tuple(json.loads((folder/'room.json').read_text())['size']) if room else (2220,1200)
        current = current.resize(size, Image.Resampling.LANCZOS)
        base_path = folder/'before-static-v3/custom-remaster-v1.png'
        art_path = ROOT/'reviews/static-sprites-v3'/(key+'-generated.png')
        if key == 'surplus':
            base_path = ROOT/'reviews/dumpster-v4/before-sign.png'
            art_path = ROOT/'reviews/dumpster-v4/sign-generated.png'
        base = Image.open(base_path).convert('RGB').resize(size, Image.Resampling.LANCZOS).crop(box)
        art = Image.open(art_path).convert('RGB').resize(base.size, Image.Resampling.LANCZOS)
        mask = Image.new('L',base.size)
        draw = ImageDraw.Draw(mask)
        for polygon in polygons:
            draw.polygon(polygon, fill=255)
        # Inward feather: zero coverage beyond the selected object, even after blur.
        hard = np.array(mask)
        soft = np.minimum(hard, np.array(mask.filter(ImageFilter.GaussianBlur(.65))))
        mask = Image.fromarray(soft)
        result = Image.composite(art,base,mask)
        assert np.array_equal(np.array(result)[hard==0],np.array(base)[hard==0])
        before = np.array(current)
        current.paste(result,box[:2])
        outside = np.ones((size[1],size[0]),bool)
        outside[box[1]:box[3],box[0]:box[2]] = False
        assert np.array_equal(before[outside],np.array(current)[outside])
        current.save(destination)
        result.save(review/(key+'-fixed.png'))
        mask.save(review/(key+'-mask.png'))
        report.append(dict(key=key,room=room or '010-dumpster',box=box,
                           surroundings_restored_exactly=True,other_scene_pixels_unchanged=True))
    (review/'validation.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__ == '__main__':
    main()
