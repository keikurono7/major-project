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
            <span className="item-icon">{item.icon}</span>
            <span>{item.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;