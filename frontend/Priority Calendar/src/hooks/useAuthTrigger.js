import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { api } from '../api';

/*
 * The API is proxied through to a Render instance that can be hibernating,
 * mid-deploy, or down in a platform incident. All three surface as a 5xx or a
 * rejected fetch rather than anything the backend itself returns, so they need
 * to read differently to the user than a genuine sign-in rejection.
 */
const SERVICE_DOWN = {
  icon: '🛠️',
  title: 'Priority Calendar is temporarily unavailable',
  detail:
    "Our servers aren't responding right now. This is on our end, not yours — " +
    'please try again in a few minutes.',
};

const OFFLINE = {
  icon: '📡',
  title: "You're offline",
  detail: 'Check your internet connection and try again.',
};

/*
 * The backend decides which calendar day a user is on — when their task
 * percentages re-split, chiefly — so it needs the zone the browser is in
 * rather than the one the server happens to run in. Resolving it per sign-in
 * keeps it current if they move.
 */
const browserTimezone = () => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null;
  } catch {
    return null;
  }
};

const SIGN_IN_FAILED = {
  icon: '🔒',
  title: "We couldn't sign you in",
  detail: 'Google sign-in didn\'t complete. Please try again.',
};

export function useAuthTrigger() {
  const navigate = useNavigate();
  const [authLoading, setAuthLoading] = useState(false);
  const [slowTip, setSlowTip] = useState(false);
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
    if (!authLoading) { setSlowTip(false); return; }
    const t = setTimeout(() => setSlowTip(true), 20000);
    return () => clearTimeout(t);
  }, [authLoading]);

  const handleSuccess = async (credentialResponse) => {
    setAuthLoading(true);
    setAuthError(null);
    try {
      const res = await fetch(api('/api/auth/google'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          token: credentialResponse.access_token,
          timezone: browserTimezone(),
        }),
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('pc_uid', data.uid);
        navigate(data.onboarded ? '/dashboard' : '/onboarding');
        return;
      }

      // 5xx means the request never reached our code — the platform answered
      // for us. 4xx means the backend did handle it and turned us away.
      console.error(`Sign-in failed: HTTP ${res.status} from /api/auth/google`);
      setAuthError(
        res.status >= 500
          ? { ...SERVICE_DOWN, status: res.status }
          : { ...SIGN_IN_FAILED, status: res.status }
      );
    } catch (err) {
      // fetch only rejects on network-level failure: offline, DNS, CORS,
      // connection refused. The backend is unreachable either way.
      console.error('Sign-in request never reached the server:', err);
      setAuthError(navigator.onLine === false ? OFFLINE : SERVICE_DOWN);
    } finally {
      setAuthLoading(false);
    }
  };

  const googleLogin = useGoogleLogin({
    onSuccess: handleSuccess,
    onError: (err) => {
      console.error('Google login failed', err);
      setAuthLoading(false);
      setAuthError(SIGN_IN_FAILED);
    },
    flow: 'implicit',
  });

  const trigger = () => {
    setAuthError(null);
    setAuthLoading(true);
    googleLogin();
  };

  const dismissError = () => setAuthError(null);

  return { trigger, authLoading, slowTip, authError, dismissError };
}
