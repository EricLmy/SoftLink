import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom'; // Import Router
import './index.css'; // Basic styling, can be expanded
import App from './App';
import reportWebVitals from './reportWebVitals';

// If using Redux, setup antd Provider etc.
// import { Provider } from 'react-redux';
// import store from './store'; // Assuming you have a store.js for Redux

// Ant Design global configuration (e.g., localization)
// import { ConfigProvider } from 'antd';
// import zhCN from 'antd/locale/zh_CN';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Router> { /* Wrap App with Router */ }
      {/* <Provider store={store}> */}
      {/* <ConfigProvider locale={zhCN}> */}
      <App />
      {/* </ConfigProvider> */}
      {/* </Provider> */}
    </Router>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals(); 