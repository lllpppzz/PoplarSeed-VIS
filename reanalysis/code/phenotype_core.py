"""Deterministic threshold phenotyping of supplied PoplarSeed-VIS crops.

Run from this directory with: python -X utf8 phenotyping.py
Original TIFFs are read-only. Measurements are derived from foreground only.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_fill_holes
from skimage.feature import local_binary_pattern
from skimage.measure import perimeter_crofton, regionprops

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parent
CALIBRATION = {'method':'fixed_resampled_image_scale',
               'pixel_size_x_um':20.0, 'pixel_size_y_um':20.0,
               'source':'Standardized output-image scale, 20 micrometres per pixel',
               'version':'fixed_20um_v1',
               'assumption':'Exported images have fixed 20 micrometre pixel spacing on both axes.',
               'conversion':'Lengths use 0.020 mm/pixel; areas use 0.0004 mm2/pixel2.',
               'camera_projection_formula_used':False}
PX_X = 0.020
PX_Y = 0.020
PX = 0.020
VARIETIES = ['NJFU 895','HENAN ZL','LIAON LHY','LIAON MZHY','LIAON XQY','SHANXI QZ','SHANXI XY']
PALETTE = ['#2878A5','#67A9A0','#8D78A8','#C59649','#C66C75','#7D9C55','#8B6C56']

def read_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert('RGB'))

def segment_seed(rgb: np.ndarray, threshold: float = 8) -> tuple[np.ndarray, dict]:
    """Threshold max-channel distance from background; exclude outer canvas.

    The supplied crops have an exactly neutral (128,128,128) circular field
    and black corners. Estimating the modal field avoids a brightness-only
    threshold that would discard pale or dark seed regions.
    """
    h,w=rgb.shape[:2]
    yy,xx=np.indices((h,w))
    rr=np.hypot(xx-(w-1)/2,yy-(h-1)/2)
    annulus=(rr>.36*min(h,w)) & (rr<.44*min(h,w))
    bg=np.median(rgb[annulus],axis=0)
    distance=np.max(np.abs(rgb.astype(np.float32)-bg),axis=2)
    binary=(distance>threshold).astype(np.uint8)
    n,labels,stats,centroids=cv2.connectedComponentsWithStats(binary,8)
    candidates=[]
    for lab in range(1,n):
        x,y,cw,ch,a=stats[lab]
        touches=(x==0 or y==0 or x+cw>=w or y+ch>=h)
        if not touches and a>=20:
            candidates.append(lab)
    if not candidates:
        raise ValueError('No non-border seed component found')
    chosen=max(candidates,key=lambda lab:stats[lab,cv2.CC_STAT_AREA])
    raw=labels==chosen
    mask=binary_fill_holes(raw)
    area=int(mask.sum())
    other=max([int(stats[j,cv2.CC_STAT_AREA]) for j in candidates if j!=chosen] or [0])
    center=np.mean(np.column_stack(np.nonzero(mask)),axis=0)
    info={'threshold':threshold,'background_r':float(bg[0]),'background_g':float(bg[1]),'background_b':float(bg[2]),
          'foreground_px':area,'filled_holes_px':int(mask.sum()-raw.sum()),
          'other_component_ratio':other/max(area,1),
          'centroid_offset_px':float(np.linalg.norm(center-np.array([(h-1)/2,(w-1)/2]))),
          'max_radius_px':float(rr[mask].max()),
          'qc_flag':bool(area<300 or area>15000 or other/max(area,1)>.05 or rr[mask].max()>108)}
    return mask,info

def morphology(mask: np.ndarray) -> dict[str,float]:
    binary=mask.astype(np.uint8)
    contour=max(cv2.findContours(binary,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0],key=cv2.contourArea)
    (_, _),(w,h),angle=cv2.minAreaRect(contour)
    theta=np.deg2rad(angle)
    pixel_support=abs(np.cos(theta))+abs(np.sin(theta))
    length=max(w,h)+pixel_support
    width=min(w,h)+pixel_support
    area=float(binary.sum())
    perimeter=float(perimeter_crofton(binary,directions=4))
    region=regionprops(binary)[0]
    return {'length_px':float(length),'width_px':float(width),'area_px2':area,'perimeter_px':perimeter,
            'length_mm':float(length*PX),'width_mm':float(width*PX),'area_mm2':float(area*PX_X*PX_Y),'perimeter_mm':perimeter*PX,
            'aspect_ratio':float(length/width),'circularity':float(4*np.pi*area/perimeter**2),
            'compactness':float(area/(length*width)), 'solidity':float(region.solidity),
            'eccentricity':float(region.eccentricity), 'roundness':float(4*area/(np.pi*length**2)),
            'equivalent_diameter_mm':float(np.sqrt(4*area/np.pi)*PX)}

def color_features(rgb: np.ndarray, mask: np.ndarray) -> dict[str,float]:
    hsv=cv2.cvtColor(rgb.astype(np.float32)/255,cv2.COLOR_RGB2HSV)
    v=hsv[mask.astype(bool)]
    theta=np.deg2rad(v[:,0].astype(float))
    sin_mean=float(np.sin(theta).mean())
    cos_mean=float(np.cos(theta).mean())
    resultant=min(1.0,float(np.hypot(sin_mean,cos_mean)))
    f={'h_circ_mean_deg':float(np.rad2deg(np.arctan2(sin_mean,cos_mean))%360),
       'h_circ_sd_deg':float(np.rad2deg(np.sqrt(max(0,-2*np.log(max(resultant,1e-12)))))),
       'h_sin_mean':sin_mean,'h_cos_mean':cos_mean,
       's_mean':float(v[:,1].mean()),'s_sd':float(v[:,1].std(ddof=1)),
       'v_mean':float(v[:,2].mean()),'v_sd':float(v[:,2].std(ddof=1))}
    for i,(channel,bins,maxv) in enumerate([('h',18,360),('s',16,1),('v',16,1)]):
        counts,_=np.histogram(v[:,i],bins=bins,range=(0,maxv))
        for j,count in enumerate(counts):
            f[f'{channel}_hist_{j:02d}']=float(count/counts.sum())
    return f

def masked_glcm(gray: np.ndarray, mask: np.ndarray, distance: int, levels: int=32) -> np.ndarray:
    """Symmetric co-occurrences with BOTH members inside the seed.

    Gray quantization is global floor(gray*32/256); no per-seed rescaling.
    Directions are 0,45,90,135 degrees with nearest-integer pixel offsets.
    """
    q=np.minimum(gray.astype(np.uint16)*levels//256,levels-1)
    matrices=[]
    for dy,dx in [(0,distance),(distance,distance),(distance,0),(distance,-distance)]:
        y0,y1=max(0,-dy),min(gray.shape[0],gray.shape[0]-dy)
        x0,x1=max(0,-dx),min(gray.shape[1],gray.shape[1]-dx)
        a=q[y0:y1,x0:x1]; b=q[y0+dy:y1+dy,x0+dx:x1+dx]
        valid=mask[y0:y1,x0:x1] & mask[y0+dy:y1+dy,x0+dx:x1+dx]
        counts=np.bincount((a[valid]*levels+b[valid]).astype(int),minlength=levels**2).reshape(levels,levels).astype(float)
        counts=counts+counts.T
        matrices.append(counts/counts.sum())
    return np.stack(matrices)

def texture_features(gray: np.ndarray, mask: np.ndarray) -> dict[str,float]:
    mask=mask.astype(bool)
    f={}
    ii,jj=np.indices((32,32))
    for distance in [1,2]:
        pp=masked_glcm(gray,mask,distance)
        contrast=np.sum(pp*(ii-jj)**2,axis=(1,2))
        dissimilarity=np.sum(pp*np.abs(ii-jj),axis=(1,2))
        homogeneity=np.sum(pp/(1+(ii-jj)**2),axis=(1,2))
        asm=np.sum(pp**2,axis=(1,2))
        entropy=-np.sum(pp*np.log2(np.maximum(pp,1e-16)),axis=(1,2))
        ux=np.sum(pp*ii,axis=(1,2)); uy=np.sum(pp*jj,axis=(1,2))
        vx=np.sum(pp*(ii-ux[:,None,None])**2,axis=(1,2))
        vy=np.sum(pp*(jj-uy[:,None,None])**2,axis=(1,2))
        cov=np.sum(pp*(ii-ux[:,None,None])*(jj-uy[:,None,None]),axis=(1,2))
        correlation=np.divide(cov,np.sqrt(vx*vy),out=np.ones(4),where=vx*vy>1e-20)
        for name,values in [('contrast',contrast),('dissimilarity',dissimilarity),('homogeneity',homogeneity),('asm',asm),('energy',np.sqrt(asm)),('correlation',correlation),('entropy',entropy)]:
            f[f'glcm_{name}_d{distance}']=float(values.mean())
    interior=cv2.erode(mask.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    if not interior.any():
        raise ValueError('No valid interior pixels for local binary patterns')
    lbp=local_binary_pattern(gray,P=8,R=1,method='uniform')
    hist=np.bincount(lbp[interior].astype(int),minlength=10).astype(float)
    for i,val in enumerate(hist/hist.sum()):
        f[f'lbp_{i:02d}']=float(val)
    return f


