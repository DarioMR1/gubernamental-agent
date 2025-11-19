import { useEffect, useState } from 'react';
import type { Route } from "./+types/signup";
import { useAuth } from '~/lib/auth';
import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Crear Cuenta" },
    { name: "description", content: "Crea tu cuenta para comenzar" },
  ];
}

export default function Signup() {
  const { user, loading, signUpWithPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Si ya está autenticado, redirigir al dashboard
  useEffect(() => {
    if (!loading && user) {
      window.location.href = '/dashboard';
    }
  }, [loading, user]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !firstName || !lastName) {
      setError('Por favor completa todos los campos');
      return;
    }

    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await signUpWithPassword(email, password, firstName, lastName);
      // Mostrar mensaje de éxito y redirigir al login
      alert('¡Cuenta creada exitosamente! Te hemos enviado un email de confirmación. Por favor verifica tu email antes de iniciar sesión.');
      window.location.href = '/login';
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Error al crear la cuenta');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8">
        <div className="bg-white p-8 rounded-xl shadow-lg">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Crear Cuenta
            </h2>
            <p className="text-gray-600 mb-8">
              Únete y comienza a usar nuestro chat assistant
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700">
                  Nombre
                </label>
                <Input
                  id="firstName"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Juan"
                  required
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700">
                  Apellido
                </label>
                <Input
                  id="lastName"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Pérez"
                  required
                  className="w-full"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Correo electrónico
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@correo.com"
                required
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Contraseña
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={8}
                className="w-full"
              />
              <p className="text-xs text-gray-500">Mínimo 8 caracteres</p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className="shrink-0 text-blue-600 text-xl">ℹ️</div>
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">Verificación de email</p>
                  <p>Te enviaremos un email de confirmación para activar tu cuenta. Revisa tu bandeja de entrada.</p>
                </div>
              </div>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Creando cuenta...' : 'Crear Cuenta'}
            </Button>

            <div className="text-center text-sm text-gray-600">
              <span>¿Ya tienes cuenta? </span>
              <a 
                href="/login" 
                className="text-green-600 hover:text-green-700 font-medium"
              >
                Inicia sesión aquí
              </a>
            </div>

            <div className="text-center text-sm">
              <a 
                href="/" 
                className="text-gray-500 hover:text-gray-700"
              >
                ← Volver al inicio
              </a>
            </div>
          </form>
        </div>

        <div className="text-center text-xs text-gray-500">
          <p>Al registrarte, aceptas nuestros términos de servicio y política de privacidad</p>
        </div>
      </div>
    </div>
  );
}