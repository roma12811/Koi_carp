import React from 'react';
import '../styles/GridOverlay.css';

function GridOverlay({ highlightedCell, isVisible }) {
  if (!isVisible) return null;

  // Создаём массив из 9 ячеек (3x3)
  const cells = Array.from({ length: 9 }, (_, i) => i + 1);

  return (
    <div className="grid-overlay">
      {cells.map((cell) => (
        <div
          key={cell}
          className={`grid-cell ${highlightedCell === cell ? 'highlighted' : ''}`}
        >
          {highlightedCell === cell && (
            <div className="grid-label">Ищи здесь 👆</div>
          )}
        </div>
      ))}
    </div>
  );
}

export default GridOverlay;