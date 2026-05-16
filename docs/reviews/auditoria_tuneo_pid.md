# Auditoria del tuneo PID clasico

## Estado actual

`tools/tune_classic_pid.py` ajusta un PID por familia (`hold`, `circle`, `lissajous`, `waypoint`) usando una busqueda en rejilla de 81 candidatos:

- multiplica `Kp_pos`, `Kd_pos`, `Kp_att` y `Kd_att` por `[0.8, 1.0, 1.2]`;
- evalua solo la primera geometria de la familia;
- evalua solo el perfil `P0_nominal`;
- descarta candidatos con filtros duros de terminacion, saturacion, degradacion y error maximo;
- selecciona por `pid_candidate_score`;
- aplica una regla conservadora: entre candidatos a menos del 5% del mejor score, elige el de menor suma de multiplicadores.

El score combina RMSE de posicion, error maximo, actitud RMS, esfuerzo normalizado, saturacion y degradacion. El empuje se normaliza por `m*g` y los momentos por `0.1 Nm`, por lo que el score es util como criterio de seleccion interno pero no como metrica fisica principal.

## Limitaciones

- Una sola geometria nominal no representa todo el dominio de cada familia.
- No valida cruzadamente contra viento, ruido, drag alto ni actuadores mas lentos.
- La rejilla de 81 candidatos es barata, pero muy gruesa; puede perder combinaciones utiles.
- El resultado puede sobreajustarse a la primera geometria de cada familia.
- El tuneo no produce un banco de expertos, solo un PID congelado por familia.
- Para aprendizaje neuronal, un unico PID por familia aporta poca variedad de ganancias y no permite aprender bien una politica tipo "PID con constantes variables".

## Propuesta implementada para banco inicial

Se introduce `tools/generate_pid_bank.py` como banco reproducible ligero:

- parte de los PIDs actuales del dataset;
- genera variantes `conservative`, `base` y `aggressive` por familia;
- evalua cada variante sobre un subconjunto fijo de geometrias y perfiles (`P0_nominal`, `P2_wind_east`, `P5_combined`);
- escribe `pid_bank_manifest.csv` con `pid_id`, familia, variante, casos validos y score medio.

Se introduce tambien `tools/generate_position_gain_dataset_from_bank.py`:

- expande un dataset clasico usando los PIDs del banco;
- cada episodio generado conserva `scenario_path`, `result_dir`, `split`, `family`, `geometry_id` y `perturbation_id`;
- añade `source_scenario_id`, `pid_id` y `pid_variant`;
- genera YAMLs ejecutables por `tools/run_classic_dataset.py`;
- permite entrenar la red de ganancias leyendo `Kp_pos` y `Kd_pos` del YAML experto.

## Criterio de uso

El tuneo actual sigue siendo valido para obtener un baseline clasico reproducible por familia. Para la red de lazo externo, el banco de PIDs es preferible porque aporta etiquetas de ganancias variadas. La comparacion final no debe hacerse por score de tuneo ni por MSE supervisado, sino por `position_rmse_m`, terminacion, saturacion y degradacion en bucle cerrado.
