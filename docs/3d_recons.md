# 3D Reconstruction

In this exercise, the aim is to reconstruct a three-dimensional scene from two images captured by a calibrated stereo viewer.

## Developing the exercise

To perform the 3D reconstruction of a scene you can work in multiple ways, but all have in common the use of epipolar geometry, but before going into details, I will explain the process to follow.

First of all we will look for pairs of homologous points, this procedure can be done in many ways and in fact, for this exercise, I tried several of them. One of them was to try to extract features with methods like *SIFT* and *ORB* and then match these points with *FLANN* and *BFM*, but the version of *OpenCV* used in the simulator is 3.2 and does not contain these methods, or at least I did not manage to implement them as with other versions. After this I tried to use the Shi-Tomasi corner detector with the `goodFeaturesToTrack` method but this resulted in very few points and the reconstruction did not look very good. Finally, the Canny edge detector was tried and was the one used in the end.

The idea is to apply Canny and detect the edges using the gradient information *(figure below)*. 

![canny](https://user-images.githubusercontent.com/35663120/119275926-30dda080-bc18-11eb-9d74-eff0c56acee5.png)

Then calculate the back projection ray passing through the optical center of the camera on the left passing through the point. And project this line on the image obtained by the camera on the right. To perform this procedure we used the function `find_directional_ray`, which returns a line expressed as a director vector and a point and where we made use of the functions:

- `HAL.getCameraPosition`: which returns the camera position.
- `HAL.backproject`: reprojects a 2D point to the 3D reference system.
- `HAL.graficToOptical`: transforms the image coordinate system to the camera coordinate system.

````python
def find_directional_ray(cam_where, point2d):
    y, x = point2d[:2]
    p0 = HAL.getCameraPosition(cam_where)
    p1 = HAL.backproject(cam_where, HAL.graficToOptical(cam_where, [x, y, 1]))[:3]
    return np.append(p1 - p0, [1]), np.append(p0, [1])
````

Once the back projection beam is obtained, it is necessary, as previously mentioned, to project it onto the camera on the right. For this purpose, the function `find_epipolar_projection` was implemented, which creates a mask with the epipolar line from a back projection ray. In this function, use was made of the functions:

- `HAL.project`: projects a 3D point of the scene onto a 2D point of the image system. 
- `HAL.opticalToGrafic`: transforms a point in the 3D system from the camera to the image system.

To perform this task this function takes two points of the reprojection line and projects them on the camera image on the right, then, it calculates the line that passes through both points in the image obtaining the extreme points (so that it can occupy the whole image). Once you have these points it is easy to create a mask by drawing a line of `True` values over an image of `False`s with `numpy`. The thickness of the epipolar line is configurable through the `ksize` parameter.

````python
def find_epipolar_projection(cam_where, dr_ray, im_size, ksize=9):
    vd0 = dr_ray[0] + dr_ray[1]
    vd0_projected = HAL.project(cam_where, vd0)

    vd1 = (10 * dr_ray[0]) + dr_ray[1]
    vd1_projected = HAL.project(cam_where, vd1)

    p0 = HAL.opticalToGrafic(cam_where, vd0_projected)
    p1 = HAL.opticalToGrafic(cam_where, vd1_projected)

    vect = p1 - p0

    rect_y = lambda x, v: (v[1] * (x - p0[0]) / v[0]) + p0[1]

    p0 = np.array([0, rect_y(0, vect)]).astype(np.int)
    p1 = np.array([im_size[1], rect_y(im_size[1], vect)]).astype(np.int)

    mask = np.zeros(im_size)
    cv.line(mask, tuple(p0), tuple(p1), (1, 1, 1), ksize)

    return mask.astype(bool)
````

Once you have the point (in the left image) and its epipolar projection (in the right image), it is necessary to find its counterpart, in this case we chose to apply the `matchTemplate` function for the epipolar fringe image (obtained after multiplying the previous mask and the right image). Obtaining something similar to the following image:

![epipolar_matching](https://user-images.githubusercontent.com/35663120/119275931-34712780-bc18-11eb-9a2c-f90e0e63e6e3.png)

This process was carried out in the `find_homologous` function that given a 2D point and the epipolar mask is able to calculate its homologous. To apply the `matchTemplate` algorithm we used the direct example from the documentation, which also makes use of the `minMaxLoc` function that extracts the best match, returning the upper left part of the detected region, to which the padding width of the region has to be added, to select the central pixel. This padding can be adjusted through the `ksize` parameter.

````python
def find_homologous(point2d, im_left, im_right, im_epipolar_mask, ksize=9):
    global left, right

    pad = ksize // 2
    x, y = point2d[:2]
    template = im_left[x - pad:x + 1 + pad, y - pad:y + 1 + pad]

    res = cv.matchTemplate(im_right * im_epipolar_mask, template, cv.TM_CCOEFF_NORMED)
    _, coeff, _, top_left = cv.minMaxLoc(res)

    top_left = np.array(top_left)
    match_point = top_left[::-1] + pad

    return match_point, coeff
````

The result of applying this algorithm several times, results in the following figure, where a random selection of a few points are shown (for visibility reasons) although in the final algorithm it is executed for each point present in the `Canny` edge image.

![homologous](https://user-images.githubusercontent.com/35663120/119275933-36d38180-bc18-11eb-9814-61b927e82a84.png)

Once you have the pairs of homologous points you can calculate both back projection rays and see where they intersect to calculate the 3D point. This in itself is a problem since the lines (due to inaccuracies) may not actually intersect, but simply cross. This can be solved by calculating a least squares solution using the `np.linalg.lstsq` function using the midpoint of the normal vector to both back projection rays:

````python
# dr_left: left rear projection beam
# dr_right: right back projection ray
# n: vector normal to both
# cam_right: optical center of right camera
# cam_left: optical center of left camera

n = np.cross(dr_left[0][:3], dr_right[0][:3])
A = np.array([dr_left[0][:3], n, -dr_right[0][:3]]).T
b = cam_right - cam_left

alpha, beta = solve_lstsq(A, b)
point3d = (alpha * dr_left[0][:3]) + ((beta / 2) * n)
````

## Results and observations.

The results are shown in the following video, which shows a pretty decent 3D reconstruction of the scene. I was looking for a way to completely fill the scene, but I couldn't find a way. The developed system does not assume that the cameras are a canonical stereo pair, so it is robust to changes in the extrinsics of the cameras.

[Video](https://user-images.githubusercontent.com/35663120/119276209-e3fac980-bc19-11eb-8bc8-4398c9cfa3ee.mp4)

At first, I tried to find the fundamental matrix to calculate all the epipolar lines of all the pixels and look for a dense solution. However, I ran into problems with the SIFT to quickly estimate 8 homologous points to start making such an approximation. I had many problems with the *OpenCV* version of the simulator that prevented me to advance on that side and in the end I opted for this solution, which is much simpler, but gives expected results with the drawback that it takes a long time.
