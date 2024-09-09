import React from 'react';

export const Alert = ({ children }) => (
  <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4" role="alert">
    {children}
  </div>
);

export const AlertTitle = ({ children }) => (
  <p className="font-bold">{children}</p>
);

export const AlertDescription = ({ children }) => (
  <p>{children}</p>
);