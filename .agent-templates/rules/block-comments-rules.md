# 🔲 REGLAS DE BLOQUES DE COMENTARIOS

## Obligatoriedad

Toda función > 5 líneas debe tener bloques de comentario inicio/fin.

## Formato Estándar

```python
### INICIO nombre_funcion
"""
Propósito: [qué hace la función]
Entradas: [parámetros y tipos]
Salidas: [retorno y tipo]
"""
### FIN nombre_funcion
```

## Alternativa Simple

Si no hay docstring:

```python
### INICIO nombre_funcion
# Lógica de la función aquí
### FIN nombre_funcion
```

## Ejemplo

```python
### INICIO calcular_promedio
def calcular_promedio(numeros: list[float]) -> float:
    """
    Calcula el promedio de una lista de números.
    
    Propósito: Calcular media aritmética
    Entradas: lista de floats
    Salidas: float con el promedio
    """
    if not numeros:
        return 0.0
    return sum(numeros) / len(numeros)
### FIN calcular_promedio
```

## Excepciones

- Getters/Setters simples (1-2 líneas)
- Lambdas
- Funciones de callback trivial
