# EJERCICIO SIMPLE DE REFACTORIZACIÓN

# --- ANTES ---
print("Hola, Ana. ¡Te damos la bienvenida al curso!")
print("Hola, Luis. ¡Te damos la bienvenida al curso!")
print("Hola, Marta. ¡Te damos la bienvenida al curso!")

# --- DESPUÉS ---

estudiantes = ["Ana", "Luis", "Marta"]

def saludar(nombre):
    return f"Hola, {nombre}. ¡Te damos la bienvenida al curso!"
for nombre in estudiantes:
    print(saludar(nombre))

