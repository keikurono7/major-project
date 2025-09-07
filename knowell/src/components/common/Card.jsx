import React from 'react';

const Card = ({ 
  children, 
  title = null, 
  footer = null,
  padding = true,
  className = '' 
}) => {
  return (
    <div className={`sharp-card bg-white border border-gray-300 ${className}`}>
      {title && (
        <div className="border-b border-gray-300 p-3">
          <h3 className="font-medium text-lg">{title}</h3>
        </div>
      )}
      
      <div className={padding ? 'p-4' : ''}>
        {children}
      </div>
      
      {footer && (
        <div className="border-t border-gray-300 p-3">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;