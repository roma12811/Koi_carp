import React, { useState } from 'react';
import '../styles/Dashboard.css';
import ActionCard from './ActionCard';
import StepsPanel from './StepsPanel';
// import GridOverlay from './GridOverlay';

function Dashboard() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [actions, setActions] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSteps, setShowSteps] = useState(false);
  const [currentAction, setCurrentAction] = useState(null);
  const [steps, setSteps] = useState([]);
  // const [highlightedCell, setHighlightedCell] = useState(null);
  // const [showGrid, setShowGrid] = useState(false);

  const loadActions = async () => {
    try {
      setIsLoading(true);

      const response = await fetch("http://localhost:8000/actions");
      if (!response.ok) throw new Error("Ошибка загрузки действий");

      const data = await response.json();
      setActions(data.actions);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };


  const loadSteps = async (action) => {
    try {
      setIsLoading(true);
      setCurrentAction(action);

      const response = await fetch("http://localhost:8000/get-steps", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: action.id })
      });

      if (!response.ok) throw new Error("Ошибка загрузки шагов");

      const data = await response.json();
      setSteps(data.steps);
      setShowSteps(true);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };


  const handleExpand = () => {
    setIsExpanded(true);
    loadActions();
  };

  const handleCollapse = () => {
    setIsExpanded(false);
    setShowSteps(false);
    // setShowGrid(false);
    setActions([]);
    setSteps([]);
    setSearchQuery('');
    // setHighlightedCell(null);
  };

  const handleBackToActions = () => {
    setShowSteps(false);
    // setShowGrid(false);
    // setHighlightedCell(null);
  };

  const handleActionClick = (action) => {
    loadSteps(action);
  };

  // const handleStepHover = (gridPosition) => {
  //   setHighlightedCell(gridPosition);
  //   setShowGrid(true);
  // };

  // Закрыть приложение
  const handleClose = () => {
    if (window.require) {
      const { remote } = window.require('electron');
      remote.getCurrentWindow().close();
    }
  };

  return (
    <>
      {/* <GridOverlay 
        highlightedCell={highlightedCell}
        isVisible={showGrid}
      /> */}

      <div className="dashboard-container">
        {/* Кнопка AI Helper (можно перетаскивать) */}
        <div className="ai-button draggable" onClick={handleExpand}>
          <img 
            src={`${process.env.PUBLIC_URL}/koi-icon.png`} 
            alt="Koi" 
            className="ai-icon-img"
            onError={(e) => {
              console.error('Image not found');
              e.target.style.display = 'none';
            }}
          />
          <span className="ai-text">AI helper</span>
          
          {/* Кнопка закрытия приложения */}
          <button 
            className="close-app-btn" 
            onClick={(e) => {
              e.stopPropagation();
              handleClose();
            }}
          >
            ✕
          </button>
        </div>

        {/* Поле поиска */}
        {isExpanded && !showSteps && (
          <div className="search-box">
            <input 
              type="text" 
              placeholder="Search actions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <span className="search-icon">🔍</span>
          </div>
        )}

        {/* Панель с действиями или шагами */}
        {isExpanded && (
          <div className="actions-panel">
            {/* Кнопка сворачивания панели */}
            <button className="collapse-btn" onClick={handleCollapse}>
              ✕
            </button>

            {showSteps ? (
              <StepsPanel 
                actionName={currentAction?.name}
                steps={steps}
                onBack={handleBackToActions}
                // onStepHover={handleStepHover}
              />
            ) : (
              <>
                {isLoading && (
                  <div className="loading">
                    <div className="spinner"></div>
                    <p>Загрузка действий...</p>
                  </div>
                )}

                {!isLoading && actions.length > 0 && (
                  <div className="actions-list">
                    <h3 className="panel-title">Популярные действия</h3>
                    {actions
                      .filter(action => 
                        action.name.toLowerCase().includes(searchQuery.toLowerCase())
                      )
                      .map(action => (
                        <ActionCard 
                          key={action.id} 
                          action={action}
                          onClick={handleActionClick}
                        />
                      ))
                    }
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default Dashboard;