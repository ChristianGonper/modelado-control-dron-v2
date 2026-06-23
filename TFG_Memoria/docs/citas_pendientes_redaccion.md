# Citas pendientes de redacción

Las entradas se crean únicamente para afirmaciones ya señaladas mediante
comentarios `CITA PENDIENTE` en los capítulos redactados. No constituyen
referencias bibliográficas ni autorizan a crear claves `\cite{}` sin verificar
la fuente original.

| ID | Archivo y subsección | Afirmación que debe respaldarse | Tipo de fuente necesaria | Términos de búsqueda | Estado |
|---|---|---|---|---|---|
| CIT-001 | `01_introduccion.tex`, 1.1 | Acoplamiento, subactuación y coordinación traslación--actitud en cuadricópteros. | Libro o artículo académico de dinámica/control. | quadrotor underactuated coupled position attitude control | Pendiente |
| CIT-002 | `03_modelo_fisico.tex`, 3.2 | Representatividad de masa, inercia, geometría y coeficientes del vehículo académico. | Ficha técnica verificable o publicación con plataforma comparable. | 1 kg quadrotor inertia thrust coefficient arm length | Pendiente |
| CIT-003 | `03_modelo_fisico.tex`, 3.3 | Propiedades y condiciones de aplicación de RK4 de paso fijo. | Libro de análisis numérico o referencia original. | fixed step RK4 ordinary differential equations stability error | Pendiente |
| CIT-004 | `03_modelo_fisico.tex`, 3.4 | Ley cuadrática de empuje/par y asignación de rotores. | Libro o artículo de modelado de cuadricópteros. | quadrotor thrust torque omega squared allocation matrix | Pendiente |
| CIT-005 | `03_modelo_fisico.tex`, 3.4 | Modelo de primer orden y retardo de actuadores. | Artículo de identificación/actuadores o documentación de plataforma. | quadrotor motor first order lag time constant delay | Pendiente |
| CIT-006 | `03_modelo_fisico.tex`, 3.5 | Alcance de drag lineal, viento constante y ruido gaussiano. | Publicación de modelado o simulación. | quadrotor linear drag constant wind Gaussian sensor noise model | Pendiente |
| CIT-007 | `03_modelo_fisico.tex`, 3.5 | Criterio para límites de actitud y seguridad. | Norma, publicación de seguridad o criterio experimental defendible. | quadrotor attitude safety limit rollover simulation termination | Pendiente |
| CIT-008 | `03_modelo_fisico.tex`, 3.7 | Retención de orden cero y simulación multirrate. | Libro de control digital o simulación. | zero order hold multirate digital control simulation | Pendiente |
| CIT-009 | `04_control_clasico.tex`, Metodología 3.2 | Control PD en cascada de posición y actitud, conversión geométrica fuerza--actitud y error de cuaternión. | Libro o artículo académico de control de cuadricópteros. | cascaded PD position attitude quadrotor geometric control quaternion attitude error | Pendiente |
| CIT-010 | `04_control_clasico.tex`, Metodología 3.2 | Alcance de ajuste manual, Ziegler--Nichols, diseño basado en modelo y búsqueda numérica para sintonizar controladores bajo restricciones. | Fuentes originales y revisión académica. | PID tuning Ziegler Nichols quadrotor numerical optimization constrained controller tuning | Pendiente |
| CIT-011 | `05_control_neuronal.tex`, 5.1 | Ventajas y límites del control híbrido aprendido--clásico. | Artículo académico de learning-based control híbrido. | hybrid learning classical control quadrotor imitation | Pendiente |
| CIT-012 | `05_control_neuronal.tex`, 5.3 | Selección de variables y ventanas temporales en control recurrente. | Artículo académico o libro de aprendizaje secuencial. | recurrent neural control feature selection sequence window actuator delay | Pendiente |
| CIT-013 | `05_control_neuronal.tex`, 5.4 | Fundamentos de ReLU, GRU y LSTM. | Trabajos originales o textos académicos fundamentales. | ReLU original paper GRU original paper LSTM original paper | Pendiente |
| CIT-014 | `05_control_neuronal.tex`, 5.5 | Normalización train-only, MSE, Adam y parada temprana. | Fuentes originales o texto académico. | Adam optimizer MSE regression early stopping data leakage normalization | Pendiente |
| CIT-015 | `05_control_neuronal.tex`, 5.6 | Criterio físico para límites de fuerza e inclinación. | Artículo de control o especificación de envolvente de vuelo. | quadrotor desired force tilt limit thrust constraint | Pendiente |
| CIT-016 | `06_metodologia.tex`, 6.3 | Cobertura, conteos, ratios y perfiles del dataset. | Metodología de diseño experimental o análisis propio versionado. | simulation experiment design trajectory dataset split coverage | Pendiente |
| CIT-017 | `06_metodologia.tex`, 6.8 | Interpretación de RMSE, MAE, máximo y saturación en seguimiento. | Libro o publicación de evaluación de control. | trajectory tracking RMSE MAE maximum error actuator saturation metric | Pendiente |
| CIT-018 | `01_introduccion.tex`, 1.1 | Un ajuste fijo puede exigir compromisos entre condiciones de operación diferentes; la especialización o programación de ganancias reduce ese compromiso a costa de ajustar, validar y seleccionar varios controladores. | Libro o artículo académico de control con parámetros variables o programación de ganancias. | gain scheduling fixed controller trade-off varying operating conditions controller bank | Pendiente |
| CIT-019 | `03_modelo_fisico.tex`, 3.1 | Python como entorno abierto, PyTorch para entrenamiento neuronal, `uv` para gestión reproducible de dependencias y GitHub como repositorio abierto. | Documentación oficial de herramientas y, si procede, página de licencia. | Python license PyTorch documentation uv documentation GitHub repository open source | Pendiente |
