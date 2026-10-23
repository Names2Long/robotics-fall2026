#!/usr/bin/env python3
"""Documented reference for all 16 guided image-playground steps.

Run from any directory with this lab's Python environment. The default image and
manual mug silhouette come from the bundled dataset. Use --image for another BGR
photograph, where the final geometry example uses a threshold mask instead of
pretending to have a manual annotation. No camera or ROS setup is needed.

Every operation starts from the same source image or an explicitly fixed mask.
The returned dictionary lets you reuse individual operations in ROS callbacks.
Do not run this whole demonstration for every camera frame. Copy only the needed
stages and preserve frame timestamps, freshness checks and command limits.
"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np


def demonstrate(image, teaching_mask=None):
    """Return intermediate images and measurements without modifying the input."""
    h,w = image.shape[:2]
    outputs = {'original':image.copy()}
    # 1. Coordinates are (column, row), but NumPy indexes image[row, column].
    x,y = w//2,h//2
    measurements = {'resolution':[w,h],'pixel_xy':[x,y],'pixel_bgr':image[y,x].tolist()}
    outputs['pixel_color'] = np.full((60,60,3),image[y,x],dtype=np.uint8)
    # 2. RGB reverses OpenCV's BGR order. Single channels are strength images.
    rgb = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    for index,name in enumerate(('red','green','blue')): outputs[name] = rgb[:,:,index]
    # 3. Grayscale discards color distinctions and keeps weighted brightness.
    outputs['grayscale'] = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    # 4. Hue is 0..179. Saturation and value are 0..255.
    hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    outputs['hue'] = (hsv[:,:,0].astype(float)*255/179).astype(np.uint8)
    outputs['saturation'],outputs['value'] = hsv[:,:,1],hsv[:,:,2]
    # 5. Resize keeps the full field of view but changes sampling resolution.
    for width in (120,240,480):
        outputs[f'resize_{width}'] = cv2.resize(image,(width,round(h*width/w)),interpolation=cv2.INTER_AREA)
    # 6. Crop removes context, without scaling retained pixels.
    outputs['crop'] = image[:max(1,round(h*.4)),round(w*.48):max(round(w*.81),round(w*.48)+1)].copy()
    # 7. Brightness adds an offset. Contrast multiplies. Clip to byte range.
    outputs['brighter'] = np.clip(image.astype(float)+50,0,255).astype(np.uint8)
    outputs['contrast'] = np.clip(image.astype(float)*1.5,0,255).astype(np.uint8)
    # 8. The same reproducible noisy input is used for both smoothers.
    noisy = image.copy()
    noise = np.random.default_rng(7).random((h,w))
    noisy[noise<.02],noisy[noise>.98] = 0,255
    outputs['noisy'] = noisy
    for size in (3,9):
        outputs[f'gaussian_{size}'] = cv2.GaussianBlur(noisy,(size,size),0)
        outputs[f'median_{size}'] = cv2.medianBlur(noisy,size)
    # 9. A mask selects colors, not object identities. The desk can also pass.
    raw = cv2.inRange(hsv,np.array([0,70,25]),np.array([35,255,180]))
    outputs['raw_mask'] = raw
    # 10..13. Erosion shrinks, dilation expands, opening removes small white
    # specks, closing fills small dark gaps. Never chain these comparisons.
    # 14. Compare all four with the SAME kernel and SAME raw input.
    for size in (1,3,5,9):
        kernel = np.ones((size,size),np.uint8)
        outputs[f'erosion_{size}'] = cv2.erode(raw,kernel)
        outputs[f'dilation_{size}'] = cv2.dilate(raw,kernel)
        outputs[f'opening_{size}'] = cv2.morphologyEx(raw,cv2.MORPH_OPEN,kernel)
        outputs[f'closing_{size}'] = cv2.morphologyEx(raw,cv2.MORPH_CLOSE,kernel)
    # 15. Mission-style contour selection uses a fixed cleaned mask.
    clean = cv2.morphologyEx(outputs['opening_3'],cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    contours,_ = cv2.findContours(clean,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    annotated = image.copy()
    candidates = []
    for index,contour in enumerate(contours):
        area,perimeter = cv2.contourArea(contour),cv2.arcLength(contour,True)
        circularity = 4*np.pi*area/perimeter**2 if perimeter else 0.
        candidates.append({'candidate':index,'area':area,'circularity':circularity,'eligible':area>=300})
        cv2.drawContours(annotated,[contour],-1,(255,0,0),1)
    eligible = [c for c in contours if cv2.contourArea(c)>=300]
    if eligible:
        selected = max(eligible,key=cv2.contourArea)
        bx,by,bw,bh = cv2.boundingRect(selected)
        cv2.rectangle(annotated,(bx,by),(bx+bw,by+bh),(0,255,0),2)
    outputs['contours'],measurements['candidates'] = annotated,candidates
    # 16. A supplied silhouette teaches geometry independently of detection.
    geometry_mask = (teaching_mask.astype(np.uint8)*255) if teaching_mask is not None else clean
    contours,_ = cv2.findContours(geometry_mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    geometry = image.copy()
    if contours:
        contour = max(contours,key=cv2.contourArea)
        bx,by,bw,bh = cv2.boundingRect(contour)
        moments = cv2.moments(geometry_mask,binaryImage=True)
        if moments['m00']:
            centroid = [moments['m10']/moments['m00'],moments['m01']/moments['m00']]
            center = [bx+bw/2,by+bh/2]
            measurements.update(box_center=center,centroid=centroid,geometry_uses_annotation=teaching_mask is not None)
            cv2.rectangle(geometry,(bx,by),(bx+bw,by+bh),(0,255,0),2)
            cv2.circle(geometry,tuple(map(round,center)),6,(0,0,255),2)
            cv2.drawMarker(geometry,tuple(map(round,centroid)),(0,255,255),markerSize=12)
    outputs['geometry'] = geometry
    return outputs,measurements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path)
    parser.add_argument('--output',type=Path,default=Path('runtime/playground_reference'))
    args = parser.parse_args()
    if args.image:
        image,mask = cv2.imread(str(args.image)),None
        if image is None: parser.error('Could not read --image')
    else:
        from perception.dataset import tuning_image,source_mask
        image,mask = tuning_image(),source_mask()
    outputs,measurements = demonstrate(image,mask)
    args.output.mkdir(parents=True,exist_ok=True)
    for name,value in outputs.items():
        if not cv2.imwrite(str(args.output/(name+'.png')),value): raise OSError('Could not save '+name)
    (args.output/'measurements.json').write_text(json.dumps(measurements,indent=2),encoding='utf-8')
    print(f'Saved {len(outputs)} images and measurements in {args.output.resolve()}')


if __name__ == '__main__': main()
