import './AuthOverlay.css';

/**
 * Full-screen overlay for the Google sign-in flow. Renders the spinner while
 * a sign-in is in flight, or an explanation when it fails — including when the
 * failure is ours (backend unreachable) rather than the user's.
 */
export default function AuthOverlay({ authLoading, slowTip, authError, onRetry, retryButton, onDismiss }) {
  if (authError) {
    return (
      <div className="auth-overlay" role="alert">
        <div className="auth-overlay-icon">{authError.icon}</div>
        <p className="auth-overlay-title">{authError.title}</p>
        <p className="auth-overlay-detail">{authError.detail}</p>
        <div className="auth-overlay-actions">
          {/* Retrying now means re-rendering Google's own button, since the
              ID-token flow has no imperative trigger. */}
          {retryButton ?? (
            <button className="auth-overlay-btn auth-overlay-btn--primary" onClick={onRetry}>
              Try again
            </button>
          )}
          <button className="auth-overlay-btn auth-overlay-btn--ghost" onClick={onDismiss}>
            Go back
          </button>
        </div>
        {authError.status && (
          <p className="auth-overlay-status">Error {authError.status}</p>
        )}
      </div>
    );
  }

  if (!authLoading) return null;

  return (
    <div className="auth-overlay">
      <div className="auth-overlay-spinner" />
      <p className="auth-overlay-text">Signing you in…</p>
      {slowTip && (
        <p className="auth-overlay-tip">
          This is taking a bit longer than expected — our server may be waking up.
        </p>
      )}
    </div>
  );
}
