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

````
python
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

Para realizar esta tarea esta función toma dos puntos de la recta de reproyección y los proyecta en la imagen de la cámara de la derecha, posteriomente, calcula la recta que pasa por ambos puntos en la imagen obteniendo los puntos extremos (para que pueda ocupar toda la imagen). Una vez se tienen estos putnos es facil crear una máscara dibujando una línea de valores `True` sobre una imagen de `False`s con `numpy`.

````
python
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



![epipolar_matching](https://user-images.githubusercontent.com/35663120/119275931-34712780-bc18-11eb-9a2c-f90e0e63e6e3.png)

![homologous](https://user-images.githubusercontent.com/35663120/119275933-36d38180-bc18-11eb-9814-61b927e82a84.png)

## Pruebas realizadas

## Resultados
![Video](https://user-images.githubusercontent.com/35663120/119276209-e3fac980-bc19-11eb-8bc8-4398c9cfa3ee.mp4)


## Futuras mejoras
