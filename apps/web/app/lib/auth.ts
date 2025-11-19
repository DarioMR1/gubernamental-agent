import { useEffect, useState } from 'react';

interface User {
  sub: string;
  name: string;
  email: string;
  given_name?: string;
  family_name?: string;
  picture?: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

class OracleAuth {
  private clientId: string;
  private domain: string;
  private redirectUri: string;

  constructor() {
    this.clientId = import.meta.env.VITE_ORACLE_CLIENT_ID;
    this.domain = import.meta.env.VITE_ORACLE_DOMAIN;
    this.redirectUri = import.meta.env.VITE_ORACLE_REDIRECT_URI;
  }

  // Generar URL de autorización
  getAuthUrl(isSignup = false): string {
    const state = Math.random().toString(36).substring(7);
    localStorage.setItem('oauth_state', state);
    
    const params = new URLSearchParams({
      client_id: this.clientId,
      redirect_uri: this.redirectUri,
      scope: 'openid profile email',
      response_type: 'code',
      state,
      ...(isSignup && { prompt: 'select_account' })
    });

    return `${this.domain}/oauth2/v1/authorize?${params.toString()}`;
  }

  // Login directo con email y contraseña
  async signInWithPassword(email: string, password: string): Promise<any> {
    const response = await fetch(`${this.domain}/oauth2/v1/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${btoa(this.clientId + ':' + import.meta.env.VITE_ORACLE_CLIENT_SECRET)}`,
      },
      body: new URLSearchParams({
        grant_type: 'password',
        username: email,
        password: password,
        scope: 'openid profile email',
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error_description || 'Credenciales inválidas');
    }

    const tokenData = await response.json();
    localStorage.setItem('oracle_token', tokenData.access_token);
    localStorage.setItem('oracle_refresh_token', tokenData.refresh_token);
    
    return tokenData;
  }

  // Registro usando API pública de self-registration
  async signUpWithPassword(email: string, password: string, firstName: string, lastName: string): Promise<any> {
    // Usamos la API pública de self-registration
    const response = await fetch(`${this.domain}/signup/v1/accounts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userName: email,
        password: password,
        givenName: firstName,
        familyName: lastName,
        email: email
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || errorData.detail || 'Error al crear la cuenta');
    }

    return await response.json();
  }

  // Redirigir a login OAuth (como fallback)
  signIn(): void {
    window.location.href = this.getAuthUrl(false);
  }

  // Redirigir a signup OAuth (como fallback)
  signUp(): void {
    window.location.href = this.getAuthUrl(true);
  }

  // Intercambiar código por token
  async exchangeCodeForToken(code: string, state: string): Promise<any> {
    const storedState = localStorage.getItem('oauth_state');
    if (state !== storedState) {
      throw new Error('Estado OAuth inválido');
    }

    const response = await fetch(`${this.domain}/oauth2/v1/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${btoa(this.clientId + ':' + import.meta.env.VITE_ORACLE_CLIENT_SECRET)}`,
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: this.redirectUri,
      }),
    });

    if (!response.ok) {
      throw new Error('Error al obtener token');
    }

    const tokenData = await response.json();
    localStorage.setItem('oracle_token', tokenData.access_token);
    localStorage.setItem('oracle_refresh_token', tokenData.refresh_token);
    localStorage.removeItem('oauth_state');
    
    return tokenData;
  }

  // Obtener información del usuario
  async getUser(accessToken?: string): Promise<User | null> {
    const token = accessToken || localStorage.getItem('oracle_token');
    if (!token) return null;

    try {
      const response = await fetch(`${this.domain}/oauth2/v1/userinfo`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          this.signOut();
          return null;
        }
        throw new Error('Error al obtener usuario');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching user:', error);
      return null;
    }
  }

  // Logout
  signOut(): void {
    localStorage.removeItem('oracle_token');
    localStorage.removeItem('oracle_refresh_token');
    localStorage.removeItem('oauth_state');
    window.location.href = `${this.domain}/oauth2/v1/logout?post_logout_redirect_uri=${window.location.origin}`;
  }

  // Verificar si hay token válido
  hasValidToken(): boolean {
    return !!localStorage.getItem('oracle_token');
  }
}

export const oracleAuth = new OracleAuth();

// Hook para usar autenticación en componentes
export function useAuth(): AuthState & {
  signIn: () => void;
  signUp: () => void;
  signOut: () => void;
  signInWithPassword: (email: string, password: string) => Promise<any>;
  signUpWithPassword: (email: string, password: string, firstName: string, lastName: string) => Promise<any>;
} {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    async function loadUser() {
      if (!oracleAuth.hasValidToken()) {
        setState({ user: null, loading: false, error: null });
        return;
      }

      try {
        const user = await oracleAuth.getUser();
        setState({ user, loading: false, error: null });
      } catch (error) {
        setState({ 
          user: null, 
          loading: false, 
          error: error instanceof Error ? error.message : 'Error de autenticación' 
        });
      }
    }

    loadUser();
  }, []);

  return {
    ...state,
    signIn: oracleAuth.signIn.bind(oracleAuth),
    signUp: oracleAuth.signUp.bind(oracleAuth),
    signOut: oracleAuth.signOut.bind(oracleAuth),
    signInWithPassword: oracleAuth.signInWithPassword.bind(oracleAuth),
    signUpWithPassword: oracleAuth.signUpWithPassword.bind(oracleAuth),
  };
}

// Hook para proteger rutas
export function useRequireAuth() {
  const auth = useAuth();
  
  useEffect(() => {
    if (!auth.loading && !auth.user) {
      window.location.href = '/login';
    }
  }, [auth.loading, auth.user]);

  return auth;
}