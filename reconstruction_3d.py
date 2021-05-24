from GUI import GUI
from HAL import HAL

import cv2 as cv
import numpy as np
import random


def find_directional_ray(cam_where, point2d):
    """
    Compute the back-projection ray that goes from optical center or
    camera `cam_where` through the point2d
    :param cam_where: Can be 'left' or 'right'
    :param point2d: Point 2D where the ray pass through
    :return: A Rect represented by a director vector and a point.
    """
    y, x = point2d[:2]
    p0 = HAL.getCameraPosition(cam_where)
    p1 = HAL.backproject(cam_where, HAL.graficToOptical(cam_where, [x, y, 1]))[:3]
    return np.append(p1 - p0, [1]), np.append(p0, [1])


def solve_lstsq(A, b):
    """
    Solve the system Ax=b by least-square method.
    :param A: A
    :param b: b
    :return: Solution
    """
    x0, x1, _ = np.linalg.lstsq(A, b)[0]
    return x0, x1


def find_epipolar_projection(cam_where, dr_ray, im_size, ksize=9):
    """
    Compute a epipolar projection from a back-projection ray to a camera image.
    :param cam_where: Can be 'left' or 'right'
    :param dr_ray: The back-projection ray
    :param im_size: The size of the mask
    :param ksize: The thickness of the line in mask.
    :return:
    """

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


def find_homologous(point2d, im_left, im_right, im_epipolar_mask, ksize=9):
    """
    Performs matchTemplate algorithm finding the point2d homologous in im_right
    by creating a template with size ksize for comparison.
    :param point2d:
    :param im_left: Left image
    :param im_right: Right image
    :param im_epipolar_mask: Image Mask with the epipolar line on it
    :param ksize: The template size
    :return: tuple ( point2d Homologous point, confidence)
    """
    global left, right

    pad = ksize // 2
    x, y = point2d[:2]
    template = im_left[x - pad:x + 1 + pad, y - pad:y + 1 + pad]

    # OpenCV example code.
    res = cv.matchTemplate(im_right * im_epipolar_mask, template, cv.TM_CCOEFF_NORMED)
    _, coeff, _, top_left = cv.minMaxLoc(res)

    top_left = np.array(top_left)
    match_point = top_left[::-1] + pad

    return match_point, coeff


window_size = 11                # The size of the epipolar line projection mask and the templateMatching template size
left, right = 'left', 'right'   # Save the camera names
amount_of_points = 100000       # See the amount of points to show (normally are 18k points)

im_left = HAL.getImage(left)
im_right = HAL.getImage(right)

cam_left = HAL.getCameraPosition(left)
cam_right = HAL.getCameraPosition(right)

mask = cv.Canny(im_left, 100, 200)   # Canny edge detection with default params by Opencv examples.

points2d = []  # Take point coordinates where the Canny mask is True.
for x, y in np.ndindex(*im_left.shape[:2]):
    if mask[x, y]:
        points2d.append([x, y])

# Pick a sample of points to execute the algorithm
points2d = random.sample(points2d, amount_of_points)

points3d_scene = []
for i, point2d in enumerate(points2d):

    # Compute back-projection left ray

    dr_left = find_directional_ray(left, point2d)
    # Project the ray in image right & find homologous on it
    im_ep_mask = find_epipolar_projection(right, dr_left, im_left.shape, ksize=window_size)
    point2d_h, coeff = find_homologous(point2d, im_left, im_right, im_ep_mask, ksize=window_size)

    if coeff > 0.9:  # if confidence is high enough
        # Compute back-projection right ray
        dr_right = find_directional_ray(right, point2d_h)

        # Create the system Ax=b for least-square solve.
        n = np.cross(dr_left[0][:3], dr_right[0][:3])
        A = np.array([dr_left[0][:3], n, -dr_right[0][:3]]).T
        b = cam_right - cam_left

        alpha, beta = solve_lstsq(A, b)

        # Compute the 3D points using least-square solutions
        point3d = (alpha * dr_left[0][:3]) + ((beta / 2) * n)
        point3d_scene = HAL.project3DScene(point3d).tolist()

        # Compute the pixel 3D color by calculating the average of
        # the two 2D pixel colors
        color_px_left = im_left[point2d[0], point2d[1]]
        color_px_right = im_right[point2d_h[0], point2d_h[1]].tolist()
        color = (color_px_left + color_px_right) // 2

        # Add to the list of points 3D calulated.
        points3d_scene.append(point3d_scene + color.tolist()[::-1])

        print("Point: " + str(i + 1) + " of " + str(len(points2d)))

# Once it ends, show all points computed
GUI.ShowNewPoints(points3d_scene)
