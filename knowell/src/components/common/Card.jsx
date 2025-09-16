import React from 'react';

const Card = ({ 
  children, 
  title = null, 
  footer = null,
  padding = true,
  className = '' 
}) => {
  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-100 ${
        padding ? 'p-6' : ''
      } ${className}`}
    >
      {title && (
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>
      )}

      {children}

      {footer && (
        <div className="border-t border-gray-300 p-3">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;
