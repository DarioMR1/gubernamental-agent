import type { Route } from "./+types/dashboard";
import { ChatLayout } from "~/components/chat";
import { useRequireAuth } from '~/lib/auth';
import { Button } from '~/components/ui/button';

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Dashboard - Chat Assistant" },
    { name: "description", content: "Chat with our AI assistant" },
  ];
}

export default function Dashboard() {
  const { user, loading, signOut } = useRequireAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <h2 className="mt-4 text-xl font-semibold">Cargando...</h2>
          <p className="text-gray-600">Verificando autenticación</p>
        </div>
      </div>
    );
  }

  if (!user) {
    // El hook useRequireAuth se encargará de la redirección
    return null;
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Top Navigation */}
      <nav className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-linear-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AI</span>
            </div>
            <span className="font-semibold text-lg text-gray-900">Chat Assistant</span>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">
              <span>Hola, </span>
              <span className="font-medium">{user.given_name || user.name}</span>
            </div>
            <Button
              onClick={signOut}
              variant="outline"
              className="text-gray-600 border-gray-300 hover:bg-gray-50"
            >
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </nav>

      {/* Chat Area */}
      <div className="flex-1 overflow-hidden">
        <ChatLayout />
      </div>
    </div>
  );
}