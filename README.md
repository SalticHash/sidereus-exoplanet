# Bienvenidos a "Sidereous: Exoplanet Finder"
Sidereus emplea algoritmos de machine learning, basados en LightGBM, una herramienta open source de Microsoft, para analizar datos tabulares basados en los obtenidos en las misiones K2, TESS y Kepler. A partir de características como el periodo orbital, profundidad de tránsito u otras propiedades estelares, el modelo evalua la probabilidad de que cierto candidato a exoplaneta sea en efecto uno o no. Esto permite optimizar la clasificación de exoplanetas, permitiendo enfocarse en candidatos con alta presición y contribuyendo así, hasta cierto punto, a acelerar el progreso científico en el área de la astronomía y la astrofísica. 
## Acerca del Desafío 
Este proyecto es nuestra solución al desafío "A World Away: Hunting for Exoplanets With IA" del NASA Space App Challenge Costa Rica 2025. 
[Enlace oficial de la competencia](https://www.spaceappschallenge.org/2025/challenges/a-world-away-hunting-for-exoplanets-with-ai/)

## Nuestra Solución 
...

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
