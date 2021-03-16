[Edit](https://github.com/JoseZamora97/robotic-vision/edit/main/docs/index.md)

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

# Estrategia a seguir

A lo largo de todo este estudio se va a intentar probar diferentes métodos para solucionar el problema del seguimiento de la línea. Estos experimentos
van a incrementar en complejidad y se van a exponer los resultados obenidos así como los parámetros que se han usado en la obtención de los
resultados.

# Controlador P

Para comenzar con esta serie de experimentos se comenzó con un controlador P para los giros (velocidad angular) y velocidad constante. La idea era encontrar
un valor **kp** tal que fuera capaz de completar el circuito con la restricción de seguir la línea lo máximo posible y, progresivamente, incrementar dicha
velocidad.

Para comenzar el análisis se recibe la imagen desde `HAL.getImage()`. De esta imagen se selecciona la mitad inferior y se le pasa el correspondiente filtro
de color extrayendo la imagen binaria de la imagen. A esta última imagen se le calculan los contornos con `cv2.findContours` y los momentos `cv2.moments`.
A partir de esta última operación se calcula el punto *centroide* y con este el error horizontal medido como la diferencia del centro de la imagen con la 
coordenada horizontal del centroide.

El máximo tiempo obtenido con esta configuración fue de 48 segundos, aunque fue obtenido gracias a un error en la carga de la perspectiva de la cámara. Siendo 1 minuto con 15 segundos la media de este controlador. La velocidad máxima que se pudo colocar para la obtención de los resultados tuvo el valor de 2. *(se comprobó con velocidad > 2 hasta un máximo de 3, sin embargo, los constantes vaivenes compensaban la velocidad mayor, por lo que el tiempo era el mismo)*

![controlador_p_vs_2_kph_0 002](https://user-images.githubusercontent.com/35663120/111233530-71ec7f80-85ed-11eb-99a4-2fb3cf073d9d.PNG)

# Controlador PD

Para intentar aplacar los vaivenes presentes en el controlador P se introdujo la componente derivativa a la ecuación del cómputo de la actualización de los giros. Esta consiste en almacenar en una variable el error previo y realizar la resta del nuevo error con este. Ajustando los valores **kp** para la componente proporcional y **kd** para la parte derivativa se obtuvieron mejores tiempos, en torno a los 50 segundos. 

https://user-images.githubusercontent.com/35663120/111240366-60aa6f80-85fb-11eb-9f3b-0ecd8fc74274.mp4

Sin embargo, analizar toda la imagen era ineficiente por lo que para mejorar la eficiencia se seleccionaron dos zonas de la imagen, una central y una inferior con la idea de calcular los centroides de ambas zonas y encontrar el punto medio donde calcular error horizontal. Teniendo dichos 3 puntos (2 centroides y el medio) se realizaron tests de estabilidad y velocidad siendo el mejor de ellos el más pegado a la línea del horizonte, bajando la marca a los 38 segundos.

https://user-images.githubusercontent.com/35663120/111241034-9a2faa80-85fc-11eb-8ffe-62ea51678348.mp4

# Controlador PDI

Para completar el controlador PDI se le incorporó la componente integral, esta acumula los errores derivativos desde que el error no es 0. En este caso se bajó 1 segundo el tiempo anterior y se mejoró un poco la estabilidad.





