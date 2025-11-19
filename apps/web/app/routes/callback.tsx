import { useEffect, useState } from 'react';
import type { Route } from "./+types/callback";
import { oracleAuth } from '~/lib/auth';

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Procesando autenticación..." },
  ];
}

export default function Callback() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    async function handleCallback() {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');

        if (error) {
          throw new Error(`Error de autenticación: ${error}`);
        }

        if (!code || !state) {
          throw new Error('Código de autorización no encontrado');
        }

        // Intercambiar código por token
        await oracleAuth.exchangeCodeForToken(code, state);
        
        setStatus('success');
        
        // Verificar si es un signup y limpiar datos temporales
        const signupData = localStorage.getItem('signup_data');
        if (signupData && state.startsWith('signup_')) {
          localStorage.removeItem('signup_data');
          // Redirigir al dashboard como usuario nuevo
          setTimeout(() => {
            window.location.href = '/dashboard?welcome=true';
          }, 1000);
        } else {
          // Login normal, redirigir al dashboard
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 1000);
        }

      } catch (error) {
        console.error('Error en callback:', error);
        setError(error instanceof Error ? error.message : 'Error desconocido');
        setStatus('error');
      }
    }

    handleCallback();
  }, []);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <h2 className="mt-4 text-xl font-semibold">Procesando autenticación...</h2>
          <p className="text-gray-600">Por favor espera mientras te autenticamos</p>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-green-600 text-6xl mb-4">✓</div>
          <h2 className="text-xl font-semibold text-green-600">¡Autenticación exitosa!</h2>
          <p className="text-gray-600">Redirigiendo al dashboard...</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-600 text-6xl mb-4">✗</div>
          <h2 className="text-xl font-semibold text-red-600 mb-2">Error de autenticación</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.href = '/login'}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Intentar de nuevo
          </button>
        </div>
      </div>
    );
  }

  return null;
}