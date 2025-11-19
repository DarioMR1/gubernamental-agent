import { useEffect } from 'react';
import type { Route } from "./+types/home";
import { useAuth } from '~/lib/auth';
import { Button } from '~/components/ui/button';

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Chat Assistant - Tu Asistente AI Inteligente" },
    { name: "description", content: "Conecta con nuestro asistente AI avanzado para obtener ayuda instantánea con cualquier consulta" },
  ];
}

export default function Home() {
  const { user, loading } = useAuth();

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

  return (
    <div className="min-h-screen bg-linear-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-linear-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <span className="font-bold text-xl text-gray-900">Chat Assistant</span>
            </div>
            <div className="flex space-x-4">
              <Button 
                onClick={() => window.location.href = '/login'}
                variant="outline"
                className="border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                Iniciar Sesión
              </Button>
              <Button 
                onClick={() => window.location.href = '/signup'}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Registrarse
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-4xl sm:text-6xl font-bold text-gray-900 mb-6">
              Tu Asistente AI{' '}
              <span className="bg-linear-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Inteligente
              </span>
            </h1>
            
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              Conecta con nuestro asistente AI avanzado para obtener ayuda instantánea, 
              resolver consultas complejas y potenciar tu productividad.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Button 
                onClick={() => window.location.href = '/signup'}
                className="bg-linear-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 px-8 text-lg rounded-lg shadow-lg hover:shadow-xl transition-all"
              >
                Comenzar Gratis
              </Button>
              <Button 
                onClick={() => window.location.href = '/login'}
                variant="outline"
                className="border-gray-300 text-gray-700 hover:bg-gray-50 font-semibold py-3 px-8 text-lg"
              >
                Ya tengo cuenta
              </Button>
            </div>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">AI Avanzado</h3>
              <p className="text-gray-600">
                Powered por tecnología de última generación para respuestas precisas y contextualmente relevantes.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Respuestas Instantáneas</h3>
              <p className="text-gray-600">
                Obtén respuestas inmediatas a tus preguntas, sin esperas ni demoras.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔒</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Seguro y Privado</h3>
              <p className="text-gray-600">
                Tus conversaciones están protegidas con autenticación Oracle Identity de nivel empresarial.
              </p>
            </div>
          </div>

          {/* Call to Action */}
          <div className="mt-16 bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              ¿Listo para comenzar?
            </h2>
            <p className="text-gray-600 mb-6">
              Únete a miles de usuarios que ya están potenciando su productividad con nuestro asistente AI.
            </p>
            <Button 
              onClick={() => window.location.href = '/signup'}
              className="bg-linear-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 px-8 text-lg rounded-lg shadow-lg hover:shadow-xl transition-all"
            >
              Crear cuenta gratuita
            </Button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500 text-sm">
            <p>&copy; 2024 Chat Assistant. Powered by Oracle Cloud Identity.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
