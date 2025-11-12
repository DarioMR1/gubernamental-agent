# RFC - Inscripción Persona Física (Primera Vez)

## Identificación del Trámite

**Código**: `SAT_RFC_INSCRIPCION_PF`  
**Nombre Oficial**: Inscripción en el RFC de Persona Física  
**Jurisdicción**: Federal (SAT)  
**Modalidad**: En línea (preferida) o Presencial  
**Tiempo Estimado**: 15-30 minutos en línea, 1-2 horas presencial  

## ¿Qué Debe Saber el Agente?

### Propósito del Trámite
El RFC (Registro Federal de Contribuyentes) es la clave única que identifica a una persona ante el SAT. Es **obligatorio** para:
- Trabajar de manera formal (recibir salario)
- Emitir facturas o comprobantes fiscales
- Abrir cuentas bancarias
- Realizar actividades económicas que generen ingresos

### Elegibilidad
- **Edad**: Mayor de 18 años (o menor con representante legal)
- **Nacionalidad**: Mexicana o extranjera con documentos migratorios
- **CURP**: Debe tener CURP válida y vigente
- **Primera vez**: No haber tenido RFC anteriormente

## Modalidades de Trámite

### Modalidad En Línea (Recomendada)
- **Requisito único**: CURP válida
- **Ventajas**: Sin cita, sin documentos físicos, inmediato
- **Limitaciones**: Solo para casos estándar (mayor de edad, mexicano, sin complicaciones)

### Modalidad Presencial
- **Cuándo usar**: Menores de edad, extranjeros, casos especiales
- **Requiere**: Cita previa + documentos físicos
- **Tiempo**: 1-2 horas en oficina del SAT

## Flujo Conversacional del Agente

### 1. Detección de Intención
```
Frases que indican este trámite:
- "Quiero sacar mi RFC"
- "Necesito inscribirme al RFC" 
- "Cómo obtengo mi RFC por primera vez"
- "Necesito darme de alta en el SAT"
```

**Respuesta del agente**:
```
"Perfecto, te ayudo con tu inscripción al RFC. Es tu clave única como contribuyente 
ante el SAT - la necesitas para trabajar formalmente, facturar o abrir cuentas bancarias.

Primero veamos si puedes hacerlo en línea, que es mucho más rápido. Para eso necesito 
verificar algunos datos básicos. ¿Eres mayor de 18 años y tienes tu CURP?"
```

### 2. Verificación de Elegibilidad
**Preguntas clave**:
1. "¿Eres mayor de 18 años?"
2. "¿Tienes tu CURP?"
3. "¿Alguna vez has tenido RFC antes?"
4. "¿Eres mexicano o extranjero?"

**Flujos según respuestas**:

**Si es mayor + mexicano + tiene CURP + nunca ha tenido RFC**:
```
"Excelente, puedes hacerlo completamente en línea. Solo necesitamos tu CURP 
y en unos minutos tendrás tu RFC listo. ¿Me compartes tu CURP para validarla?"
```

**Si es menor de edad**:
```
"Al ser menor de 18 años, necesitarás hacer el trámite presencial con un tutor 
o representante legal. Te explico qué documentos van a necesitar..."
```

**Si es extranjero**:
```
"Al ser extranjero, el proceso requiere documentos migratorios adicionales. 
¿Tienes tu documento migratorio vigente (FM3, residente, etc.)?"
```

### 3. Validación de CURP
**Herramienta**: `validate_official_identifier("curp", valor)`

**Si CURP es válida**:
```
"Tu CURP está perfecta. Veo que naciste el [fecha] en [entidad]. 
Ahora necesito algunos datos adicionales para completar tu perfil fiscal."
```

**Si CURP tiene errores**:
```
"Hay un problema con el formato de tu CURP. Debe tener exactamente 18 caracteres 
con letras y números específicos. ¿Puedes revisarla? O si tienes una foto de 
algún documento oficial, puedo ayudarte a extraerla."
```

### 4. Recolección de Datos Adicionales

#### Datos Personales
- **Nombre completo** (debe coincidir con CURP)
- **Correo electrónico** (para notificaciones del SAT)
- **Teléfono** (opcional pero recomendado)

#### Domicilio Fiscal
```
"Ahora necesito tu domicilio fiscal - es donde el SAT te enviará notificaciones 
y donde legalmente tienes tu residencia para efectos fiscales.

¿Prefieres dictármelo o tienes un comprobante de domicilio que puedo leer?"
```

**Datos requeridos**:
- Calle y número
- Colonia
- Código postal
- Municipio/Delegación
- Estado

### 5. Declaración de Actividades Económicas

**Pregunta clave**:
```
"Ahora viene una pregunta importante: ¿planeas realizar alguna actividad que 
te genere ingresos? Por ejemplo: trabajar por tu cuenta, prestar servicios, 
vender productos, rentar algo, etc.

Esto determina qué obligaciones fiscales tendrás."
```

**Opciones principales**:
- **Solo salario**: "Únicamente voy a trabajar como empleado"
- **Actividad empresarial**: "Voy a tener mi propio negocio/prestar servicios"
- **Ambas**: "Tendré salario y también actividades por mi cuenta"
- **Sin actividad**: "Solo necesito el RFC para trámites (banco, etc.)"

### 6. Explicación de Régimen Fiscal

Según la respuesta anterior, explicar qué régimen le corresponde:

**Solo salario**:
```
"Perfecto, en tu caso aplicarías para 'Sueldos y Salarios'. Esto significa que:
- Tu empleador te retendrá impuestos automáticamente
- Probablemente no tendrás que presentar declaraciones anuales
- No necesitas facturar nada"
```

