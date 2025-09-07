// src/components/common/ParallaxSection.jsx
import React, { useRef, useEffect } from 'react';

const ParallaxSection = ({ children, speed = 0.5, className = '' }) => {
  const sectionRef = useRef(null);

  useEffect(() => {
    const section = sectionRef.current;
    let offset = 0;
    
    const handleScroll = () => {
      if (!section) return;
      
      const rect = section.getBoundingClientRect();
      const scrollTop = window.scrollY;
      
      // Only apply parallax effect when section is visible
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        offset = (scrollTop - rect.top) * speed;
        section.style.transform = `translateY(${offset}px)`;
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [speed]);

  return (
    <div ref={sectionRef} className={`parallax-section ${className}`}>
      {children}
    </div>
  );
};

export default ParallaxSection;