from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json
import numpy as np,pandas as pd,cv2
from PIL import Image
import phenotype_core as core
ROOT=Path(__file__).resolve().parents[1]
def one(row):
 p=ROOT/row.image_path;rgb=core.read_rgb(p);mask,_=core.segment_seed(rgb)
 out={**core.morphology(mask),**core.color_features(rgb,mask),**core.texture_features(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),mask)}
 Image.fromarray(mask.astype(np.uint8)*255).save(ROOT/row.mask_path)
 return {'seed_id':row.seed_id,**out}
def main():
 m=pd.read_csv(ROOT/'data/image_manifest.csv');expected=pd.read_csv(ROOT/'data/seed_features.csv').set_index('seed_id')
 with ThreadPoolExecutor(max_workers=8) as pool:result=pd.DataFrame(pool.map(one,m.itertuples())).set_index('seed_id')
 cols=json.loads((ROOT/'data/feature_groups.json').read_text())['Combined']
 assert np.allclose(result.loc[expected.index,cols],expected[cols],rtol=1e-10,atol=1e-10)
 result.to_csv(ROOT/'data/recomputed_descriptors.csv')
 print('Re-extracted and verified',len(result),'images and',len(cols),'descriptors')
if __name__=='__main__':main()
