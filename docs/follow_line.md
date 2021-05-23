# Line follower

## Color filter
To detect the line from the rest of the track it is necessary to use a HSV filter that is less susceptible to illumination changes. However, it is necessary to know between which values of the HSV space range the line to follow lies. Therefore, a small application has been implemented with *OpenCV* that makes use of trackbars ``cv2.createTrackbar`` to select the values and extract the binary mask.

- First, the trackbars are created, two are needed for each channel in order to specify the maximum and minimum values that can be obtained.


Translated with www.DeepL.com/Translator (free version)

  ````python
  cv2.namedWindow(title_window)

  # H - channel ---------------------------------------
  cv2.createTrackbar(trackbar_min_h_name, title_window,
                     0, trackbar_h_values, update)
  cv2.createTrackbar(trackbar_max_h_name, title_window,
                     0, trackbar_h_values, update)

  # S - channel ---------------------------------------
  cv2.createTrackbar(trackbar_min_s_name, title_window,
                     0, trackbar_s_values, update)
  cv2.createTrackbar(trackbar_max_s_name, title_window,
                     0, trackbar_s_values, update)

  # V - channel ---------------------------------------
  cv2.createTrackbar(trackbar_min_v_name, title_window,
                     0, trackbar_v_values, update)
  cv2.createTrackbar(trackbar_max_v_name, title_window,
                         0, trackbar_v_values, update)
  ````
- Then you have to capture the values in the trackbar position change this is done by calling the ``update`` function.
  
  ````python
  min_h = cv2.getTrackbarPos(trackbar_min_h_name, title_window)
  max_h = cv2.getTrackbarPos(trackbar_max_h_name, title_window)

  # S - channel -------------------------------------------------
  min_s = cv2.getTrackbarPos(trackbar_min_s_name, title_window)
  max_s = cv2.getTrackbarPos(trackbar_max_s_name, title_window)

  # V - channel -------------------------------------------------
  min_v = cv2.getTrackbarPos(trackbar_min_v_name, title_window)
  max_v = cv2.getTrackbarPos(trackbar_max_v_name, title_window)
  ````
- Once the values are available, the mask is created.

  ````python
  mask = cv2.inRange(im_base, (min_h, min_s, min_v), (max_h, max_s, max_v))
  ````
By adjusting the trackbars the following result image is obtained:

