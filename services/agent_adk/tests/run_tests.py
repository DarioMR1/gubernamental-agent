#!/usr/bin/env python3
# Copyright 2024 SEMOVI Multiagent System Tests

"""Test runner script for SEMOVI agent tests."""

import sys
import os
import subprocess
import argparse

def run_unit_tests():
    """Run unit tests with pytest."""
    print("🧪 Ejecutando tests unitarios...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "test_semovi_agent.py", 
        "-v", 
        "--tb=short",
        "--color=yes"
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode == 0

def run_evaluation_tests():
    """Run evaluation tests with ADK."""
    print("📊 Ejecutando tests de evaluación...")
    
    # Change to the parent directory where the agent module is
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    
    cmd = [
        "adk", "eval", 
        "semovi_multiagent_system",
        "tests/semovi_evaluation.test.json", 
        "--config_file_path=tests/test_config.json",
        "--print_detailed_results"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=parent_dir, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en evaluación: {e}")
        return False
    except FileNotFoundError:
        print("❌ ADK CLI no encontrado. Asegúrate de que esté instalado.")
        return False

def run_quick_smoke_test():
    """Run a quick smoke test to verify basic functionality."""
    print("💨 Ejecutando smoke test rápido...")
    
    try:
        # Import the agent to check for import errors
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from semovi_multiagent_system.agent import root_agent
        print("✅ Importación del agente exitosa")
        
        # Check that the agent has required components
        assert root_agent.name == "semovi_coordinator"
        assert len(root_agent.sub_agents) == 5
        assert len(root_agent.tools) >= 6
        print("✅ Estructura del agente verificada")
        
        # Check that context variables are initialized
        from semovi_multiagent_system.core.callbacks import initialize_semovi_session
        print("✅ Callbacks de inicialización disponibles")
        
        return True
        
    except Exception as e:
        print(f"❌ Smoke test falló: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Ejecutar tests para SEMOVI agent")
    parser.add_argument("--smoke", action="store_true", help="Ejecutar solo smoke test")
    parser.add_argument("--unit", action="store_true", help="Ejecutar solo tests unitarios")
    parser.add_argument("--eval", action="store_true", help="Ejecutar solo tests de evaluación")
    parser.add_argument("--all", action="store_true", help="Ejecutar todos los tests")
    
    args = parser.parse_args()
    
    if not any([args.smoke, args.unit, args.eval, args.all]):
        args.all = True  # Default to all tests
    
    results = []
    
    if args.smoke or args.all:
        results.append(("Smoke Test", run_quick_smoke_test()))
    
    if args.unit or args.all:
        results.append(("Tests Unitarios", run_unit_tests()))
    
    if args.eval or args.all:
        results.append(("Tests de Evaluación", run_evaluation_tests()))
    
    # Print results summary
    print("\n" + "="*50)
    print("📋 RESUMEN DE RESULTADOS")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ¡Todos los tests pasaron!")
        return 0
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa los errores arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())