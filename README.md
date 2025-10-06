# Bienvenidos a "Sidereous: Exoplanet Finder"
Sidereus emplea algoritmos de machine learning, basados en LightGBM, una herramienta open source de Microsoft, para analizar datos tabulares basados en los obtenidos en las misiones K2, TESS y Kepler. A partir de características como el periodo orbital, profundidad de tránsito u otras propiedades estelares, el modelo evalua la probabilidad de que cierto candidato a exoplaneta sea en efecto uno o no. Esto permite optimizar la clasificación de exoplanetas, permitiendo enfocarse en candidatos con alta presición y contribuyendo así, hasta cierto punto, a acelerar el progreso científico en el área de la astronomía y la astrofísica. 
## Acerca del Desafío 
Este proyecto es nuestra solución al desafío "A World Away: Hunting for Exoplanets With IA" del NASA Space App Challenge Costa Rica 2025. 
[Enlace oficial de la competencia](https://www.spaceappschallenge.org/2025/challenges/a-world-away-hunting-for-exoplanets-with-ai/)

## Nuestra Solución 
Sidereus-Exoplanet Finder is a web application built with Flask that uses a LightGBM-based machine learning model to analyze astronomical data from NASA missions such as Kepler, TESS, and K2, aiming to classify exoplanet candidates as real, false, or ambiguous based on parameters like orbital period, transit depth, and stellar characteristics. The app provides an intuitive interface where users can enter data, visualize predictions, and explore model metrics, while the backend handles requests, normalizes the inputs, and returns results in JSON format, automatically adapting the interface language to the user’s browser. To run it locally, the repository must be cloned and executed within a Python virtual environment (venv) to properly isolate dependencies; once the environment is activated, the required libraries listed in the requirements file can be installed, and the Flask server started to access the app through a local address. In essence, Sidereus serves as both an educational and scientific tool that illustrates how artificial intelligence can assist in the detection and classification of exoplanets, making advanced astronomical analysis accessible to students, researchers, and enthusiasts alike.

Sidereus-Exoplanet Finder es una aplicación web desarrollada con Flask que utiliza un modelo de aprendizaje automático basado en LightGBM para analizar datos astronómicos de misiones de la NASA como Kepler, TESS y K2, con el objetivo de clasificar candidatos a exoplanetas como reales, falsos o ambiguos según parámetros como el período orbital, la profundidad del tránsito y las características estelares. La aplicación ofrece una interfaz intuitiva donde los usuarios pueden ingresar datos, visualizar predicciones y explorar métricas del modelo, mientras que el backend gestiona las solicitudes, normaliza los datos de entrada y devuelve los resultados en formato JSON, adaptando automáticamente el idioma de la interfaz al del navegador del usuario. Para ejecutarla localmente, se debe clonar el repositorio y correr el proyecto dentro de un entorno virtual de Python (venv) para aislar correctamente las dependencias; una vez activado el entorno, se instalan las librerías necesarias indicadas en el archivo de requisitos y se inicia el servidor Flask para acceder a la aplicación desde una dirección local. En esencia, Sidereus funciona como una herramienta tanto educativa como científica que demuestra cómo la inteligencia artificial puede asistir en la detección y clasificación de exoplanetas, haciendo que el análisis astronómico avanzado sea accesible para estudiantes, investigadores y entusiastas del espacio.

How to run it step by step:
Prerequisites: Have Python 3.11+ installed (3.12 works as well), along with pip and optionally Git. Make sure you are in the root folder of the project (where app.py and requirements.txt are located).


Windows

Create the environment: python -m venv venv
Activate it: venv\Scripts\activate
(Optional) Update pip: python -m pip install --upgrade pip
Install dependencies: pip install -r requirements.txt
Run the app: python app.py and open http://127.0.0.1:2727/


Linux

Create the environment: python3 -m venv venv
Activate it: source venv/bin/activate
(Optional) Update pip: python -m pip install --upgrade pip
Install dependencies: pip install -r requirements.txt
Run the app: python app.py and open http://127.0.0.1:2727/


macOS

Create the environment: python3 -m venv venv
Activate it: source venv/bin/activate
(Optional) Update pip: python -m pip install --upgrade pip
Install dependencies: pip install -r requirements.txt
• Note for macOS/Apple Silicon: if LightGBM fails to compile, install OpenMP with Homebrew (brew install libomp) and then run pip install lightgbm again.
Run the app: python app.py and open http://127.0.0.1:2727/


Quick Tips:

To change the port: define PORT (Windows: set PORT=3000; Linux/macOS: export PORT=3000) before running python app.py.
To disable debug mode: set FLASK_DEBUG=0.
The prediction endpoint is /api/calculateDisposition (requires at least two of: orbital_period, transit_duration, transit_depth).
If you want real predictions, place the model artifacts inside the model/ folder with the expected filenames (model_lgb.pkl, columns_used.json, thresholds.json, metrics.json). Without them, the interface will load but no inference will occur.


Como correrlo paso a paso:
Requisitos previos: Tener instalado Python 3.11+ (3.12 funciona), pip y Git (opcional). Sitúate en la carpeta raíz del proyecto (donde están app.py y requirements.txt).


Windows

Crea el entorno: python -m venv venv
Actívalo: venv\Scripts\activate
(Opcional) Actualiza pip: python -m pip install --upgrade pip
Instala dependencias: pip install -r requirements.txt
Ejecuta la app: python app.py y abre http://127.0.0.1:2727/


Linux

Crea el entorno: python3 -m venv venv
Actívalo: source venv/bin/activate
(Opcional) Actualiza pip: python -m pip install --upgrade pip
Instala dependencias: pip install -r requirements.txt
Ejecuta la app: python app.py y abre http://127.0.0.1:2727/


macOS

Crea el entorno: python3 -m venv venv
Actívalo: source venv/bin/activate
(Opcional) Actualiza pip: python -m pip install --upgrade pip
Instala dependencias: pip install -r requirements.txt
• Nota macOS/Apple Silicon: si LightGBM da error de compilación, instala OpenMP con Homebrew (brew install libomp) y vuelve a pip install lightgbm.
Ejecuta la app: python app.py y abre http://127.0.0.1:2727/

Consejos rápidos:

Para cambiar el puerto: define PORT (Windows: set PORT=3000; Linux/macOS: export PORT=3000) antes de ejecutar python app.py.
Para desactivar modo debug: define FLASK_DEBUG=0.
El endpoint de predicción es /api/calculateDisposition (requiere al menos dos de: orbital_period, transit_duration, transit_depth).
Si quieres predicciones reales, coloca los artefactos del modelo en la carpeta model/ con los nombres que el servidor espera (model_lgb.pkl, columns_used.json, thresholds.json, metrics.json). Sin ellos, la interfaz carga pero no habrá inferencia.


## Recursos Empleados  
Para la aplicación completa usamos el lenguaje de programación **Python**, el cual nos da flexibilidad de uso al ser interpretado y tener una gran variedad de **librerías de código abierto** fáciles de usar.  

Usamos **estructuras de datos** para almacenar y analizar los datos de manera mucho más dinámica, evitando el *hardcode*, que es cuando los parámetros se implementan de forma estática y difícil de modificar.  

También usamos varias librerías de Python como **NumPy** y **LightGBM**, además de **Flask** para el backend de nuestra aplicación, el cual maneja la lógica del servidor, abriendo puntos de acceso para obtener información del modelo. Este mismo se encarga de dar acceso a la interfaz de usuario, facilitando el uso de la aplicación.  

Para la **interfaz de usuario**, utilizamos **HTML**, **CSS** y **JavaScript**, lo que brinda un acceso simple y organizado a la aplicación.  

Para el **entrenamiento de nuestro modelo de inteligencia artificial**, usamos las bases de datos que la NASA ha brindado sobre exoplanetas, como los **objetos de interés de Kepler y TESS (KOI y TOI)**, así como los datos de **K2**.  

También nos apoyamos en el uso responsable de **inteligencias artificiales** como ChatGPT para completar tareas tediosas, como la generación de estructuras de datos para los exoplanetas, así como para ayudar en la depuración de errores desconocidos, ya que este fue un reto nuevo para todo el equipo. 

## Alcance Potencial 
Implementamos una aplicación de reconocimiento de exoplanetas basada en datos de satélite que es **simple e intuitiva** de usar, brindando una experiencia agradable y educativa para los entusiastas del espacio.  

También decidimos usar **GitHub** para que nuestra aplicación fuera de **código abierto**, permitiendo que cualquier persona interesada en innovar con una aplicación similar pueda hacerlo, o incluso colaborar directamente con este proyecto.  

## Innovación
Nuestra aplicación implementa la detección de exoplanetas de una forma **sencilla y accesible** para los usuarios. Además, expone **puntos de acceso (API)** que permiten a cualquier persona utilizar el modelo y sus predicciones, así como **clonar el repositorio** para colaborar o crear sus propias aplicaciones de detección de exoplanetas.  

## Nuestro Equipo 
Está conformado por 3 personas, trabajando en conjunto pero con una división de trabajos clara, definida previa al comienzo del desafío, para una vez este hubiera comenzado, poder aprovechar el tiempo de manera sensta y llevar el proyecto al mayor grado de culminación posible: 
- Mathias Rojas Valverde: Estudiante del Colegio Científico de Costa Rica, sede San Carlos. Responsable del modelado y creación del algoritmo de aprendizaje automático.
+ Ignacio Alberto Carmiol Jimenez: Estudiante en el Colegio Diocesano Padre Eladio Sancho, San Carlos. Responsable de elaborar el backend y mayor parte de la implementación de este algoritmo en una app web. 
* Aaron Eduardo Valerio Barrante: Estudiante del Colegio Científico de Costa Rica, sede San Carlos. Responsable por el diseño de la interfaz de usuario de la app web. 





# Welcome to "Sidereous: Exoplanet Finder"
Sidereus uses machine learning algorithms based on LightGBM, an open-source tool from Microsoft, to analyze tabular data obtained from the K2, TESS, and Kepler missions. Based on characteristics such as orbital period, transit depth, and other stellar properties, the model evaluates the probability that a given exoplanet candidate is indeed one or not. This optimizes exoplanet classification, allowing for a focus on candidates with high accuracy and thus contributing, to a certain extent, to accelerating scientific progress in astronomy and astrophysics.
## About the challenge 
This project is our solution to the NASA Space App Challenge Costa Rica 2025 "A World Away: Hunting for Exoplanets With AI" challenge.
[Official competition link](https://www.spaceappschallenge.org/2025/challenges/a-world-away-hunting-for-exoplanets-with-ai/)

## Our Solution 
...

## Resources used
For the complete application, we used the **Python** programming language, which provides flexibility as an interpreted language and offers a wide range of **open-source libraries** that are easy to use.  

We used **data structures** to store and analyze data more dynamically, avoiding *hardcoding*, which is when parameters are implemented statically and are harder to modify.  

We also used several Python libraries such as **NumPy** and **LightGBM**, as well as **Flask** for the backend of our application, which handles the server logic, opening endpoints to retrieve model information. The backend also provides access to the user interface, making the app easier to use.  

For the **user interface**, we used **HTML**, **CSS**, and **JavaScript**, providing a clean and organized way to interact with the app.  

For the **training of our AI model**, we used **NASA’s exoplanet datasets**, including **Kepler and TESS Objects of Interest (KOI and TOI)**, as well as **K2** data.  

We also made responsible use of **AI tools** like ChatGPT to assist with repetitive tasks such as data structure generation and debugging, since this challenge was a new experience for our entire team. 

## Potencial Impact 
We implemented a **simple and intuitive exoplanet recognition application** based on satellite data, providing an engaging and educational experience for space enthusiasts.  

We also chose to make our project **open source on GitHub**, allowing anyone interested in innovating with a similar application to do so, or even collaborate directly with this project.  

## Innovation 
Our application implements **exoplanet detection in a simple and accessible way** for users. Additionally, it exposes **API endpoints** that allow anyone to use the model and its predictions, as well as **clone the repository** to collaborate or create their own exoplanet detection applications.

## Our Team: 
It is made up of three people working together, but with a clear division of labor, defined prior to the start of the challenge, so that once it has begun, they can use their time wisely and bring the project to the highest possible level of completion:
- **Mathias Rojas Valverde:** Student at the San Carlos Campus of the Scientific Highschool of Costa Rica. Responsible for the modeling and creation of the machine learning algorithm.
+ **Ignacio Alberto Carmiol Jimenez:** Student at the Padre Eladio Sancho Diocesan School in San Carlos. Responsible for developing the backend and most of the implementation of this algorithm in a web app.
* **Aaron Eduardo Valerio Barrante:** Student at the San Carlos Campus of the Scientific Highschool of Costa Rica. Responsible for desing the UI of the web app.
