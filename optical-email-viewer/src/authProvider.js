import { MsalAuthProvider, LoginType } from 'react-aad-msal';
import { PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';

// Msal msalConfigurations
export const msalConfig = {
  auth: {
    authority: 'https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47',
    clientId: '4260538b-cfc5-401e-acc4-be3d829e5440',
    redirectUri: process.env.REACT_APP_REDIRECT_URL
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: true
  }
};

// Authentication Parameters
export const authenticationParameters = {
  scopes: [
    'https://graph.microsoft.com/.default'
  ], 
}

// Options
const options = {
  loginType: LoginType.Redirect,
  tokenRefreshUri: window.location.origin + "/auth.html"
}

// export const authProvider = new MsalAuthProvider(msalConfig, authenticationParameters, options);

export const msalInstance = await PublicClientApplication.createPublicClientApplication(msalConfig)