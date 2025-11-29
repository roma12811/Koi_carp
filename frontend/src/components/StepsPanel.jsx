import React, { useState } from 'react';
import '../styles/StepsPanel.css';

function StepsPanel({ actionName, steps, onBack, onStepHover }) {
  const [activeStep, setActiveStep] = useState(null);

  const handleStepClick = (step, index) => {
    setActiveStep(index);
    // Вызвать подсветку области
    // if (onStepHover) {
      // onStepHover(step.grid_position);
    // }
  };

  return (
    <div className="steps-panel">
      {/* Кнопка назад */}
      <button className="back-button" onClick={onBack}>
        ← Назад
      </button>

      {/* Название действия */}
      <h3 className="steps-title">{actionName}</h3>

      {/* Список шагов */}
      <div className="steps-list">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`step-item ${activeStep === index ? 'active' : ''}`}
            onClick={() => handleStepClick(step, index)}
          >
            <div className="step-number">{index + 1}</div>
            <div className="step-text">{step.instruction}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default StepsPanel;