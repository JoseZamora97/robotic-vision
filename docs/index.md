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

Para comenzar con esta serie de experimentos se comenzó con un controlador P para los giros (velocidad angular) y velocidad lineal. La idea era encontrar
un valor **kp** tal que fuera capaz de completar el circuito con la restricción de seguir la línea lo máximo posible y, progresivamente, incrementar dicha
velocidad.

Para comenzar el análisis se recibe la imagen desde `HAL.getImage()`. De esta imagen se selecciona la mitad inferior y se le pasa el correspondiente filtro
de color extrayendo la imagen binaria de la imagen. A esta última imagen se le calculan los contornos con `cv2.findContours` y los momentos `cv2.moments`.
A partir de esta última operación se calcula el punto *centroide* y con este el error horizontal medido como la diferencia del centro de la imagen con la 
coordenada horizontal del centroide.



