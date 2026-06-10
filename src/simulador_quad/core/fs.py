import os
import shutil
import tempfile
import warnings
from pathlib import Path

def atomic_write_directory(target_path: str, write_func, overwrite: bool = False):
    """
    Escribe contenido de forma segura utilizando un directorio temporal hermano.
    Si overwrite es False y el destino existe, lanza FileExistsError.

    Parámetros:
        target_path: Ruta del directorio destino final.
        write_func: Función callable que recibe la ruta del directorio temporal
                    donde debe escribir los archivos.
        overwrite: Si es True, permite sobreescribir un destino existente eliminando
                   los residuos que no pertenezcan al nuevo resultado.
    """
    target = Path(target_path).resolve()
    if target.exists() and not overwrite:
        raise FileExistsError(f"El directorio destino '{target}' ya existe y overwrite=False.")

    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)

    # Crear directorio temporal en el mismo padre para asegurar el renombrado atómico (mismo volumen)
    temp_dir = Path(tempfile.mkdtemp(dir=parent, prefix=".tmp_atomic_"))

    try:
        # Ejecutar la función de escritura sobre el directorio temporal
        write_func(temp_dir)

        # Validar que el directorio temporal no quedó vacío
        if not any(temp_dir.iterdir()):
            raise RuntimeError(f"La ejecucion de la escritura finalizo sin crear ningun archivo en {temp_dir}")

        # Reemplazo seguro
        if target.exists():
            # En Windows no se puede hacer os.replace de directorios directamente si tienen archivos.
            # En su lugar, renombramos el destino actual a un nombre temporal,
            # renombramos el nuevo y finalmente borramos el antiguo.
            old_temp = Path(tempfile.mkdtemp(dir=parent, prefix=".tmp_old_"))
            old_temp.rmdir() # Borramos para poder renombrar target a esta ruta

            target.rename(old_temp)
            try:
                temp_dir.rename(target)
            except Exception as e:
                if old_temp.exists() and not target.exists():
                    old_temp.rename(target)
                raise e
            else:
                try:
                    shutil.rmtree(old_temp)
                except OSError as cleanup_error:
                    warnings.warn(
                        f"Atomic write installed '{target}' but failed to remove backup "
                        f"'{old_temp}': {cleanup_error}",
                        RuntimeWarning,
                        stacklevel=2,
                    )
        else:
            temp_dir.rename(target)

    finally:
        # Asegurar la limpieza en caso de fallos antes del rename
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
