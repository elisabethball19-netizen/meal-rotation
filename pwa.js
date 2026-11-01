/* Installation and offline support; recipe data stays in the app's existing storage. */
(() => {
  if (!('serviceWorker' in navigator) || !window.isSecureContext) return;
  if (!['http:', 'https:'].includes(location.protocol)) return;

  const register = () => {
    navigator.serviceWorker.register('./service-worker.js', { updateViaCache: 'none' })
      .catch(error => console.warn('Meal Rotation offline setup could not finish:', error));
  };
  if (document.readyState === 'complete') register();
  else window.addEventListener('load', register, { once: true });
})();
