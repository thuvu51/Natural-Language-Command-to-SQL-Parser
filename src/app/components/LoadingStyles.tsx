export const LoadingStyles = () => (
  <style>{`
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    .loading-spin {
      animation: spin 1s linear infinite;
    }
  `}</style>
);
