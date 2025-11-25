import React from 'react';

export const Button = ({ 
  children, 
  onClick, 
  type = 'primary', 
  fullWidth = false,
  disabled = false
}) => {
  const types = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
    success: 'bg-green-600 hover:bg-green-700 text-white',
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        sharp-button ${types[type]}
        ${fullWidth ? 'w-full' : ''}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        px-4 py-2 border-0 transition-colors duration-200
      `}
    >
      {children}
    </button>
  );
};

export default Button;