import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { api } from '../api';

export function useAuthTrigger() {
  const navigate = useNavigate();
  const [authLoading, setAuthLoading] = useState(false);

  const handleSuccess = async (credentialResponse) => {
    setAuthLoading(true);
    try {
      const res = await fetch(api('/api/auth/google'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ token: credentialResponse.access_token }),
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('pc_uid', data.uid);
        navigate(data.onboarded ? '/dashboard' : '/onboarding');
      }
    } finally {
      setAuthLoading(false);
    }
  };

  const trigger = useGoogleLogin({
    onSuccess: handleSuccess,
    onError: () => { setAuthLoading(false); console.error('Google login failed'); },
    flow: 'implicit',
  });

  return { trigger, authLoading };
}
