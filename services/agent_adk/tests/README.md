# SEMOVI Agent Testing Suite

Esta suite de tests te permite verificar automáticamente el funcionamiento del sistema SEMOVI multiagente y detectar errores sin testing manual.

## 🚀 Ejecución Rápida

```bash
# Ejecutar todos los tests
python tests/run_tests.py --all

# Ejecutar solo smoke test (verificación básica)
python tests/run_tests.py --smoke

# Ejecutar solo tests unitarios 
python tests/run_tests.py --unit

# Ejecutar solo tests de evaluación
python tests/run_tests.py --eval
```

## 📁 Estructura de Tests

### 1. **test_semovi_agent.py** - Tests Unitarios
- ✅ **TestSemoviAuthentication**: Flujos de autenticación
- ✅ **TestSemoviContextVariables**: Variables de contexto (license_type, appointment_date, etc.)
- ✅ **TestSemoviAgentTransitions**: Transiciones entre agentes
- ✅ **TestSemoviFunctionCalls**: Signatures de funciones y parsing
- ✅ **TestSemoviSessionState**: Consistencia del estado de sesión
- ✅ **TestSemoviIntegration**: Flujos completos integrados

### 2. **semovi_evaluation.test.json** - Dataset de Evaluación
- Casos de prueba para flujos completos
- Conversaciones multi-turn
- Validación de respuestas esperadas
- Manejo de errores

### 3. **conftest.py** - Configuración y Mocks
- Mocks para Supabase (evita dependencias externas)
- Fixtures para sesiones pre-configuradas
- Configuración de entorno de testing

## 🧪 Tipos de Tests

### Smoke Tests
Verificación básica que el agente puede importarse y tiene la estructura correcta:
```bash
python tests/run_tests.py --smoke
```

### Tests Unitarios
Tests detallados de componentes específicos:
```bash
pytest tests/test_semovi_agent.py -v
```

### Tests de Evaluación ADK
Evaluación completa usando el framework ADK:
```bash
adk eval semovi_multiagent_system tests/semovi_evaluation.test.json --config_file_path=tests/test_config.json
```

## 🔍 Qué Detectan los Tests

### Errores de Context Variables
- `'Context variable not found: license_type'`
- `'Context variable not found: appointment_date'`
- Variables no inicializadas correctamente

### Errores de Function Parsing 
- `Failed to parse the parameter selected_date`
- Falta de anotaciones de tipo
- Signatures incorrectas

### Errores de Estado de Sesión
- Estado no persistente entre mensajes
- Campos requeridos faltantes
- Transiciones de proceso incorrectas

### Errores de Autenticación
- Flujos de autenticación rotos
- Manejo incorrecto de credenciales
- Estado de autenticación inconsistente

## 📊 Interpretación de Resultados

### ✅ Test Exitoso
```
✅ PASS Tests Unitarios
✅ PASS Tests de Evaluación
✅ PASS Smoke Test
```

### ❌ Test Fallido
```
❌ FAIL Tests Unitarios
FAILED test_semovi_agent.py::TestSemoviContextVariables::test_license_type_variable_set_after_determination
```

### 📝 Detalles de Fallo
Los tests proporcionan información detallada sobre:
- Qué variable de contexto falta
- Qué función no se ejecutó correctamente
- Qué transición de agente falló
- Estado esperado vs estado actual

## 🛠️ Configuración

### Variables de Entorno
Crea un archivo `.env` en el directorio `tests/`:
```
GOOGLE_API_KEY=tu_api_key
GOOGLE_GENAI_USE_VERTEXAI=FALSE
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_key
```

### Dependencias
```bash
pip install pytest python-dotenv
# ADK ya debe estar instalado
```

## 🎯 Casos de Uso

### Desarrollo Continuo
```bash
# Ejecutar smoke test rápido antes de commit
python tests/run_tests.py --smoke

# Testing completo antes de deploy
python tests/run_tests.py --all
```

### Debugging
```bash
# Test específico con detalles
pytest tests/test_semovi_agent.py::TestSemoviContextVariables -v -s

# Evaluación con resultados detallados
adk eval semovi_multiagent_system tests/semovi_evaluation.test.json --print_detailed_results
```

### CI/CD Integration
```bash
# En pipeline de CI
python tests/run_tests.py --all
if [ $? -eq 0 ]; then
    echo "✅ Todos los tests pasaron - proceder con deploy"
else
    echo "❌ Tests fallaron - bloquear deploy"
    exit 1
fi
```

## 📈 Extensión de Tests

### Agregar Nuevos Tests Unitarios
```python
class TestNuevaFuncionalidad:
    def test_nueva_feature(self):
        runner = TestRunner(root_agent)
        # Tu test aquí
```

### Agregar Casos de Evaluación
Edita `semovi_evaluation.test.json`:
```json
{
  "eval_id": "nuevo_flujo",
  "conversation": [
    {
      "user_content": {"parts": [{"text": "nuevo caso"}]},
      "expected_final_response_contains": ["respuesta esperada"]
    }
  ]
}
```

## 🆘 Troubleshooting

### Error: "Module not found"
```bash
# Verificar paths en conftest.py
sys.path.append('/ruta/correcta/al/agente')
```

### Error: "ADK command not found"  
```bash
# Instalar ADK CLI
pip install google-adk
```

### Tests muy lentos
```bash
# Usar menos runs en evaluación
# Editar test_config.json: "num_runs": 1
```

Con esta suite de tests puedes detectar automáticamente todos los errores que encontraste manualmente, acelerando significativamente el desarrollo y asegurando la calidad del sistema SEMOVI.