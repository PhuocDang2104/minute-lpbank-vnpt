import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../../context/AuthContext';
import { GOOGLE_CLIENT_ID } from '../../config/env';
import { useLocaleText } from '../../i18n/useLocaleText';
import { loginWithGoogle } from '../../lib/api/auth';
import { ApiError } from '../../lib/apiClient';

interface GoogleCredentialResponse {
  credential?: string;
}

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: {
          initialize: (config: {
            client_id: string;
            callback: (response: GoogleCredentialResponse) => void;
            cancel_on_tap_outside?: boolean;
          }) => void;
          renderButton: (
            parent: HTMLElement,
            options: Record<string, string | number | boolean>,
          ) => void;
          prompt: () => void;
        };
      };
    };
  }
}

const getErrorMessage = (error: unknown, fallback: string): string => {
  if (error instanceof ApiError) {
    const payload = error.data;
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const detail = (payload as { detail?: unknown }).detail;
      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
    }
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
};

const Login = () => {
  const { login, refreshUser, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { lt, language } = useLocaleText();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [googleScriptLoaded, setGoogleScriptLoaded] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const googleButtonRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/app/meetings', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleGoogleCredential = useCallback(async (response: GoogleCredentialResponse) => {
    if (!response.credential) {
      setError(lt('Không nhận được token Google hợp lệ.', 'Google credential was not returned.'));
      return;
    }

    setGoogleLoading(true);
    setError('');
    try {
      await loginWithGoogle({ id_token: response.credential });
      await refreshUser();
      navigate('/app/meetings', { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, lt('Đăng nhập Google thất bại.', 'Google sign-in failed.')));
    } finally {
      setGoogleLoading(false);
    }
  }, [lt, navigate, refreshUser]);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    if (window.google?.accounts?.id) {
      setGoogleScriptLoaded(true);
      return;
    }

    const existingScript = document.getElementById('google-identity-script') as HTMLScriptElement | null;
    if (existingScript) {
      const onLoad = () => setGoogleScriptLoaded(true);
      existingScript.addEventListener('load', onLoad);
      return () => existingScript.removeEventListener('load', onLoad);
    }

    const script = document.createElement('script');
    script.id = 'google-identity-script';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setGoogleScriptLoaded(true);
    script.onerror = () =>
      setError(lt('Không thể tải Google Sign-In.', 'Could not load Google Sign-In script.'));
    document.head.appendChild(script);
  }, [lt]);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !googleScriptLoaded) return;
    if (!googleButtonRef.current || !window.google?.accounts?.id) return;

    const container = googleButtonRef.current;
    container.innerHTML = '';
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleCredential,
      cancel_on_tap_outside: true,
    });
    window.google.accounts.id.renderButton(container, {
      theme: 'outline',
      size: 'large',
      shape: 'pill',
      text: 'continue_with',
      width: 320,
      locale: language === 'vi' ? 'vi' : 'en',
    });
  }, [googleScriptLoaded, handleGoogleCredential, language]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      navigate('/app/meetings', { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, lt('Đăng nhập thất bại.', 'Login failed.')));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <img src="/minute_icon.svg" alt="Minute" className="auth-brand__logo" />
          <div>
            <h1>{lt('Đăng nhập', 'Login')}</h1>
            <p>{lt('Truy cập workspace cuộc họp của bạn', 'Access your meeting workspace')}</p>
          </div>
        </div>

        {error && <div className="form-error">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">{lt('Email', 'Email')}</label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@company.com"
              autoComplete="email"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">{lt('Mật khẩu', 'Password')}</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </div>
          <button className="btn btn--primary auth-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? lt('Đang đăng nhập...', 'Signing in...') : lt('Đăng nhập', 'Login')}
          </button>
        </form>

        {GOOGLE_CLIENT_ID && (
          <>
            <div className="auth-divider">
              <span>{lt('hoặc', 'or')}</span>
            </div>
            <div className="auth-google-wrap">
              <div ref={googleButtonRef} />
              <button
                type="button"
                className="btn btn--secondary auth-google-fallback"
                disabled={!googleScriptLoaded || googleLoading}
                onClick={() => window.google?.accounts?.id?.prompt()}
              >
                {googleLoading
                  ? lt('Đang xác thực Google...', 'Authenticating with Google...')
                  : lt('Tiếp tục với Google', 'Continue with Google')}
              </button>
            </div>
          </>
        )}

        <p className="auth-footer">
          {lt('Chưa có tài khoản?', 'No account yet?')}{' '}
          <Link to="/register">{lt('Đăng ký', 'Register')}</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
