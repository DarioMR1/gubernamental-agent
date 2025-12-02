# Usuario de Prueba para SEMOVI Agent

Para probar la funcionalidad de autenticación del agente SEMOVI, necesitas crear un usuario en Supabase.

## Paso 1: Crear Usuario en Supabase

Puedes crear un usuario de prueba directamente en el Dashboard de Supabase:

### Authentication > Users > Add user

```json
{
  "email": "juan.perez@email.com",
  "password": "test123456",
  "user_metadata": {
    "first_name": "Juan",
    "last_name": "Pérez"
  }
}
```

## Paso 2: Verificar Profile Creado

El trigger automático debería crear un perfil en la tabla `profiles`:

```sql
SELECT * FROM profiles WHERE id = (SELECT id FROM auth.users WHERE email = 'juan.perez@email.com');
```

## Paso 3: Probar Autenticación con el Agent

Una vez que el usuario exista, puedes probar la autenticación con el agent:

### Mensaje de Prueba:
```
"Hola, mi email es juan.perez@email.com y mi contraseña es test123456"
```

**Nota**: El agente ahora usa los parámetros `user_email` y `user_password` internamente.

### Respuesta Esperada:
```
¡Bienvenido/a Juan Pérez! 
🚗 Servicios disponibles:
- Licencia Tipo A (autos y motos hasta 400cc)
...
```

## Paso 4: Datos Opcionales para Testing Completo

Si quieres probar el flujo completo, puedes actualizar el perfil con más información:

```sql
UPDATE profiles 
SET 
  phone = '+52-555-123-4567',
  first_name = 'Juan Carlos',
  last_name = 'Pérez González'
WHERE id = (SELECT id FROM auth.users WHERE email = 'juan.perez@email.com');
```

## Comandos de Prueba para el Agent

1. **Saludar sin autenticación:**
   - "Hola"
   - Debería solicitar credenciales

2. **Autenticarse:**
   - "Mi email es juan.perez@email.com y mi contraseña es test123456"
   - Debería autenticar y saludar con nombre

3. **Verificar estado:**
   - "¿Estoy autenticado?"
   - Debería confirmar estatus

4. **Logout:**
   - "Quiero cerrar sesión"
   - Debería limpiar autenticación

5. **Continuar con flujo SEMOVI:**
   - Una vez autenticado, enviar foto de INE o solicitar información sobre licencias