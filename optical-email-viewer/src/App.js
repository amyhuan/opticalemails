import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'
import Main from './pages/Main';
import './App.css'
import { AuthenticatedTemplate, UnauthenticatedTemplate, useMsal, useMsalAuthentication } from "@azure/msal-react";
import { InteractionType, InteractionRequiredAuthError } from '@azure/msal-browser';
import { useEffect, useState } from 'react';
import { msalConfig } from './authProvider';
import { InteractionStatus } from "@azure/msal-browser";


function App() {

  return (
      <Router>
        <Routes>
          <Route path="/" element={<Main />} />
        </Routes>
      </Router>
  )
}

export default App;
