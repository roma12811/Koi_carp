const { app, BrowserWindow } = require('electron');
const path = require('path');
// const isDev = require('electron-is-dev');

const isDev = !app.isPackaged;

let mainWindow;

function createWindow() {
  // Создать окно приложения
  mainWindow = new BrowserWindow({
    width: 400,
    height: 150,
    x: undefined,  // Позиция X (можешь изменить)
    y: undefined,  // Позиция Y
    frame: false,  // Без рамки Windows
    transparent: false,
    alwaysOnTop: true,  // Поверх всех окон
    resizable: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // Загрузить React приложение
  const startUrl = isDev
    ? 'http://localhost:3000'  // В режиме разработки
    : `file://${path.join(__dirname, './index.html')}`; // В продакшене

  mainWindow.loadURL(startUrl);

  // Открыть DevTools (для отладки)
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Когда Electron готов
app.whenReady().then(createWindow);

// Выход при закрытии всех окон (кроме macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});