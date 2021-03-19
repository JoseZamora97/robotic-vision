from GUI import GUI
from HAL import HAL

import cv2
import math


def color_filter(img):
    # Color filter:
    # - img: np.array with the image
    # returns im_line_mask: np.array with the masked image.
    import cv2
    MIN_HSV_LINE, MAX_HSV_LINE = (0, 77, 56), (0, 255, 255)
    im_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    im_line_mask = cv2.inRange(im_hsv, MIN_HSV_LINE, MAX_HSV_LINE)
    _, im_line_mask = cv2.threshold(im_line_mask, 248, 255, cv2.THRESH_BINARY)
    return im_line_mask

def get_moments(cnt):
    # Compute moments
    # - cnt: greater contourn calculated by cv2.findContours
    # returns (cx, cy): tuple with centroid coordinates.
    import cv2
    M = cv2.moments(cnt)
    if M['m00'] > 0:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
    else:
        cx = cy = -1
    return cx, cy

def compute_errors(err, prev_err, accum_err):
    # Compute the P, D, I errors
    # - err: float, current error
    # - prev_err: float, previous error
    # - accum_err: float, sum of all previous errors
    # returns: pdi: float, the PDI value
    
    kp, kd, ki = 0.002 , 0.006, 0.0015
    
    p_err = - kp * err
    d_err = - kd * (err - prev_err)
    i_err = - ki * accum_err
    
    pdi = p_err + d_err + i_err
    
    return pdi

def speed_v_modulator_on_curve(h, b):
    # Compute the ratio between alpha angle and 
    # 90 degrees.
    # - h: int, height of the rect triangle.
    # - b: int, base of the rect triangle.
    # returns: v_ratio: float, the ratio between (0.0, 1.0)
    import math
    rads = math.atan(abs(h/(b + 1e-8)))
    alpha = math.degrees(rads)
    v_ratio = alpha / 90
    return v_ratio


# Initialize previous centroids values
p_cx_t, p_cy_t = -1, -1
p_cx_b, p_cy_b = -1, -1

# Initialize errors
accum_err = prev_err = err = 0

# Initialize speed and previous ratio
v_min, v_max = 2, 3
v_ratio_prev = 0.2

# Initialize `a` and `s` where:
# - a: represents the importance of the centroid speed.
# - s: represents the smoothness of the changes of speed value.
a, s = 0.75, 0.2

# Initial computes for future printing
im = HAL.getImage()
rows, cols = im.shape[:2]
mid_h = cols / 2
mid_v = rows / 2

y0, yf, x0, xf = [mid_v-10, rows-220, 0, cols]
y10, y1f, x10, x1f = [yf, rows, 0, cols]

rect0 = [(x0, y0), (xf, yf)]
rect1 = [(x10, y10), (x1f, y1f)]


# Force Fallback
# -- Uncomment for testing fallback

# for i in range(10):
#     im_fallback = HAL.getImage()
#     GUI.showImage(im_fallback)
#     HAL.motors.sendW(-0.2)
# import time
# time.sleep(2)

# Handle fallback
fallback = True

# Fallback loop:
# - rotate the vehicle till he can see the line.
while fallback:
    im_fallback = HAL.getImage()
    GUI.showImage(im_fallback)
    mask_fallback = color_filter(im_fallback)
    cnt_fallback = cv2.findContours(mask_fallback[y0:yf, x0:xf], 1, 2)[0]
    cx_fallback, cy_fallback = get_moments(cnt_fallback)
    
    if cx_fallback == -1 or cy_fallback == -1:
        HAL.motors.sendW(0.2)
    else:
        p_cx_t = cx_fallback
        p_cy_t = cy_fallback
        # Exit fallback
        fallback = False

# Main Loop
while True:
    # Get image and compute the color filter based mask
    im_or = HAL.getImage()
    mask = color_filter(im_or)
    # Select the 2 fragments of image
    mask_top = mask[y0:yf, x0:xf]
    mask_bottom = mask[y10: y1f, x10:x1f]
    # Compute contours in both fragments
    cnt_top = cv2.findContours(mask_top, 1, 2)[0]
    cnt_bot = cv2.findContours(mask_bottom, 1, 2)[0]    
    # Compute moments of the 2 main contours
    cx_t, cy_t = get_moments(cnt_top)
    cx_b, cy_b = get_moments(cnt_bot)
    # Check the centrois are OK else set the previous
    # centroids values to the new ones.
    cx_t = p_cx_t if cx_t == -1 else cx_t
    cy_t = p_cy_t if cy_t == -1 else cy_t
    cx_b = p_cx_b if cx_b == -1 else cx_b
    cy_b = p_cy_b if cy_b == -1 else cy_b
    # Compute the distance from centroids to the center
    err = (cx_t + x0) - mid_h
    err_b = (cx_b + x10) - mid_h
    # Compute the new W value
    w = compute_errors(err, prev_err, accum_err)
    # Compute h, b, b1 where:
    # - h: the distance between centroids
    # - b, b1: the absolute difference between centroids errors
    h = (cy_b + y10) - (cy_t + y0)
    b = abs(err_b) - abs(err)
    b1 = abs(err) - abs(err_b)
    # Compute the ratios to modulate the speed
    v_ratio_0 = speed_v_modulator_on_curve(h, b)
    v_ratio_1 = speed_v_modulator_on_curve(h, b1)
    # Find the ratio depending on the `a` value
    v_ratio = a * v_ratio_0 + (1 - a) * v_ratio_1
    # Find the ratio depending on the `s` value
    v_ratio = s * v_ratio + (1 - s) * v_ratio_prev
    # Set the speed as the max of the v_min and the v_max modulated
    v = max(v_min, v_max * v_ratio)
    # Send actions
    HAL.motors.sendW(w)
    HAL.motors.sendV(v)
    
    # Update centroids
    p_cx_t, p_cy_t, p_cx_b, p_cy_b = cx_t, cy_t, cx_b, cy_b
    # Update errors
    accum_err += err - prev_err
    prev_err = err
    v_ratio_prev = v_ratio

    # GUI ----------------------------------------------------------

    console.print(["v:", v, "w:", w])
    
    # Draw rectangles
    cv2.rectangle(im_or, rect0[0], rect0[1], (255, 255, 0), 1)
    cv2.rectangle(im_or, rect1[0], rect1[1], (255, 255, 0), 1) 
    
    # Draw important lines
    cv2.line(im_or, (cx_t + x0, cy_t + y0),(cx_b + x10, cy_b + y10), (0, 255, 255), 1 )
    cv2.line(im_or, (mid_h, cy_t + y0), (cx_t + x0, cy_t + y0), (0, 255, 255), 1)
    cv2.line(im_or, (mid_h, cy_b + y10), (cx_b + x10, cy_b + y10), (0, 255, 255), 1)
    cv2.line(im_or, (cx_t + x0, 0), (cx_t+x0, rows), (0, 255, 0), 1)
    cv2.line(im_or, (mid_h, 0), (mid_h, rows), (0, 0, 255), 1)
    
    # Draw centroids
    cv2.circle(im_or, (cx_t + x0, cy_t + y0), 8, (0, 255, 255), -1)
    cv2.circle(im_or, (cx_b + x10, cy_b + y10), 8, (0, 255, 255), -1)
    
    # Show the image
    GUI.showImage(im_or)