![hsv_color](https://user-images.githubusercontent.com/35663120/109877596-8175db00-7c73-11eb-9cda-f2525edcc2d6.PNG)

**Note**: The image used to extract this filter is the starting image of the Unibotics simulator downloaded from the browser.

## Strategy to follow

Throughout this study we are going to try different methods to solve the line tracking problem. These experiments are going to increase in complexity and we are going to expose the results obtained as well as the parameters that have been used in obtaining the results.

### Controller P

To begin with this series of experiments we started with a P controller for the turns (angular velocity) and constant velocity. The idea was to find a value **kp** such that it would be able to complete the circuit with the constraint of following the line as much as possible and progressively increase the speed.

To start the analysis the image is received from `HAL.getImage()`. From this image the lower half is selected and the corresponding color filter is passed to extract the binary image from the image. To this last image the contours are calculated with `cv2.findContours` and the moments `cv2.moments`. From this last operation the *centroid* point is calculated and with this the horizontal error measured as the difference of the center of the image with the horizontal coordinate of the centroid. horizontal coordinate of the centroid.

The maximum time obtained with this configuration was 48 seconds, although it was obtained thanks to an error in the loading of the camera perspective. Being 1 minute and 15 seconds the average of this controller. The maximum speed that could be placed to obtain the results had the value of 2. *(it was tested with speed > 2 up to a maximum of 3, however, the constant back and forth compensated the higher speed, so the time was the same)*.

![controlador_p_vs_2_kph_0 002](https://user-images.githubusercontent.com/35663120/111233530-71ec7f80-85ed-11eb-99a4-2fb3cf073d9d.PNG)

### PD Controller

In order to try to appease the oscillations present in the P controller, the derivative component was introduced to the equation of the computation of the update of the turns. This consists of storing the previous error in a variable and subtracting the new error from it. By adjusting the values **kp** for the proportional component and **kd** for the derivative part, better times were obtained, around 50 seconds.

[Video](https://user-images.githubusercontent.com/35663120/111240366-60aa6f80-85fb-11eb-9f3b-0ecd8fc74274.mp4)

However, analyzing the whole image was inefficient, so to improve efficiency, two areas of the image were selected, a central one and a lower one, with the idea of calculating the centroids of both areas and finding the middle point where to calculate the horizontal error. Having these 3 points (2 centroids and the middle one), stability and speed tests were performed, the best of them being the one closest to the horizon line, lowering the mark to 38 seconds.

[Video](https://user-images.githubusercontent.com/35663120/111241034-9a2faa80-85fc-11eb-8ffe-62ea51678348.mp4)

### PDI Controller

To complete the PDI controller, the integral component was added, which accumulates the derivative errors since the error is different from 0. In this case, the previous time was reduced by 1 second and the stability was improved a little.

[Video](https://user-images.githubusercontent.com/35663120/111397183-f0662180-86c0-11eb-923b-32e0a013b515.mp4)

## Adding variable speed

Previous controllers worked correctly for a given speed. This speed was constant, which had its limitations. Firstly, a lot of time was lost on the straights, as there is an implicit trade-off between speed on curves and straights due to the inertiality of the system. Secondly, the high speed causes instability at the exits of the curves, and in consecutive curves the non-determinism of the system comes into play, sometimes producing collisions. Finally, the constant speed makes corrections difficult, similar to the previous one, due to the inertia of the system.

### PDI Controller + Variable Speed I
Despite the aforementioned drawbacks, the constant speed allowed us to discover the maximum speed at which the car can go through the curves without producing too much instability. With the latter in mind, the first variant of the speed controller is proposed.

The idea is to calculate the angle formed by the upper centroid with the center of the image, for this we make use of the function `arctg(h/b)` where `h` is the distance between centroids and b is the distance of the upper centroid with the center of the image. (*the following figure illustrates the idea*).

![v_primer](https://user-images.githubusercontent.com/35663120/111803036-f16c9e00-88ce-11eb-8ffe-c4b2e6cc7741.png)

The absolute value of the resulting angle is always less than 90º, (*since when it is 90 it means that the points are aligned and it is impossible for it to be greater since they are interior angles of a right triangle*). We can then obtain the ratio `ratio_v = alpha/90` which will be in the interval (0, 1). This ratio will be close to 1 for straight lines and close to 0 for curves. With this in mind you can specify two speed values `vmax` which will be the maximum speed the car can take and `vmin` which will be the lower limit. The speed to apply at each instant of time is calculated as `curr_v = ratio_v * vmax`, in case this speed is lower than `vmin` will be this `vmin` the actual value to apply. 

When executing the exercise:
- With `vmin=1.7` and `vmax=3.0` a time of 45 seconds is obtained, it goes out in some curves and has few oscillations.
- With `vmin=2.0` and `vmax=4.0` a time of 37 seconds is obtained, it goes out in some curves and starts to oscillate in some curves.
- With `vmin=2.0` and `vmax=4.5` you get a time of 32 seconds, it comes out in some corners and, *to my surprise* it didn't oscillate in the corners as before. Coming out of a corner it naturally merged into the center.
- With `vmin=2.5` and `vmax=4.5` a time of 31 seconds is obtained, it comes out in some curves and, as before, presents naturalness in its behavior.
- With `vmax=5` it crashes in the first curve.
- With `vmin=3` and `vmax=4.8` a time of 29 seconds is obtained, it goes out in all the curves and begins to oscillate as in the second execution.
- With `vmin=3.5` and `vmax=4.8` a time of 27 seconds is obtained, identical behavior to the previous one.

As can be seen, this controller has been pushed to the limit in terms of speed at the expense of stability and line tracking.

### PDI Controller + Variable Speed II

Continuing with the previous idea, the calculation of the speed ratio is approached this time in a similar way, this time using the lower centroid.

![v_primer](https://user-images.githubusercontent.com/35663120/111809495-575c2400-88d5-11eb-9e1d-bd6d52a6e182.png)

The idea is to control, not only the speed before the curves, but also during the curves, since in the middle of a curve the upper centroid is almost always located in the center. This time the speed to apply is going to be the resultant of the equation `a * v_ratio_sup + (1 - a) * v_ratio_inf` so if `a = 1` we have the previous case.

By executing the exercise:
- `vmin=2.0`, `vmax=4.5` and `a=0.5` we get a time of 35 seconds, worse than its previous equivalent in all respects. Although some improvement is noted after the curves.
- With `vmin=2.0`, `vmax=4.5` and `a=0.8` it was equal in time to the previous one and has more stability in curves, above all, in consecutive curves.
- With `vmin=3.5`, `vmax=4.8` and `a=0.8` a time of 26 seconds is obtained. One second below its equivalent and more stable.

This controller, improves the stability of the execution of the exercise in the curves as it was thought, nevertheless, when taking to the limit this exercise, it is inevitable that one leaves the curves that are immediately after a straight line, since in straight lines one goes to maximum speed and the variation of this speed is indicated by the angle of entrance to the curve, this causes that the changes of speed are very abrupt.

### PDI + Variable Speed Controller III

To smooth the speed changes, it has been thought to introduce a smoothness factor `s` that indicates how much the current ratio has to be changed with respect to the previously applied one, in this way, abrupt speed jumps are avoided and the speed changes are more organic. So, with this in mind the speed to apply at each instant is `s * (a * v_ratio_up + (1 - a) * v_ratio_inf) + (1 - s) * v_ratio_previous`. As before, if `s = 1` we have the previous case.

- With `vmin=2.0`, `vmax=4.5`, `a=0.8` and `s=0.5` we obtain a time of 35 seconds, with a more stable behavior than its previous equivalent.
- With `vmin=2.0`, `vmax=4.5`, `a=0.8` and `s=0.8` a time of 34 seconds is obtained, without much difference.
- With `vmin=2.0`, `vmax=4.5`, `a=0.8` and `s=0.2` a time of 37 seconds is obtained, a worse time, although stability is maintained.
- With `vmin=3.5`, `vmax=4.8`, `a=0.8` and `s=0.2` a time of 26 seconds is obtained, much more stable than all the previous equivalents, although it is only a question of speed in completing the circuit since it constantly goes out of line in curves.
- With `vmin=3.5`, `vmax=5`, `a=0.8` and `s=0.2` a time of 25 seconds is obtained, the first controller being stable enough to handle speed 5.

## Path over the line

All of the above experiments measure the behavior of the controller in extreme speed situations to determine the ability to self-regulate *(varying its speed and turning angle)* and self-stabilize *(being able to center itself on the path once its speed or turning angle is modified)*. However, the specification is, from the outset *to follow the line with a time of less than 1 minute*.

Therefore, the most stable controller, the **PDI Controller + Variable Speed III** will be tested by modifying its minimum and maximum speed and adjusting the `a` and `s` parameters.

- With `vmin=1`, `vmax=3`, `a=0.8` and `s=0.2` a time of 47 seconds is obtained, completing both timing and line tracking requirements.

[Video](https://user-images.githubusercontent.com/35663120/111825051-4d432100-88e7-11eb-82df-a69dfa585b12.mp4)

- With `vmin=2`, `vmax=3`, `a=0.8` and `s=0.2` a time of 40 seconds is obtained.

[Video](https://user-images.githubusercontent.com/35663120/111826156-a2336700-88e8-11eb-9044-1f80f1aa7077.mp4)

### Testing in the opposite direction

To test the whole algorithm, the car was turned around and tested in the opposite direction, the result is shown in the video below.

[Video](https://user-images.githubusercontent.com/35663120/111835251-fe9c8380-88f4-11eb-91f9-1db7779e6422.mp4)

## Adding robustness

So far, the circuit has been completed whenever there is a *(Follow Line)* in the circuit. However, it is possible that there is no line to follow, it is then where a behavior needs to be added that addresses this drawback. In order to test this feature, a start was forced against the wall. The algorithm performs the search for the upper centroid, if it does not find it turns a little in one direction, repeating this until the line is found.

[Video](https://user-images.githubusercontent.com/35663120/111835346-22f86000-88f5-11eb-9d1f-d73ed2c5bf87.mp4)

# Important functions

Throughout this post, the functions used have been mentioned above, in this section we intend to explain them in a little more depth.

## Color filter

````python
def color_filter(img):
    import cv2
    
    # Define the range of HSV values
    MIN_HSV_LINE, MAX_HSV_LINE = (0, 77, 56), (0, 255, 255)
    
    # Color conversion
    im_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Mask calculation
    im_line_mask = cv2.inRange(im_hsv, MIN_HSV_LINE, MAX_HSV_LINE)
    _, im_line_mask = cv2.threshold(im_line_mask, 248, 255, cv2.THRESH_BINARY)
    return im_line_mask
````

## Moment calculation

In this function `cnt` is the first *(largest)* contour of `cv2.findContours`.

````python
def get_moments(cnt):
    import cv2
    M = cv2.moments(cnt)
    if M['m00'] > 0:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
    else:
        # If it could not be calculated.
        cx = cy = -1
    return cx, cy
````

## Error calculation

````python
def compute_errors(err, prev_err, accum_err, console):
    # Replace _ with the corresponding values
    kp, kd, ki = _, _, _ 
    
    p_err = - kp * err
    d_err = - kd * (err - prev_err)
    i_err = - ki * accum_err
    
    # PDI controller equation
    pdi = p_err + d_err + i_err
    
    return pdi
````

## Speed ratio calculation

````python
def speed_v_modulator_on_curve(h, b):
    import math
    
    # Calculation of the angle in radians
    rads = math.atan(abs(h/(b + 1e-8)))
    
    # Conversion to degrees
    alpha = math.degrees(rads)
    
    # Ratio calculation
    v_ratio = alpha / 90
    return v_ratio
````
