# 3D Reconstruction

En este ejercicio se pretende realizar una reconstrucción de una escena en tres dimensiones a partir de dos imágenes capturadas por un para estéreo calibrado.

## Desarrollando el ejercicio

Para realizar la reconstrucción 3D de un escena se puede trabajar de múltiples formas, pero todas tienen en común la utilización de la geometría epipolar, pero antes de entrar en detalles, voy a explicar el proceso a seguir.

En primer lugar se buscarán pares de puntos homólogos, este procedimiento se puede realizar de muchas formas y de hecho, para este ejercicio, probe con varias. Una de ellas fue intentar extraer características con métodos como el *SIFT* y el *ORB* y luego hacer matching de estos puntos con *FLANN* y *BFM*, pero la versión de *OpenCV* que se emplea en el simulador es la 3.2 y no contiene estos métodos, o al menos no conseguí implementarlos como con otras versiones. Después de esto intenté utilizar el detector de esquinas de Shi-Tomasi con el método `goodFeaturesToTrack` pero esto resultó en muy pocos puntos y no se veía muy bien la reconstrucción. Por último, se probó el detector de bordes de Canny y fue el que se utilizó al final.

La idea es aplicar Canny y detectar los bordes utilizando la información del gradiente *(figura de abajo)*. 

![canny](https://user-images.githubusercontent.com/35663120/119275926-30dda080-bc18-11eb-9d74-eff0c56acee5.png)

Después calcular el rayo de retroproyección que pasa por centro óptico de la cámara de la izquierda que pasa por el punto. Y proyectar dicha recta en la imagen obtenida por la cámara de la derecha. Para realizar este procedimiento se empleó la función `find_directional_ray`, que devuelve una recta expresada como un vector director y un punto y donde se hizo uso de las funciones:

- `HAL.getCameraPosition`: que devuelve la posición de la cámara.
- `HAL.backproject`: reproyecta un punto en 2D al sistema de referencia 3D.
- `HAL.graficToOptical`: que transforma el sistema de coordenada de la imagen al sistema de coordenadas de la cámara.

````python
def find_directional_ray(cam_where, point2d):
    y, x = point2d[:2]
    p0 = HAL.getCameraPosition(cam_where)
    p1 = HAL.backproject(cam_where, HAL.graficToOptical(cam_where, [x, y, 1]))[:3]
    return np.append(p1 - p0, [1]), np.append(p0, [1])
````

Una vez se tiene el rayo de retroproyección, es necesario, como se comentó anteriormente, proyectarlo sobre la cámara de la derecha. Para ello se implementó la función 
`find_epipolar_projection` que, a partir de un rayo de retroproyección crea una máscara con la línea epipolar. En esta función, se hizo uso de las funciones 

- `HAL.project`: proyecta un punto en 3D de la escena en un punto 2D del sistema de la imagen. 
- `HAL.opticalToGrafic`: transforma un punto en el sistema 3D de la cámara al sistema de la imagen.

Para realizar esta tarea esta función toma dos puntos de la recta de reproyección y los proyecta en la imagen de la cámara de la derecha, posteriomente, calcula la recta que pasa por ambos puntos en la imagen obteniendo los puntos extremos (para que pueda ocupar toda la imagen). Una vez se tienen estos putnos es facil crear una máscara dibujando una línea de valores `True` sobre una imagen de `False`s con `numpy`. El grosor de la línea epipolar es configurable a través del parámetro `ksize`.

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

Una vez se tiene el punto (en la imagen izquirda) y su proyección epipolar (en la imagen derecha), es necesario buscar su homólogo, en este caso se optó por aplicar la función `matchTemplate` por la imagen de franja epipolar (obtenida tras multiplicar la máscara anterior y la imagen derecha). Obteniendo algo parecido a la imagen siguiente:

![epipolar_matching](https://user-images.githubusercontent.com/35663120/119275931-34712780-bc18-11eb-9a2c-f90e0e63e6e3.png)

Este proceso se llevó a cabo en la función `find_homologous` que dado un punto en 2D y la máscara epipolar es capaz de calcular su homólogo. Para aplicar el algoritmo de `matchTemplate` se usó el ejemplo directo de la documentación, que hace uso también de la función `minMaxLoc` que extrae el mejor match, devolviendo la parte superior izquierda de la región detectada, a la que se le tiene que sumar el ancho de padding de la región, para seleccionar el píxel central. Dicho padding se puede ajustar a través del parámetro `ksize`.

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

El resultado de aplicar este algoritmo varias veces, da como resultado la siguiente figura, donde se muestran una selección aleatoria de unos pocos puntos (por motivos de visibilidad) aunque en el algoritmo final se ejecuta por cada punto presente en la imagen de bordes de `Canny`.

![homologous](https://user-images.githubusercontent.com/35663120/119275933-36d38180-bc18-11eb-9814-61b927e82a84.png)

Una vez se tienen los pares de puntos homólogos se puede calcular ambos rayos de retroproyección y ver donde se cortan para calcular el punto en 3D. Esto en si es un problema puesto que las rectas (debido a las imprecisiones) puenden no llegar a cortarse, sino simplemente cruzarse. Esto se puede solventar en calculando una solución de mínimos cuadrados utilizando la función `np.linalg.lstsq` empleando el punto medio del vector normal a ambos rayos de retroprojección, es decir:

````python
# dr_left: rayo de retroproyección izquierdo
# dr_right: rayo de retroproyección derecho
# n: vector normal a ambos
# cam_right: centro optico de la cámara derecha
# cam_left: centro optico de la cámara izquierda

n = np.cross(dr_left[0][:3], dr_right[0][:3])
A = np.array([dr_left[0][:3], n, -dr_right[0][:3]]).T
b = cam_right - cam_left

alpha, beta = solve_lstsq(A, b)
point3d = (alpha * dr_left[0][:3]) + ((beta / 2) * n)
````

## Resultados y observaciones.

Los resultados se muestran en el siguiente video, en el se ve una reconstruccíon 3D de la escena bastante decente. Estuve buscando la forma de rellenar por completo dicha escena, pero no encontré la forma. El sistema desarrollado no asume que las cámaras son un par estéreo canónico, por lo que es robusto frente a cambios en los extrinsecos de las cámaras.

[Video](https://user-images.githubusercontent.com/35663120/119276209-e3fac980-bc19-11eb-8bc8-4398c9cfa3ee.mp4)

En un primer lugar me lancé en la búsqueda de una solución completamente diferente a esta, intenté encontrar la matriz fundamental para calcular todas las lineas epipolares de todos los píxels y buscar una solución densa. Sin embargo, me encontré con problemas con el SIFT para estimar rapidamente 8 puntos homólogos y así empezar a realizar dicha aproximación. Tuve muchos problemas con la versión de *OpenCV* del simulador que me impidieron avanzar en ese lado y al final opté por esta solución, que es muchísimo mas simple, pero da resultados esperados con la pega de que tarda mucho.
