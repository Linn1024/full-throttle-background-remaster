"""Scene-coordinate maps including two-pixel atlas filtering gutters."""
import cv2
import numpy as np
from scene_assets import triangle_pixels

def scene_maps(chunk,tex,padding=2):
 w,h=tex['image'].size;mx=np.full((h,w),-1,np.float32);my=mx.copy();inside_all=np.zeros((h,w),bool)
 yy,xx=np.mgrid[:h,:w].astype('float32');points=np.stack([xx+.5,yy+.5,np.ones_like(xx)],axis=-1)
 triangles=[]
 for ids in chunk['indices'][tex['first']:tex['first']+tex['count']].reshape(-1,3):
  v=chunk['vertices'][ids];uv=np.float32(v[:,2:]*(w,h));r=triangle_pixels(uv,w,h)
  if r is None:continue
  lo,hi,weights,inside=r;mask=np.zeros((h,w),np.uint8);mask[lo[1]:hi[1],lo[0]:hi[0]]=inside
  inside_all|=mask>0;A=cv2.getAffineTransform(uv,np.float32(v[:,:2]/2));triangles.append((mask,A))
 # Fill only the empty gutter after collecting all real coverage. Extrapolate
 # from the same scene rather than copying stale original atlas edge colors.
 for mask,A in triangles:
  selected=(cv2.dilate(mask,np.ones((2*padding+1,2*padding+1),np.uint8))>0)&~inside_all
  xy=points@A.T;mx[selected]=xy[:,:,0][selected];my[selected]=xy[:,:,1][selected]
 for mask,A in triangles:
  selected=mask>0;xy=points@A.T;mx[selected]=xy[:,:,0][selected];my[selected]=xy[:,:,1][selected]
 return mx,my,inside_all
