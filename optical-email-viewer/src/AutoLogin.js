// AutoLogin.js
import React, { useEffect } from "react";
import { useMsal } from "@azure/msal-react";

const AutoLogin = () => {
  const { instance } = useMsal();

  useEffect(() => {
    const login = async () => {
      try {
        await instance.loginRedirect({
          scopes: ["openid", "profile", "User.Read"] // Adjust scopes as needed
        });
      } catch (err) {
        console.error(err);
      }
    };

    if (!instance.getActiveAccount()) {
      login();
    }
  }, [instance]);

  return null; // This component does not render anything
};

export default AutoLogin;