**Actividad empresarial**:
```
"Para actividades por tu cuenta, hay varios regímenes disponibles dependiendo 
de tus ingresos esperados. Los más comunes son:
- Régimen de Incorporación Fiscal (RIF): Si esperas ganar menos de $2 millones anuales
- Régimen General: Para cualquier monto, pero con más obligaciones

¿Tienes una idea aproximada de cuánto planeas facturar al año?"
```

## Validaciones Específicas

### CURP
```python
def validate_curp_for_rfc(curp: str) -> CurpValidationResult:
    """
    Valida CURP específicamente para trámite de RFC
    - Formato: 18 caracteres
    - Patrón: 4 letras + 6 números + 6 letras/números + 2 números
    - Dígito verificador correcto
    - Fecha de nacimiento válida
    - Entidad federativa válida
    """
```

### Coherencia de Datos
- Nombre en CURP vs nombre declarado (similitud ≥90%)
- Fecha de nacimiento coherente con edad declarada
- Entidad de nacimiento en CURP vs domicilio (alertar si muy diferente)

### Domicilio
- Código postal válido (5 dígitos, existe en catálogo del SAT)
- Estado y municipio coherentes con CP
- Si hay comprobante: antigüedad ≤90 días, legible, coincide con CP

## Errores Comunes a Prevenir

### 1. CURP Incorrecta
**Síntomas**: Formato inválido, no coincide con datos
**Solución**: Guiar para obtener CURP oficial de RENAPO

### 2. Datos Inconsistentes
**Síntomas**: Nombre no coincide, fechas contradictorias
**Solución**: Usar datos exactos de documentos oficiales

### 3. Domicilio Incompleto
**Síntomas**: CP faltante, colonia no existe
**Solución**: Validar con catálogo oficial del SAT

### 4. Régimen Fiscal Incorrecto
**Síntomas**: Usuario no entiende implicaciones
**Solución**: Explicar claramente obligaciones de cada régimen

## Checklist Final Pre-Trámite

```
✅ DATOS PERSONALES
  □ CURP válida (18 caracteres, formato correcto)
  □ Nombre completo (coincide con CURP)
  □ Fecha de nacimiento confirmada
  □ Correo electrónico válido

✅ DOMICILIO FISCAL  
  □ Calle y número completos
  □ Colonia existente
  □ Código postal válido (5 dígitos)
  □ Municipio y estado coherentes
  □ Comprobante ≤90 días (si presencial)

✅ ACTIVIDAD ECONÓMICA
  □ Tipo de actividad definida
  □ Régimen fiscal identificado
  □ Obligaciones fiscales explicadas

✅ MODALIDAD DE TRÁMITE
  □ En línea: Solo CURP requerida
  □ Presencial: Documentos físicos preparados
```

## Pasos Sugeridos Para Ejecutar

### Modalidad En Línea
```
"Ya tienes todo listo para hacer tu trámite en línea. Los pasos son:

1. Ve a sat.gob.mx
2. Busca 'Inscripción al RFC'
3. Selecciona 'Persona Física con CURP'
4. Captura tu CURP: [CURP_VALIDADA]
5. Llena el formulario con estos datos:
   - Nombre: [NOMBRE]
   - Domicilio: [DOMICILIO_COMPLETO]
   - Correo: [CORREO]
   - Actividad: [ACTIVIDAD_SELECCIONADA]

El sistema te dará tu RFC inmediatamente y podrás descargar tu cédula."
```

### Modalidad Presencial  
```
"Para el trámite presencial necesitas:

1. Agendar cita en sat.gob.mx o llamar al 55-4738-3676
2. Llevar estos documentos:
   - Identificación oficial vigente (INE/Pasaporte)
   - Comprobante de domicilio ≤90 días
   - CURP impresa

3. Ir a tu cita con 15 minutos de anticipación
4. El trámite toma aproximadamente 30 minutos en ventanilla"
```

## Respuestas a Preguntas Frecuentes

**"¿Cuánto cuesta?"**: Es gratuito, tanto en línea como presencial.

**"¿Cuánto tiempo tarda?"**: En línea es inmediato. Presencial, unos 30 minutos en ventanilla.

**"¿Qué pasa si me equivoco?"**: Puedes hacer correcciones posteriormente, pero es mejor revisar bien antes de enviar.

**"¿Necesito contratar un contador?"**: No, para la inscripción básica no necesitas ayuda profesional.

**"¿Puedo hacer el trámite por alguien más?"**: No, debe hacerlo el interesado personalmente o con representante legal (menores).

## Limitaciones del Agente

El agente debe ser transparente sobre qué NO puede hacer:
- No puede ejecutar el trámite automáticamente en el portal del SAT
- No puede garantizar que no habrá cambios en requisitos
- No puede acceder a sistemas del SAT para verificar disponibilidad
- No puede dar asesoría fiscal específica (régimen optimal, deducciones, etc.)

## Tono y Estilo Para Este Trámite

- **Tranquilizador**: "Es un trámite sencillo cuando tienes todo preparado"
- **Educativo**: Explica el porqué de cada requisito
- **Práctico**: Se enfoca en los pasos concretos
- **Preventivo**: Anticipa errores comunes
- **Empático**: Reconoce que puede ser intimidante la primera vez

**Ejemplo de cierre**:
```
"Ya tienes todo listo para tu RFC. Recuerda que es un paso importante - 
con esto podrás trabajar formalmente y hacer muchos trámites que antes 
no podías. El proceso en línea es muy directo, y si tienes algún problema, 
el SAT tiene chat y teléfono de ayuda. ¡Mucho éxito con tu trámite!"
```