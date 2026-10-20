"""PLP-inspired experimental prototype. This is not the paper's PLP operator."""
import cv2
import numpy as np

def wiener_plane(image, sigma):
    """Single 5x5 local Wiener estimator; independent of the paper operators."""
    x=np.asarray(image,dtype=np.float32)
    mean=cv2.boxFilter(x,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)
    var=np.maximum(cv2.boxFilter(x*x,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)-mean*mean,0)
    gain=np.maximum(var-sigma*sigma,0)/(var+1e-8)
    return mean+gain*(x-mean)

def guided_stage(plane,sigma):
    """Legacy second spatial pass, factored out for an honest ablation."""
    m=cv2.boxFilter(plane,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)
    v=np.maximum(cv2.boxFilter(plane*plane,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)-m*m,0)
    a=v/(v+0.25*sigma*sigma+1e-8);b=m-a*m
    return cv2.boxFilter(a,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)*plane+cv2.boxFilter(b,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)

def latch(image):
    """Nearest 10-bit intensity quantization, not phase wrap or localization."""
    return (np.rint(np.clip(image,0,1)*1023)/1023).astype(np.float32)

def prototype_v2(image,sigma):
    """Edge-retention variant: remove the legacy second smoothing pass.

    This is a single local Wiener estimator plus 10-bit quantization. It trades
    residual noise for less gradient attenuation and less work; quality gains
    are not guaranteed. It is not a validated implementation of PLP equations.
    """
    return latch(wiener_plane(image,sigma))

def prototype(image, sigma, return_stages=False):
    """Plane: local Wiener shrinkage; Line: guided smoothing; Point: 10-bit latching.

    These three numerical choices are independently designed substitutes, not
    discretizations of the undefined surface potential or prime-orbit dynamics.
    Input and sigma are in [0,1]. No clean reference image is used.
    """
    x = np.asarray(image, dtype=np.float32)
    mean = cv2.boxFilter(x, -1, (5,5), borderType=cv2.BORDER_REFLECT_101)
    var = np.maximum(cv2.boxFilter(x*x,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)-mean*mean,0)
    gain = np.maximum(var-sigma*sigma,0)/(var+1e-8)
    plane = mean + gain*(x-mean)
    # An edge-aware local linear model uses the plane result as its guide.
    m = cv2.boxFilter(plane,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)
    v = np.maximum(cv2.boxFilter(plane*plane,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)-m*m,0)
    a = v/(v+0.25*sigma*sigma+1e-8)
    b = m-a*m
    line = cv2.boxFilter(a,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)*plane + cv2.boxFilter(b,-1,(5,5),borderType=cv2.BORDER_REFLECT_101)
    point = (np.rint(np.clip(line,0,1)*1023)/1023).astype(np.float32)
    return (plane,line,point) if return_stages else point

def methods(sigma):
    """Fixed parameters; no tuning on clean benchmark outputs."""
    return {
        'Gaussian':lambda x:cv2.GaussianBlur(x,(5,5),1.0,borderType=cv2.BORDER_REFLECT_101),
        'Bilateral':lambda x:cv2.bilateralFilter(x,7,float(2*sigma),2.0,borderType=cv2.BORDER_REFLECT_101),
        'Median':lambda x:cv2.medianBlur(x,3),
        'PLP-Inspired Experimental Prototype':lambda x:prototype(x,sigma),
    }
