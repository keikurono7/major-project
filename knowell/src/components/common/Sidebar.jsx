import React from 'react';

const Sidebar = ({ items, activeItem, onItemClick }) => {
  return (
    <div className="sidebar">
      <ul className="sidebar-menu">
        {items.map((item) => (
          <li 
            key={item.id}
            className={`sidebar-item ${activeItem === item.id ? 'active' : ''}`}
            onClick={() => onItemClick(item.id)}
          >
            <span className="item-icon">
              {typeof item.icon === 'string'
                ? item.icon
                : item.icon && <item.icon className="w-5 h-5" />}
            </span>
            <span>{item.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;