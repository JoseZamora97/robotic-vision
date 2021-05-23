# Line follower

## Filtro de color
Para detectar la línea del resto de la pista es necesario emplear un filtro HSV que menos susceptible a 
cambios de iluminación. No obstante, es necesario saber entre que valores del rango del espacio HSV se
encuentra la línea a seguir. Por ello, se ha implementado una pequeña aplicación con *OpenCV* que hace
uso de trackbars ``cv2.createTrackbar`` para seleccionar los valores y extraer la máscara binaria.

- En primer lugar, se crean los trackbars, se necesitan dos por cada canal para poder especificar los
valores máximos y mínimos que pueden obtenerse.

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
- Después se tienen que capturar los valores en el cambio de posición del trackbar esto se hace llamando a la
  función ``update``.
  
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
- Una vez se tienen los valores se crea la máscara

  ````python
  mask = cv2.inRange(im_base, (min_h, min_s, min_v), (max_h, max_s, max_v))
  ````
Ajustando los trackbars se obtiene la siguiente imagen de resultado:

![hsv_color](https://user-images.githubusercontent.com/35663120/109877596-8175db00-7c73-11eb-9cda-f2525edcc2d6.PNG)

**Nota**: La imagen utilizada para extraer este filtro es la imagen de partida del simulador de Unibotics descargada
desde el navegador.

## Estrategia a seguir

A lo largo de todo este estudio se va a intentar probar diferentes métodos para solucionar el problema del seguimiento de la línea. Estos experimentos
van a incrementar en complejidad y se van a exponer los resultados obenidos así como los parámetros que se han usado en la obtención de los
resultados.

### Controlador P

Para comenzar con esta serie de experimentos se comenzó con un controlador P para los giros (velocidad angular) y velocidad constante. La idea era encontrar
un valor **kp** tal que fuera capaz de completar el circuito con la restricción de seguir la línea lo máximo posible y, progresivamente, incrementar dicha
velocidad.

Para comenzar el análisis se recibe la imagen desde `HAL.getImage()`. De esta imagen se selecciona la mitad inferior y se le pasa el correspondiente filtro
de color extrayendo la imagen binaria de la imagen. A esta última imagen se le calculan los contornos con `cv2.findContours` y los momentos `cv2.moments`.
A partir de esta última operación se calcula el punto *centroide* y con este el error horizontal medido como la diferencia del centro de la imagen con la 
coordenada horizontal del centroide.

El máximo tiempo obtenido con esta configuración fue de 48 segundos, aunque fue obtenido gracias a un error en la carga de la perspectiva de la cámara. Siendo 1 minuto con 15 segundos la media de este controlador. La velocidad máxima que se pudo colocar para la obtención de los resultados tuvo el valor de 2. *(se comprobó con velocidad > 2 hasta un máximo de 3, sin embargo, los constantes vaivenes compensaban la velocidad mayor, por lo que el tiempo era el mismo)*

![controlador_p_vs_2_kph_0 002](https://user-images.githubusercontent.com/35663120/111233530-71ec7f80-85ed-11eb-99a4-2fb3cf073d9d.PNG)

### Controlador PD

Para intentar aplacar los vaivenes presentes en el controlador P se introdujo la componente derivativa a la ecuación del cómputo de la actualización de los giros. Esta consiste en almacenar en una variable el error previo y realizar la resta del nuevo error con este. Ajustando los valores **kp** para la componente proporcional y **kd** para la parte derivativa se obtuvieron mejores tiempos, en torno a los 50 segundos. 

[Video](https://user-images.githubusercontent.com/35663120/111240366-60aa6f80-85fb-11eb-9f3b-0ecd8fc74274.mp4)

Sin embargo, analizar toda la imagen era ineficiente por lo que para mejorar la eficiencia se seleccionaron dos zonas de la imagen, una central y una inferior con la idea de calcular los centroides de ambas zonas y encontrar el punto medio donde calcular error horizontal. Teniendo dichos 3 puntos (2 centroides y el medio) se realizaron tests de estabilidad y velocidad siendo el mejor de ellos el más pegado a la línea del horizonte, bajando la marca a los 38 segundos.

[Video](https://user-images.githubusercontent.com/35663120/111241034-9a2faa80-85fc-11eb-8ffe-62ea51678348.mp4)

### Controlador PDI

Para completar el controlador PDI se le incorporó la componente integral, esta acumula los errores derivativos desde que el error es distinto 0. En este caso se bajó 1 segundo el tiempo anterior y se mejoró un poco la estabilidad.

[Video](https://user-images.githubusercontent.com/35663120/111397183-f0662180-86c0-11eb-923b-32e0a013b515.mp4)

## Añadiendo velocidad variable

Los controladores anteriores funcionaban de manera correcta para una velocidad dada. Esta velocidad era constante, lo cual tenía sus limitaciones. En primer lugar, se perdía mucho tiempo en las rectas, ya que existe un compromiso implícito entre la velocidad en curvas y rectas debido a la inercialidad del sistema. En segundo lugar, al ser alta la velocidad se produce inestabilidad en las salidas de las curvas, y en las curvas consecutivas entra en juego la no determinación del sistema produciendo colisiones en ocasiones. Por último, la velocidad constante dificulta las correcciones, similar al anterior, producto de la inercialidad del sistema.

### Controlador PDI + Velocidad Variable I
A pesar de los inconvenientes anteriormente mencionados, la velocidad constante permitió descubrir cual es la velocidad máxima con la que el coche puede atravesar las curvas sin producir mucha inestabilidad. Teniendo esto último en cuenta se plantea la primera variante de controlador de velocidad.

La idea es calcular el ángulo que forma el centroide superior con el centro de la imagen, para ello se hace uso de la función `arctg(h/b)` donde `h` es la distancia entre centroides y b es la distancia del centroide superior con el centro de la imagen. (*la figura siguiente ilustra la idea*).

![v_primer](https://user-images.githubusercontent.com/35663120/111803036-f16c9e00-88ce-11eb-8ffe-c4b2e6cc7741.png)

El valor absoluto  del ángulo resultante siempre es menor que 90º, (*ya que cuando es 90 quiere decir que los puntos están alineados y es imposible que sea mayor ya que se tratan de angulos interiores de un triángulo rectángulo*). Se puede obtener entonces, la proporción `ratio_v = alpha/90` que estará en el intervalo (0, 1). Esta proporción será cercana a 1 en rectas y cercana a 0 en curvas. Con esto en mente se puede especificar dos valores de velocidad un `vmax` que será la velocidad máxima que puede tomar el coche y `vmin` que será el límite inferior. La velocidad a aplicar en cada instante de tiempo se calcula como `curr_v = ratio_v * vmax`, en caso de que dicha velocidad sea inferior a `vmin` será esta `vmin` el valor actual a aplicar. 

Al ejecutar el ejercicio:
- Con `vmin=1.7` y `vmax=3.0` se obtiene un tiempo de 45 segundos, se sale en algunas curvas y tiene pocas oscilaciones.
- Con `vmin=2.0` y `vmax=4.0` se obtiene un tiempo de 37 segundos, se sale en algunas curvas y comienza a oscilar en algunas curvas.
- Con `vmin=2.0` y `vmax=4.5` se obtiene un tiempo de 32 segundos, se sale en algunas curvas y, *para mi sorpresa* no osciló en las curvas como antes. Al salir de una curva se incorporaba con naturalidad al centro.
- Con `vmin=2.5` y `vmax=4.5` se obtiene un tiempo de 31 segundos, se sale en algunas curvas y, como antes, presenta naturalidad en su comportamiento.
- Con `vmax=5` choca en la primera curva.
- Con `vmin=3` y `vmax=4.8` se obtiene un tiempo de 29 segundos, se sale en todas las curvas y comienza a oscilar como en la segunda ejecución.
- Con `vmin=3.5` y `vmax=4.8` se obtiene un tiempo de 27 segundos, comportamiento idéntico al anterior.

Como se puede ver, se ha llevado al límite a este controlador en cuanto a velocidad a costa de estabilidad y seguimiento de línea.

### Controlador PDI + Velocidad Variable II

Siguiendo con la idea anterior, se plantea esta vez el cálculo del ratio de la velocidad de forma similar, esta vez, utilizando el centroide inferior. 

![v_primer](https://user-images.githubusercontent.com/35663120/111809495-575c2400-88d5-11eb-9e1d-bd6d52a6e182.png)

La idea es controlar, no solo la velocidad antes de las curvas, sino durante las curvas, ya que en mitad de una el centroide superior se situa en el centro casi siempre. Esta vez la velocidad a aplicar va a ser la resultante de la ecuación `a * v_ratio_sup + (1 - a) * v_ratio_inf` de esta forma si `a = 1` tenemos el caso anterior.

Al ejecutar el ejercicio:
- Con `vmin=2.0`, `vmax=4.5` y `a=0.5` se obtiene un tiempo de 35 segundos, peor que su equivalente anterior en todos los aspectos. Aunque después de las curvas se nota cierta mejoría.
- Con `vmin=2.0`, `vmax=4.5` y `a=0.8` se igualó en tiempo al anterior y tiene más estabilidad en curvas, sobretodo, en las curvas consecutivas.
- Con `vmin=3.5`, `vmax=4.8` y `a=0.8` se obtiene un tiempo de 26 segundos. Un segundo por debajo a su equivalente y más estable.

Este controlador, mejora la estabilidad de la ejecución del ejercicio en las curvas como se pensaba, no obstante, al llevar al límite dicho ejercicio, es inevitable que se salga de las curvas que están inmediatamente después de una recta, ya que en rectas se va a velocidad máxima y la variación de dicha velocidad viene indicada por el ángulo de entrada a la curva, esto provoca que los cambios de velocidad sean muy abruptos.

### Controlador PDI + Velocidad Variable III

Para suavizar los cambios de velocidad, se ha pensado en introducir un factor de suavidad `s` que indique cuanto se tiene que cambiar el ratio actual con respecto al anteriormente aplicado, de esta forma, se evitan saltos abruptos de velocidad y los cambios de esta son más orgánicos. Entonces, con esto en cuenta la velocidad a aplicar en cada instante es `s * (a * v_ratio_sup + (1 - a) * v_ratio_inf) + (1 - s) * v_ratio_anterior`. Igual que antes, si `s = 1` tenemos el caso anterior.

- Con `vmin=2.0`, `vmax=4.5`, `a=0.8` y `s=0.5` se obtiene un tiempo de 35 segundos, con un comportamiento más estable que su equivalente anterior.
- Con `vmin=2.0`, `vmax=4.5`, `a=0.8` y `s=0.8` se obtiene un tiempo de 34 segundos, sin muchas diferencias.
- Con `vmin=2.0`, `vmax=4.5`, `a=0.8` y `s=0.2` se obtiene un tiempo de 37 segundos, tiempo peor, aunque la estabilidad se mantiene.
- Con `vmin=3.5`, `vmax=4.8`, `a=0.8` y `s=0.2` se obtiene un tiempo de 26 segundos, muchismo más estable que todos los equivalentes anteriores, aunque solo es cuestión de rapidez en completar el circuito ya que se sale de la línea constantemente en curvas.
- Con `vmin=3.5`, `vmax=5`, `a=0.8` y `s=0.2` se obtiene un tiempo de 25 segundos, siendo el primer controlador lo suficientemente estable como para manejar velocidad 5.

## Camino sobre la línea

Todos expermientos anteriores miden el comportamiento del controlador en situaciones extremas de velocidad para determinar la capacidad de autorregulación *(variando su velocidad y su ángulo de giro)* y autoestabilizarse *(ser capaz de centrarse en el camino una vez se modifica su velocidad o ángulo de giro)*. Sin embargo, la especificación es, desde un principio *seguir la línea con un tiempo inferior a 1 minuto*.

Por ello, se probará el controlador más estable, el **Controlador PDI + Velocidad Variable III** modificando su velocidad mínima y máxima y ajustando los parámetros `a` y `s`.

- Con `vmin=1`, `vmax=3`, `a=0.8` y `s=0.2` se obtiene un tiempo de 47 segundos, completando ambos requisitos de tiempo y seguimiento de la línea.

[Video](https://user-images.githubusercontent.com/35663120/111825051-4d432100-88e7-11eb-82df-a69dfa585b12.mp4)

- Con `vmin=2`, `vmax=3`, `a=0.8` y `s=0.2` se obtiene un tiempo de 40 segundos.

[Video](https://user-images.githubusercontent.com/35663120/111826156-a2336700-88e8-11eb-9044-1f80f1aa7077.mp4)

### Probando en el sentido contrario

Para comprobar el algoritmo del todo, se le dió la vuelta al coche y se probó en sentido contrario, el resultado se muestra en el video siguiente.

[Video](https://user-images.githubusercontent.com/35663120/111835251-fe9c8380-88f4-11eb-91f9-1db7779e6422.mp4)

## Añadiendo robustez

Hasta ahora, se ha completado el circuito siempre que hay una línea *(Follow Line)* en el circuito. Sin embargo, es posible que no haya linea que seguir, es entonces donde hay que añadir un comportamiento que solucione este inconveniente. Para poder comprobar esta característica se forzó un inicio contra la pared. El algoritmo realiza la búsqueda del centroide superior, si no la encuentra gira un poco en una dirección, repitiendo esto hasta encontrar la línea.

[Video](https://user-images.githubusercontent.com/35663120/111835346-22f86000-88f5-11eb-9d1f-d73ed2c5bf87.mp4)

# Funciones importantes

A lo largo de todo este post, se han mencionado por encima las funciones utilizadas, en este apartado se pretende explicarlas con un poco más de profundidad.

## Filtro de color

````python
def color_filter(img):
    import cv2
    
    # Definir el rango de los valores HSV
    MIN_HSV_LINE, MAX_HSV_LINE = (0, 77, 56), (0, 255, 255)
    
    # Conversión del color
    im_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Cálculo de la máscara
    im_line_mask = cv2.inRange(im_hsv, MIN_HSV_LINE, MAX_HSV_LINE)
    _, im_line_mask = cv2.threshold(im_line_mask, 248, 255, cv2.THRESH_BINARY)
    return im_line_mask
````

## Cálculo de los momentos

En esta función `cnt` es el primer contorno *(el más grande)* de `cv2.findContours`.

````python
def get_moments(cnt):
    import cv2
    M = cv2.moments(cnt)
    if M['m00'] > 0:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
    else:
        # Si no se pudo calcular.
        cx = cy = -1
    return cx, cy
````

## Cálculo de errores

````python
def compute_errors(err, prev_err, accum_err, console):
    # Reemplazar _ con los correspondientes valores
    kp, kd, ki = _, _, _ 
    
    p_err = - kp * err
    d_err = - kd * (err - prev_err)
    i_err = - ki * accum_err
    
    # Ecuación del controlador PDI
    pdi = p_err + d_err + i_err
    
    return pdi
````

## Cálculo del ratio de velocidad

````python
def speed_v_modulator_on_curve(h, b):
    import math
    # Cálculo del ángulo en radianes
    rads = math.atan(abs(h/(b + 1e-8)))
    # Conversión a grados
    alpha = math.degrees(rads)
    # Cálculo del ratio
    v_ratio = alpha / 90
    return v_ratio
````
