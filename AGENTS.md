# Agent Instructions

Este proyecto debe trabajarse con el estilo del second brain: claridad humana primero, reproducibilidad despues, modularizacion solo cuando aporte valor.

## Reglas locales

- No modificar, sobrescribir ni mover los datasets originales sin peticion explicita.
- Tratar los CSV de la raiz como fuente inicial de verdad.
- Guardar cualquier salida derivada en `data/processed/`, `reports/` o una carpeta nueva justificada.
- Mantener un flujo humano: cargar datos, explorar, validar calidad, limpiar, crear variables, modelar y medir.
- Usar nombres descriptivos y pasos intermedios visibles.
- No crear arquitectura extra antes de entender el problema.
- Actualizar `PROJECT_LOG.md` cuando se cambie el proyecto.

## Estilo tecnico

- Preferir rutas relativas desde la raiz del proyecto.
- Usar `RANDOM_STATE = 42` cuando haya aleatoriedad.
- Separar hechos observados, decisiones tomadas y dudas abiertas.
- Revisar leakage antes de entrenar modelos.
- Crear un baseline simple antes de modelos complejos.