import React from 'react';

function ActionCard({ action, onClick }) {
  return (
    <div className="action-card" onClick={() => onClick && onClick(action)}>
      <span className="action-name">{action.name}</span>
    </div>
  );
}

export default ActionCard;